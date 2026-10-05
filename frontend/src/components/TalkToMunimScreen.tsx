import React, { useState, useEffect, useRef } from "react";
import { Mic, MicOff, Send, Sparkles, Check, X, ShieldAlert, Volume2 } from "lucide-react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  actionCard?: any;
}

interface TalkToMunimScreenProps {
  merchantId: string;
  onSendActionApproval: (approvalId: number, decision: string) => void;
  onPlaySpeech: (text: string) => void;
}

export const TalkToMunimScreen: React.FC<TalkToMunimScreenProps> = ({
  merchantId,
  onSendActionApproval,
  onPlaySpeech
}) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "assistant",
      content: "Namaste Sharma ji! Main aapka digital Munim hu. Aaj dhandha kaisa raha, ya koi offer chalu karna hai?"
    }
  ]);
  const [inputText, setInputText] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [resolvedActions, setResolvedActions] = useState<Record<string, string>>({});

  const handleActionClick = (cardKey: string, approvalId: number, decision: "APPROVED" | "REJECTED") => {
    setResolvedActions(prev => ({ ...prev, [cardKey]: decision }));
    onSendActionApproval(approvalId, decision);
  };

  const samplePrompts = [
    "Aaj kitni bikri hui?",
    "Sales kyu kam thi pichle hafte?",
    "Udhaar kiska baki hai?",
    "Tuesday dead slot offer chalao",
    "Mera Munim Score kya hai?"
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text
    };
    setMessages(prev => [...prev, userMsg]);
    setInputText("");
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ merchant_id: merchantId, message: text })
      });
      const data = await res.json();

      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.spoken_reply,
        actionCard: data.action_card
      };
      setMessages(prev => [...prev, assistantMsg]);
      onPlaySpeech(data.spoken_reply);
    } catch (err) {
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content: "Maaf kijiye, server se connect nahi ho paya. Dobara koshish karein."
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const startVoiceInput = () => {
    // Check if browser SpeechRecognition is available
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.lang = "hi-IN";
      recognition.continuous = false;
      recognition.interimResults = false;

      recognition.onstart = () => setIsListening(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setIsListening(false);
        handleSendMessage(transcript);
      };
      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);
      recognition.start();
    } else {
      // Fallback: cycle through typical voice prompts
      const randomPrompt = samplePrompts[Math.floor(Math.random() * samplePrompts.length)];
      handleSendMessage(randomPrompt);
    }
  };

  return (
    <div className="flex flex-col h-[560px] pb-16">
      {/* Header Info */}
      <div className="p-3 bg-cyan-50 border-b border-cyan-100 rounded-t-2xl flex items-center justify-between text-xs text-paytm-blue font-bold">
        <div className="flex items-center gap-1.5">
          <Sparkles className="w-4 h-4" />
          <span>TALK TO MUNIM (Voice & Action Cards)</span>
        </div>
        <span className="text-[10px] text-slate-500 font-normal">Hinglish • Spoken Mode</span>
      </div>

      {/* Messages Stream */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-xs leading-relaxed ${
                msg.role === "user"
                  ? "bg-paytm-blue text-white rounded-br-none shadow-sm"
                  : "bg-white text-slate-800 border border-slate-200 rounded-bl-none shadow-sm"
              }`}
            >
              {msg.content}
            </div>

            {/* Inline Action Card (Tier 2 Guardrail Approval) */}
            {msg.actionCard && (
              <div className="mt-2 w-[85%] bg-amber-50 border border-amber-200 rounded-2xl p-3 shadow-sm text-xs">
                <div className="flex items-center gap-1.5 text-amber-900 font-bold mb-1">
                  <ShieldAlert className="w-4 h-4 text-amber-600" />
                  <span>ACTION APPROVAL REQUIRED (Phone View)</span>
                </div>

                {msg.actionCard.type === "campaign_proposal" && (
                  <div>
                    <p className="text-slate-700 font-medium mb-2">{msg.actionCard.offer_text}</p>
                    {resolvedActions[msg.id] ? (
                      <div className="flex items-center gap-1.5 py-1.5 px-3 bg-emerald-50 text-emerald-700 font-semibold rounded-lg border border-emerald-200">
                        <Check className="w-3.5 h-3.5" />
                        <span>Campaign {resolvedActions[msg.id] === "APPROVED" ? "Approved & Launched ✓" : "Rejected"}</span>
                      </div>
                    ) : (
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleActionClick(msg.id, msg.actionCard?.opportunity_id || 1, "APPROVED")}
                          className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg flex items-center justify-center gap-1"
                        >
                          <Check className="w-3.5 h-3.5" /> Haan, Chalu Karo
                        </button>
                        <button
                          onClick={() => handleActionClick(msg.id, msg.actionCard?.opportunity_id || 1, "REJECTED")}
                          className="py-1.5 px-3 bg-slate-200 hover:bg-slate-300 text-slate-700 font-semibold rounded-lg"
                        >
                          Nahi
                        </button>
                      </div>
                    )}
                  </div>
                )}

                {msg.actionCard.type === "udhaar_reminder_card" && (
                  <div>
                    <p className="text-slate-700 font-medium mb-2">
                      {msg.actionCard.target_customer} ko ₹{msg.actionCard.amount} ka UPI payment reminder bhejein?
                    </p>
                    {resolvedActions[msg.id] ? (
                      <div className="flex items-center gap-1.5 py-1.5 px-3 bg-emerald-50 text-emerald-700 font-semibold rounded-lg border border-emerald-200">
                        <Check className="w-3.5 h-3.5" />
                        <span>Collect Request Sent to {msg.actionCard.target_customer} ✓</span>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleActionClick(msg.id, msg.actionCard?.approval_id || 4, "APPROVED")}
                        className="w-full py-1.5 bg-paytm-blue hover:bg-cyan-600 text-white font-bold rounded-lg flex items-center justify-center gap-1"
                      >
                        <Check className="w-3.5 h-3.5" /> Bhejo (Send Collect Link)
                      </button>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="px-3 py-1.5 flex gap-1.5 overflow-x-auto text-[11px]">
        {samplePrompts.slice(0, 3).map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(prompt)}
            className="flex-shrink-0 px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-full border border-slate-200 transition-colors"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Voice Waveform Indicator */}
      {isListening && (
        <div className="p-2 bg-rose-50 border border-rose-200 text-center text-xs text-rose-600 font-bold flex items-center justify-center gap-2 animate-pulse">
          <Mic className="w-4 h-4" />
          <span>Aapki awaz sun rahe hain... Boliye!</span>
        </div>
      )}

      {/* Input Form with Mic Button */}
      <div className="p-3 bg-white border-t border-slate-200 flex items-center gap-2">
        <button
          onClick={startVoiceInput}
          className={`p-2.5 rounded-full text-white shadow-md transition-all ${
            isListening ? "bg-rose-500 animate-bounce" : "bg-paytm-blue hover:bg-cyan-600"
          }`}
          title="Phone Voice Input (Hold or Tap to speak)"
        >
          {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
        </button>

        <input
          type="text"
          value={inputText}
          onChange={e => setInputText(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleSendMessage()}
          placeholder="Munim se kuch bhi poochiye (Hinglish)..."
          className="flex-1 py-2 px-3 bg-slate-100 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-paytm-blue border border-slate-200"
        />

        <button
          onClick={() => handleSendMessage()}
          disabled={isLoading || !inputText.trim()}
          className="p-2.5 bg-slate-900 text-white rounded-xl hover:bg-slate-800 disabled:opacity-40 transition-colors"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};
