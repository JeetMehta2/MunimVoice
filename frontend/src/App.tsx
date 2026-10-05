import React, { useState, useEffect, useRef } from "react";
import { 
  Home, MessageSquare, PieChart, BookOpen, Megaphone, 
  Award, Zap, RefreshCw, Volume2, ShieldCheck, ChevronDown 
} from "lucide-react";

import { SoundboxDevice } from "./components/SoundboxDevice";
import { HomeScreen } from "./components/HomeScreen";
import { TalkToMunimScreen } from "./components/TalkToMunimScreen";
import { WhatISellScreen } from "./components/WhatISellScreen";
import { BahiKhataScreen } from "./components/BahiKhataScreen";
import { CampaignsScreen } from "./components/CampaignsScreen";
import { ScoreScreen } from "./components/ScoreScreen";
import { DemoControlPanelModal } from "./components/DemoControlPanelModal";
import { EvalDashboardModal } from "./components/EvalDashboardModal";
import { fetchApi } from "./lib/api";

export default function App() {
  const [currentMerchantId, setCurrentMerchantId] = useState("merchant_sharma_chai");
  const [activeTab, setActiveTab] = useState("home");
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [isEvalModalOpen, setIsEvalModalOpen] = useState(false);

  // Live Soundbox state
  const [lastAnnouncement, setLastAnnouncement] = useState(
    "Paytm par ₹20 prapt hue."
  );
  const [isBroadcasting, setIsBroadcasting] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>("/api/audio/tts_default_soundbox.mp3");
  const audioPlayerRef = useRef<HTMLAudioElement | null>(null);

  // App Data
  const [merchant, setMerchant] = useState<any>(null);
  const [summary, setSummary] = useState<any>(null);
  const [morningBrief, setMorningBrief] = useState<any>(null);
  const [scoreData, setScoreData] = useState<any>(null);
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [productMix, setProductMix] = useState<any[]>([]);
  const [udhaarList, setUdhaarList] = useState<any[]>([]);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [approvals, setApprovals] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [evalResults, setEvalResults] = useState<any>(null);

  // Load merchant data
  const loadData = async (mId: string) => {
    try {
      const [
        merchRes, sumRes, briefRes, scoreRes, oppsRes, 
        mixRes, udhaarRes, campRes, appRes, auditRes, evalRes
      ] = await Promise.all([
        fetchApi<any>(`/merchants/${mId}`),
        fetchApi<any>(`/merchants/${mId}/summary`),
        fetchApi<any>(`/merchants/${mId}/morning-brief`),
        fetchApi<any>(`/merchants/${mId}/score`),
        fetchApi<any>(`/merchants/${mId}/opportunities`),
        fetchApi<any>(`/merchants/${mId}/product-mix`),
        fetchApi<any>(`/merchants/${mId}/udhaar`),
        fetchApi<any>(`/merchants/${mId}/campaigns`),
        fetchApi<any>(`/merchants/${mId}/approvals`),
        fetchApi<any>(`/merchants/${mId}/audit-log`),
        fetchApi<any>(`/eval/results`)
      ]);

      setMerchant(merchRes);
      setSummary(sumRes);
      setMorningBrief(briefRes);
      setScoreData(scoreRes);
      setOpportunities(oppsRes);
      setProductMix(mixRes);
      setUdhaarList(udhaarRes);
      setCampaigns(campRes);
      setApprovals(appRes);
      setAuditLogs(auditRes);
      setEvalResults(evalRes);
    } catch (err) {
      console.error("Data load error:", err);
    }
  };

  useEffect(() => {
    loadData(currentMerchantId);
  }, [currentMerchantId]);

  // WebSocket for Live Soundbox Announcements
  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/live/${currentMerchantId}`);
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "soundbox_announcement" || msg.type === "rush_alert") {
          const annText = msg.data.text || msg.data.message || "";
          triggerSoundbox(annText, msg.data.audio);
        }
      } catch (e) {}
    };
    return () => ws.close();
  }, [currentMerchantId]);

  // Helper to play an MP3 audio URL
  const playAudioUrl = (url: string) => {
    try {
      const fullUrl = url.startsWith("http") ? url : url.startsWith("/") ? url : `/${url}`;
      if (audioPlayerRef.current) {
        audioPlayerRef.current.src = fullUrl;
        audioPlayerRef.current.currentTime = 0;
        audioPlayerRef.current.play().catch((err) => {
          console.warn("Audio element play error:", err);
        });
      } else {
        const sound = new Audio(fullUrl);
        sound.play().catch((err) => {
          console.warn("Direct Audio play error:", err);
        });
      }
    } catch (e) {
      console.error("Audio playback error:", e);
    }
  };

  const triggerSoundbox = async (text: string, audio?: string) => {
    setLastAnnouncement(text);
    setIsBroadcasting(true);

    // If an audio URL is explicitly passed
    if (audio) {
      setAudioUrl(audio);
      playAudioUrl(audio);
      return;
    }

    // Request authentic neural Indian Soundbox TTS from backend
    try {
      const res = await fetchApi<{ audio_url: string }>("/voice/tts", {
        method: "POST",
        body: JSON.stringify({ text })
      });
      if (res && res.audio_url) {
        setAudioUrl(res.audio_url);
        playAudioUrl(res.audio_url);
        return;
      }
    } catch (err) {
      console.warn("TTS API fetch failed:", err);
    }
  };


  const handleResolveApproval = async (approvalId: number, decision: string) => {
    try {
      const res = await fetchApi<any>(
        `/merchants/${currentMerchantId}/approvals/${approvalId}/resolve`,
        {
          method: "POST",
          body: JSON.stringify({ decision })
        }
      );
      // Refresh state
      loadData(currentMerchantId);
      triggerSoundbox(`Action ${decision.toLowerCase()} ho gaya.`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleConfirmItem = async (amount: number, confirmedItem: string) => {
    try {
      await fetchApi(`/merchants/${currentMerchantId}/confirm-item`, {
        method: "POST",
        body: JSON.stringify({ amount, confirmed_item: confirmedItem })
      });
      loadData(currentMerchantId);
      triggerSoundbox(`Prior updated: ₹${amount} confirmed as ${confirmedItem}.`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleInjectBurst = async () => {
    try {
      const res = await fetchApi<any>(`/merchants/${currentMerchantId}/inject-burst`, {
        method: "POST",
        body: JSON.stringify({ count: 16, amount: 20.0 })
      });
      loadData(currentMerchantId);
      if (res.analysis?.announcement) {
        triggerSoundbox(res.analysis.announcement);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleRunUpliftSimulation = async (campaignId: number) => {
    try {
      await fetchApi<any>(`/campaigns/${campaignId}/simulate-uplift`, {
        method: "POST"
      });
      loadData(currentMerchantId);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSendReminder = async (udhaarId: number, tone: string) => {
    try {
      await fetchApi<any>(`/merchants/${currentMerchantId}/udhaar/${udhaarId}/remind`, {
        method: "POST",
        body: JSON.stringify({ tone })
      });
      loadData(currentMerchantId);
      triggerSoundbox("Udhaar reminder ka approval request phone par bhej diya gaya hai.");
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddUdhaar = async (name: string, amount: number) => {
    try {
      await fetchApi<any>(`/merchants/${currentMerchantId}/udhaar`, {
        method: "POST",
        body: JSON.stringify({ customer_name: name, amount, due_days: 7 })
      });
      loadData(currentMerchantId);
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogCashExpense = async (data: any) => {
    try {
      await fetchApi<any>(`/merchants/${currentMerchantId}/bahi-khata/log`, {
        method: "POST",
        body: JSON.stringify(data)
      });
      loadData(currentMerchantId);
      triggerSoundbox(`Bahi-Khata logged: Cash ₹${data.cash_in}, Kharcha ₹${data.expense_amount}.`);
    } catch (err) {
      console.error(err);
    }
  };

  const handleReseed = async () => {
    try {
      await fetchApi<any>(`/eval/run`, { method: "POST" });
      loadData(currentMerchantId);
      triggerSoundbox("System data reseeded with 9 months history.");
    } catch (err) {}
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Top Navbar */}
      <header className="h-14 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-6 z-10">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-xl bg-paytm-blue flex items-center justify-center font-black text-white text-lg shadow-md">
            M
          </div>
          <div>
            <h1 className="text-sm font-black tracking-tight text-white flex items-center gap-2">
              MUNIM <span className="text-[11px] text-paytm-blue font-medium">• AI Business Partner</span>
            </h1>
            <div className="text-[10px] text-slate-400">Paytm Merchant Copilot</div>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsEvalModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-bold border border-slate-700 shadow-sm"
          >
            <Award className="w-3.5 h-3.5 text-emerald-400" />
            <span>Eval Dashboard (F1: 1.0)</span>
          </button>

          <button
            onClick={() => setIsDemoModalOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-slate-950 rounded-xl text-xs font-black shadow-md transition-all"
          >
            <Zap className="w-3.5 h-3.5 fill-slate-950" />
            <span>Demo Controls</span>
          </button>
        </div>
      </header>

      {/* Main Split Layout: Soundbox on Left, Phone App on Right */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-6 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Output-Only Soundbox Simulator (4 cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center justify-between px-1">
            <span>Paytm Soundbox Simulator</span>
            <span className="text-[10px] text-cyan-400 font-normal">Physical Hardware Mock</span>
          </div>

          <SoundboxDevice
            lastAnnouncement={lastAnnouncement}
            isBroadcasting={isBroadcasting}
            audioUrl={audioUrl}
            onPlayAudio={() => triggerSoundbox(lastAnnouncement, audioUrl || undefined)}
          />
          <audio ref={audioPlayerRef} id="soundbox-audio-player" className="hidden" preload="auto" />


          {/* Quick Hardware Notice */}
          <div className="p-3 bg-slate-900/60 rounded-2xl border border-slate-800 text-[11px] text-slate-400 space-y-1">
            <div className="font-bold text-slate-300">Soundbox Policy: Output-Only</div>
            <p>
              The Soundbox device only plays audio and announces transaction events. All voice prompts,
              transcription, and approval actions happen strictly on the phone app.
            </p>
          </div>
        </div>

        {/* Right Column: Mobile-First Phone View (8 cols) */}
        <div className="lg:col-span-8 flex justify-center">
          <div className="w-full max-w-md bg-slate-50 text-slate-900 rounded-[36px] shadow-2xl border-8 border-slate-800 overflow-hidden flex flex-col relative h-[680px]">
            {/* Phone Status Bar */}
            <div className="h-7 bg-slate-900 text-white px-5 flex items-center justify-between text-[11px] font-semibold select-none flex-shrink-0">
              <span>9:41 AM</span>
              <div className="w-24 h-3.5 bg-black rounded-b-xl mx-auto" />
              <div className="flex items-center gap-1.5 text-[10px]">
                <span>5G</span>
                <span>100%</span>
              </div>
            </div>

            {/* Phone Header: Merchant Identity */}
            <div className="bg-paytm-dark text-white p-3.5 flex items-center justify-between border-b border-paytm-blue/20 flex-shrink-0">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-paytm-blue flex items-center justify-center font-bold text-xs text-white">
                  SC
                </div>
                <div>
                  <div className="text-xs font-black truncate max-w-[180px]">
                    {merchant?.name || "Sharma Chai & Snacks"}
                  </div>
                  <div className="text-[10px] text-cyan-300">
                    {merchant?.city || "Jaipur"} • Paytm Verified Merchant
                  </div>
                </div>
              </div>

              <button
                onClick={() => setIsDemoModalOpen(true)}
                className="text-[10px] bg-slate-800/80 px-2 py-1 rounded-lg text-slate-200 border border-slate-700 flex items-center gap-1"
              >
                <span>Switch</span>
                <ChevronDown className="w-3 h-3" />
              </button>
            </div>

            {/* Scrollable Phone App Body */}
            <div className="flex-1 overflow-y-auto p-4">
              {activeTab === "home" && (
                <HomeScreen
                  summary={summary}
                  morningBrief={morningBrief}
                  scoreData={scoreData}
                  topOpportunity={opportunities[0]}
                  onApproveOpportunity={opp => {
                    handleResolveApproval(1, "APPROVED");
                    triggerSoundbox(`Naya offer chalu kiya gaya: ${opp.title}`);
                  }}
                  onPlayBriefAudio={() => {
                    if (morningBrief?.spoken_script) {
                      triggerSoundbox(morningBrief.spoken_script);
                    }
                  }}
                  onNavigateTab={tab => setActiveTab(tab)}
                />
              )}

              {activeTab === "talk" && (
                <TalkToMunimScreen
                  merchantId={currentMerchantId}
                  onSendActionApproval={handleResolveApproval}
                  onPlaySpeech={text => triggerSoundbox(text)}
                />
              )}

              {activeTab === "mix" && (
                <WhatISellScreen
                  productMix={productMix}
                  onConfirmItem={handleConfirmItem}
                  onRefresh={() => loadData(currentMerchantId)}
                />
              )}

              {activeTab === "bahi_khata" && (
                <BahiKhataScreen
                  summary={summary}
                  udhaarList={udhaarList}
                  onLogCashExpense={handleLogCashExpense}
                  onSendReminder={handleSendReminder}
                  onAddUdhaar={handleAddUdhaar}
                />
              )}

              {activeTab === "campaigns" && (
                <CampaignsScreen
                  approvals={approvals}
                  campaigns={campaigns}
                  auditLogs={auditLogs}
                  onResolveApproval={handleResolveApproval}
                  onRunUpliftSimulation={handleRunUpliftSimulation}
                />
              )}

              {activeTab === "score" && (
                <ScoreScreen scoreData={scoreData} />
              )}
            </div>

            {/* Phone Bottom Tab Bar */}
            <nav className="h-16 bg-white border-t border-slate-200 flex items-center justify-around px-2 absolute bottom-0 inset-x-0 z-20 shadow-lg">
              <button
                onClick={() => setActiveTab("home")}
                className={`flex flex-col items-center gap-0.5 text-[10px] font-bold ${
                  activeTab === "home" ? "text-paytm-blue" : "text-slate-400 hover:text-slate-600"
                }`}
              >
                <Home className="w-4 h-4" />
                <span>Home</span>
              </button>

              <button
                onClick={() => setActiveTab("talk")}
                className={`flex flex-col items-center gap-0.5 text-[10px] font-bold ${
                  activeTab === "talk" ? "text-paytm-blue" : "text-slate-400 hover:text-slate-600"
                }`}
              >
                <MessageSquare className="w-4 h-4" />
                <span>Munim</span>
              </button>

              <button
                onClick={() => setActiveTab("mix")}
                className={`flex flex-col items-center gap-0.5 text-[10px] font-bold ${
                  activeTab === "mix" ? "text-paytm-blue" : "text-slate-400 hover:text-slate-600"
                }`}
              >
                <PieChart className="w-4 h-4" />
                <span>Menu</span>
              </button>

              <button
                onClick={() => setActiveTab("bahi_khata")}
                className={`flex flex-col items-center gap-0.5 text-[10px] font-bold ${
                  activeTab === "bahi_khata" ? "text-paytm-blue" : "text-slate-400 hover:text-slate-600"
                }`}
              >
                <BookOpen className="w-4 h-4" />
                <span>Bahi-Khata</span>
              </button>

              <button
                onClick={() => setActiveTab("campaigns")}
                className={`flex flex-col items-center gap-0.5 text-[10px] font-bold relative ${
                  activeTab === "campaigns" ? "text-paytm-blue" : "text-slate-400 hover:text-slate-600"
                }`}
              >
                <Megaphone className="w-4 h-4" />
                <span>Offers</span>
                {approvals.length > 0 && (
                  <span className="w-2 h-2 rounded-full bg-rose-500 absolute top-0 right-2" />
                )}
              </button>

              <button
                onClick={() => setActiveTab("score")}
                className={`flex flex-col items-center gap-0.5 text-[10px] font-bold ${
                  activeTab === "score" ? "text-paytm-blue" : "text-slate-400 hover:text-slate-600"
                }`}
              >
                <Award className="w-4 h-4" />
                <span>Score</span>
              </button>
            </nav>
          </div>
        </div>
      </main>

      {/* Modals */}
      <DemoControlPanelModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
        onInjectBurst={handleInjectBurst}
        onSwitchMerchant={id => setCurrentMerchantId(id)}
        onReseed={handleReseed}
        currentMerchantId={currentMerchantId}
      />

      <EvalDashboardModal
        isOpen={isEvalModalOpen}
        onClose={() => setIsEvalModalOpen(false)}
        evalResults={evalResults}
        onRerunEval={async () => {
          await fetchApi(`/eval/run`, { method: "POST" });
          loadData(currentMerchantId);
        }}
      />
    </div>
  );
}
