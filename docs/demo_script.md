# Munim — 3-Minute Hackathon Demo Script

**Theme**: "Build the AI business partner for every Paytm merchant."  
**Persona**: Sharma Ji, Owner of "Sharma Chai & Snacks" (Jaipur, Rajasthan).  
**Hardware & Interface**: Split Layout — Simulated Physical Paytm Soundbox (Left) + Phone App View (Right).

---

## ⏱️ Act 1: The Problem & The Voice Morning Brief (0:00 – 0:40)

> **Speaker**:  
> *"Over 30 million small Indian merchants have a Paytm Soundbox on their counter. Today, that Soundbox does one thing: it announces payments after money comes in. But it doesn't help the merchant make more money.*  
> *Meet **Munim**: a voice-first AI business partner that transforms raw UPI transaction streams into growth, soundbox announcements, and financial intelligence."*

### Screen Action:
1. Point to the **Split Screen**: On the left is the **Paytm Soundbox 5G Simulator** (Output-only, with pulsing speaker animation and prominent `Simulated` badge). On the right is the **Phone App View**.
2. On the Phone Home Screen, point out **Today's True Daily Profit**:
   - `UPI Sales (₹4,280) + Cash Mila (₹2,400) - Kharcha (₹740) = Net Profit (₹5,940)`.
   - Highlight: *"Zero arithmetic in the LLM. All numbers come strictly from deterministic Python calculations."*
3. Tap the **"Suno"** button on the Morning Brief card:
   - The Soundbox speaker pulses with cyan audio rings and speaks in warm natural Hinglish:  
     *"Suprabhat Sharma ji! Kal dukaan par ₹6,680 ka dhandha hua. Aaj Tuesday dopahar ka sannata dur karne ke liye offer chalayein. Phone pe brief dekhein."*

---

## ⏱️ Act 2: Headline Feature — Item Inference from Payment Amounts (0:40 – 1:15)

> **Speaker**:  
> *"Small merchants don't have barcode scanners or POS billing machines. They only have a UPI QR code. So how can an AI know what they actually sell?*  
> *Munim's **Item Inference Engine** uses frequency clustering and constrained subset decomposition. It realizes that ₹10 is a Chai, ₹20 is a Samosa, and ₹30 is a Chai + Samosa combo!"*

### Screen Action:
1. Tap the **"Menu"** tab on the phone app view.
2. Show the **Top Price Points Volume Chart**:
   - Point out ₹10 (Masala Chai), ₹20 (Samosa), ₹40 (Kulhad Chai).
3. Scroll to the **Bayesian Confirmation Chips**:
   - Show the chip: `₹20 = Samosa (88% Confidence)`.
   - Tap **"Sahi Hai (Haan)"**:
   - The chip instantly turns green: `Confirmed (Prior 1.0)`.
   - The Soundbox announces: *"Prior updated: ₹20 confirmed as Samosa."*
   - Highlight: *"Inference code is strictly blind to ground truth in `ground_truth.db`. Confirmations update Bayesian priors in real time!"*

---

## ⏱️ Act 3: Footfall Sensor & Live Payment Burst (1:15 – 1:55)

> **Speaker**:  
> *"Now let's see Munim's live Footfall Sensor. By computing payment frequency against historical hour-of-week baselines, Munim detects rushes and lulls in real time."*

### Screen Action:
1. Open the **"Demo Controls"** modal in the top bar.
2. Tap **"⚡ Inject 16 Payments Now (Trigger Rush)"**:
3. Instantly, the Footfall Sensor computes $Z\text{-score} > 2.0$:
   - The Soundbox speaker rings pulse rapidly!
   - Soundbox announces:  
     *"Dhyan dein: Rush aa raha hai! Doodh aur snacks ka stock check kar lo."*
4. Highlight:
   - *"The Soundbox is strictly output-only. Notice there is no microphone or buttons on the device. All approvals happen on the phone!"*

---

## ⏱️ Act 4: Dead-Slot Opportunity, Tier 2 Guardrails & Uplift vs Holdout (1:55 – 2:30)

> **Speaker**:  
> *"What happens during a lull? Our synthetic data generator planted a real merchant pain point: Tuesdays between 2 PM and 5 PM, footfall crashes by 85%."*

### Screen Action:
1. Switch to **"Offers (Campaigns)"** tab.
2. Show the **Tier 2 Approvals Queue**:
   - `START_CAMPAIGN: Tuesday Special 20% Off Chai + Samosa Combo (2 PM - 5 PM)`.
   - Highlight: *"Tier 0 read and Tier 1 drafts are auto-allowed. But Tier 2 actions that spend money or message customers REQUIRE explicit merchant approval on the phone. Direct adapter calls are blocked by a private runtime token."*
3. Tap **"Haan, Approve Karein"**:
   - The action executes through the mock messaging adapter and writes to the **Immutable Audit Log**.
4. Tap **"Measure Uplift vs Holdout"**:
   - The counterfactual simulation runs with an 80/20 customer split.
   - The chart renders:
     - **Uplift vs Holdout: +21.4%** [Simulated Badge].
     - Treatment Conversion: 28.5% vs Holdout Baseline: 7.1%.
     - Incremental Revenue: +₹1,840.

---

## ⏱️ Act 5: Bahi-Khata, Udhaar Aging & Munim Score (2:30 – 3:00)

> **Speaker**:  
> *"Finally, Munim handles the daily financial rituals that micro-merchants dread."*

### Screen Action:
1. Switch to **"Bahi-Khata"** tab:
   - Show the Udhaar ledger with 8 borrowers. Point out the 2 critical overdue debtors (15+ days late).
   - Select Ramesh Kumar (₹650) $\to$ choose **"Funny"** tone:  
     *"Arrey Ramesh bhai! Chai ki dosti barkarar rahe, bas ₹650 ka hisab clear kar do toh mazaa aa jaye! 😊"*
   - Tap **"Bhejo"** to send simulated Paytm UPI Collect request.
2. Switch to **"Score"** tab:
   - Display the **Munim Score: 78/100**.
   - Show the 5 factors: Consistency (21/25), Growth (15/20), Repeat Rate (16/20), Udhaar Recovery (13/20), Cash Discipline (13/15).
   - Show the unlocked Indicative Loan Limit Band: **₹65,000 – ₹85,000** [Simulated Badge].
   - Point out the underwriting disclaimer:  
     *"Illustrative signal for Paytm's existing underwriting, not a credit decision."*

> **Closing**:  
> *"Munim transforms the passive Paytm Soundbox into an active, voice-first business partner for India's 30 million merchants. Thank you!"*
