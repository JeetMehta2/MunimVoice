import re
import os
import asyncio
import hashlib
import ssl
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import edge_tts
from app.core.config import settings

# Patch SSL context for edge_tts to prevent Windows certificate verification failures
try:
    import edge_tts.communicate
    _ssl_ctx = ssl.create_default_context()
    _ssl_ctx.check_hostname = False
    _ssl_ctx.verify_mode = ssl.CERT_NONE
    edge_tts.communicate._SSL_CTX = _ssl_ctx
except Exception:
    pass

# Comprehensive Hinglish to Devanagari Hindi phonetic dictionary for authentic Soundbox voice
HINDI_SPEECH_MAP = {
    "paytm": "पेटीएम", "phone": "फ़ोन", "par": "पर", "pe": "पर", "prapt": "प्राप्त",
    "hue": "हुए", "approve": "अप्रूव", "approved": "अप्रूव्ड", "approval": "अप्रूवल",
    "reject": "रद्द", "rejected": "रद्द", "request": "अनुरोध", "kar": "कर", "karein": "करें",
    "kijiye": "कीजिए", "dijiye": "दीजिए", "ho": "हो", "gaya": "गया", "gayi": "गयी",
    "gaye": "गए", "hai": "है", "hain": "हैं", "aaj": "आज", "kal": "कल",
    "suprabhat": "सुप्रभात", "namaste": "नमस्ते", "sharma": "शर्मा", "ji": "जी",
    "dukaan": "दुकान", "kamai": "कमाई", "shuddh": "शुद्ध", "munafa": "मुनाफ़ा",
    "raha": "रहा", "rahi": "रही", "mukhya": "मुख्य", "mauka": "मौका", "pura": "पूरा",
    "hisab": "हिसाब", "dekhein": "देखें", "brief": "ब्रीफ़", "bahi": "बही", "khata": "खाता",
    "logged": "दर्ज हुआ", "record": "दर्ज", "cash": "कैश", "kharch": "खर्च", "kharcha": "खर्चा",
    "doodh": "दूध", "chai": "चाय", "patti": "पत्ती", "cheeni": "चीनी", "sugar": "चीनी",
    "adrak": "अदरक", "masala": "मसाला", "gas": "गैस", "kiraya": "किराया", "samosa": "समोसा",
    "tel": "तेल", "diya": "दिया", "mila": "मिला", "aaya": "आया", "bheja": "भेजा",
    "galla": "गल्ला", "jama": "जमा", "collection": "कलेक्शन", "naya": "नया", "offer": "ऑफ़र",
    "campaign": "ऑफ़र", "chalu": "चालू", "karo": "करो", "kiya": "किया", "udhaar": "उधार",
    "reminder": "रिमाइंडर", "bhejo": "भेजो", "action": "कार्रवाई", "rush": "भीड़",
    "alert": "अलर्ट", "aur": "और", "ka": "का", "ki": "की", "ke": "के", "ko": "को",
    "se": "से", "mein": "में", "me": "में", "rupaye": "रुपये", "rupayee": "रुपये",
    "rupees": "रुपये", "rupee": "रुपया", "rs": "रुपये", "darj": "दर्ज", "sahi": "सही",
    "total": "कुल", "bhi": "भी", "customer": "ग्राहक", "payment": "भुगतान", "batao": "बताओ",
    "kitna": "कितना", "baki": "बाकी", "bache": "बचे", "bacha": "बचा"
}

def clean_text_for_speech(text: str) -> str:
    """
    Cleans and normalizes text for Indian neural TTS pronunciation.
    Translates common Hinglish soundbox phrases to Devanagari so neural Hindi voice
    pronounces words with 100% natural, fluent cadence without spelling out letters.
    """
    # 1. Standardize currency expressions
    cleaned = text.replace("₹", " रुपये ")
    cleaned = re.sub(r'\brs\.?\s*', ' रुपये ', cleaned, flags=re.IGNORECASE)

    # 2. Transliterate known Hinglish words to Devanagari Hindi
    def word_repl(match):
        w = match.group(0).lower()
        return HINDI_SPEECH_MAP.get(w, match.group(0))

    cleaned = re.sub(r'[a-zA-Z]+', word_repl, cleaned)

    # 3. Clean up syntax and ensure amounts read naturally (e.g., '20 रुपये')
    cleaned = re.sub(r'रुपये\s*(\d+)', r'\1 रुपये', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


# Hinglish Hindi/Urdu number word mapping
HINDI_NUMBER_WORDS = {
    "ek": 1, "do": 2, "teen": 3, "chaar": 4, "char": 4, "paanch": 5, "panch": 5,
    "chheh": 6, "che": 6, "saat": 7, "sat": 7, "aath": 8, "ath": 8, "nau": 9, "no": 9,
    "das": 10, "gyarah": 11, "barah": 12, "terah": 13, "chaudah": 14, "pandrah": 15,
    "solah": 16, "satrah": 17, "atharah": 18, "unnis": 19, "bees": 20, "bis": 20,
    "pachees": 25, "pachis": 25, "tees": 30, "tis": 30, "pentees": 35, "chalis": 40,
    "pachas": 50, "saath": 60, "sattar": 70, "assi": 80, "nabbe": 90,
    "sau": 100, "so": 100,
    "hazaar": 1000, "hazar": 1000, "k": 1000,
    "lakh": 100000, "lac": 100000
}

EXPENSE_KEYWORDS = {
    "doodh": "milk", "milk": "milk",
    "chai patti": "tea_leaves", "patti": "tea_leaves", "tea": "tea_leaves",
    "cheeni": "groceries", "sugar": "groceries", "adrak": "groceries", "masala": "groceries",
    "gas": "gas", "cylinder": "gas",
    "kiraya": "rent", "rent": "rent",
    "samosa": "snacks_prep", "maida": "snacks_prep", "tel": "oil", "oil": "oil"
}

class HinglishVoiceParser:
    """
    Parses spoken Hinglish cash and expense phrases into structured numerical values.
    Examples:
      - 'Aaj cash teen hazaar do sau mila' -> 3200
      - 'Doodh ka paanch sau rupaye diya' -> milk: 500
      - 'Cash 2500 aur kharcha 700' -> cash: 2500, expense: 700
    """

    @classmethod
    def parse_number_phrase(cls, text: str) -> Optional[float]:
        """
        Extracts spoken Hindi or numerical digits from string.
        """
        cleaned = text.lower().replace(",", "").replace("₹", "").replace("rs.", "").replace("rs", "").strip()
        
        # 1. Direct digit match e.g. "3200"
        digit_match = re.search(r'\b\d+(\.\d+)?\b', cleaned)
        if digit_match:
            return float(digit_match.group(0))

        # 2. Spoken Hindi number words e.g. "teen hazaar do sau"
        words = re.findall(r'\b[a-z]+\b', cleaned)
        total = 0.0
        current = 0.0

        for w in words:
            if w in HINDI_NUMBER_WORDS:
                val = HINDI_NUMBER_WORDS[w]
                if val in (100, 1000, 100000):
                    if current == 0.0:
                        current = 1.0
                    current *= val
                    total += current
                    current = 0.0
                else:
                    current += val
        total += current
        return total if total > 0 else None

    @classmethod
    def extract_bahi_khata_fields(cls, transcript: str) -> Dict[str, Any]:
        """
        Extracts structured cash_in, expenses list, and creates a confirmation prompt.
        """
        text = transcript.lower()
        cash_in = 0.0
        expenses: List[Dict[str, Any]] = []

        # Split clauses by 'aur', 'and', commas, or periods
        clauses = re.split(r'\baur\b|\band\b|,|\.', text)

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            num = cls.parse_number_phrase(clause)
            if not num:
                continue

            # Check if this clause relates to cash in or expense
            if any(w in clause for w in ["cash", "aaya", "mila", "galla", "jama", "collection"]):
                cash_in = num
            elif any(w in clause for w in ["kharch", "diya", "bheja", "payment", "bill", "chuka"]) or any(k in clause for k in EXPENSE_KEYWORDS):
                # Identify category
                cat = "misc"
                for k, v in EXPENSE_KEYWORDS.items():
                    if k in clause:
                        cat = v
                        break
                expenses.append({
                    "category": cat,
                    "amount": num,
                    "source_text": clause
                })
            else:
                # Default heuristic: if cash_in is 0, first number is usually cash
                if cash_in == 0:
                    cash_in = num
                else:
                    expenses.append({"category": "misc", "amount": num, "source_text": clause})

        total_expense = sum(e["amount"] for e in expenses)
        confirmation_msg = f"Cash ₹{int(cash_in)}, kharcha ₹{int(total_expense)} darj karu, sahi hai?"

        return {
            "transcript": transcript,
            "cash_in": cash_in,
            "expenses": expenses,
            "total_expense": total_expense,
            "confirmation_message": confirmation_msg
        }


class VoiceSynthesizer:
    """
    Edge-TTS voice synthesizer with authentic Indian Hindi / Hinglish neural voice profiles.
    Uses 'hi-IN-SwaraNeural' by default (the authentic Paytm Soundbox female voice)
    with automatic Devanagari normalization for 100% natural, fluent speech.
    """
    VOICE_SOUNDBOX = "hi-IN-SwaraNeural"    # Authentic Paytm Soundbox female voice
    VOICE_MALE = "hi-IN-MadhurNeural"       # Warm Indian Hindi male voice
    VOICE_ENGLISH = "en-IN-PrabhatNeural"   # Indian English voice
    DEFAULT_VOICE = "hi-IN-SwaraNeural"

    @classmethod
    async def synthesize_speech(
        cls, 
        text: str, 
        voice: Optional[str] = None,
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes text into MP3 audio file. Returns local file path and web audio URL.
        """
        selected_voice = voice or cls.DEFAULT_VOICE
        cleaned_text = clean_text_for_speech(text)

        if not cleaned_text:
            return {"file_path": "", "audio_url": "", "cached": False, "error": "Empty text"}

        if output_filename is None:
            text_hash = hashlib.md5(f"{selected_voice}:{cleaned_text}".encode("utf-8")).hexdigest()[:12]
            output_filename = f"tts_{text_hash}.mp3"

        out_path = settings.AUDIO_DIR / output_filename
        audio_url = f"/api/audio/{output_filename}"

        # If already cached and valid, return immediately
        if out_path.exists() and out_path.stat().st_size > 1000:
            return {
                "file_path": str(out_path),
                "audio_url": audio_url,
                "cached": True,
                "text": text,
                "voice": selected_voice
            }

        try:
            communicate = edge_tts.Communicate(cleaned_text, selected_voice)
            await communicate.save(str(out_path))
            return {
                "file_path": str(out_path),
                "audio_url": audio_url,
                "cached": False,
                "text": text,
                "voice": selected_voice
            }
        except Exception as e:
            return {
                "file_path": str(out_path),
                "audio_url": audio_url if (out_path.exists() and out_path.stat().st_size > 0) else "",
                "cached": False,
                "error": str(e)
            }

    @classmethod
    def synthesize_sync(cls, text: str, voice: Optional[str] = None) -> str:
        """Synchronous wrapper returning the audio web URL for soundbox announcements."""
        try:
            res = asyncio.run(cls.synthesize_speech(text, voice))
            return res.get("audio_url", "")
        except Exception:
            return ""

    @classmethod
    def precache_defaults(cls):
        """Pre-generates common default soundbox audio so playback is instantaneous."""
        default_phrase = "Paytm par ₹20 prapt hue."
        try:
            res = asyncio.run(cls.synthesize_speech(default_phrase, cls.DEFAULT_VOICE, output_filename="tts_default_soundbox.mp3"))
            return res.get("audio_url", "")
        except Exception:
            pass

