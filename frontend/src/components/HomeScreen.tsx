import React from "react";
import { TrendingUp, Volume2, ArrowUpRight, ShieldCheck, Clock, Check, X, Sparkles } from "lucide-react";

interface HomeScreenProps {
  summary: any;
  morningBrief: any;
  scoreData: any;
  topOpportunity: any;
  onApproveOpportunity: (opp: any) => void;
  onPlayBriefAudio: () => void;
  onNavigateTab: (tab: string) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  summary,
  morningBrief,
  scoreData,
  topOpportunity,
  onApproveOpportunity,
  onPlayBriefAudio,
  onNavigateTab
}) => {
  const upiRev = summary?.upi_revenue || 4280;
  const cashIn = summary?.cash_in || 2400;
  const expenses = summary?.total_expense || 740;
  const netProfit = summary?.net_profit || (upiRev + cashIn - expenses);
  const marginPct = summary?.margin_pct || 89.0;
  const score = scoreData?.score || 78;

  return (
    <div className="space-y-4 pb-20">
      {/* 1. Today's True Daily Profit Card */}
      <div className="bg-gradient-to-br from-paytm-dark to-paytm-navy p-5 rounded-2xl text-white shadow-lg relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-paytm-blue/10 rounded-full blur-2xl" />
        <div className="flex items-center justify-between text-xs text-cyan-200 font-medium mb-1">
          <span>AAJ KA SHUDDH MUNAFA (NET PROFIT)</span>
          <span className="bg-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded-full border border-emerald-500/30">
            {marginPct}% Margin
          </span>
        </div>
        <div className="text-3xl font-black text-white tracking-tight mb-3">
          ₹{netProfit.toLocaleString()}
        </div>

        {/* 3-Way Financial Equation */}
        <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-700/60 text-center text-xs">
          <div className="bg-slate-800/60 p-2 rounded-xl border border-slate-700/40">
            <span className="text-slate-400 block text-[10px]">UPI Sales</span>
            <span className="font-bold text-cyan-400">₹{upiRev.toLocaleString()}</span>
          </div>
          <div className="bg-slate-800/60 p-2 rounded-xl border border-slate-700/40">
            <span className="text-slate-400 block text-[10px]">+ Cash Mila</span>
            <span className="font-bold text-amber-400">₹{cashIn.toLocaleString()}</span>
          </div>
          <div className="bg-slate-800/60 p-2 rounded-xl border border-slate-700/40">
            <span className="text-slate-400 block text-[10px]">- Kharcha</span>
            <span className="font-bold text-rose-400">₹{expenses.toLocaleString()}</span>
          </div>
        </div>
      </div>

      {/* 2. Morning Brief Card with Audio Player */}
      {morningBrief && (
        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm relative">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-paytm-blue" />
              <span className="text-xs font-bold text-slate-800 uppercase tracking-wide">
                Daily Morning Brief
              </span>
            </div>
            <button
              onClick={onPlayBriefAudio}
              className="flex items-center gap-1.5 px-3 py-1 bg-cyan-50 text-paytm-blue hover:bg-cyan-100 rounded-full text-xs font-semibold border border-cyan-200 transition-colors"
            >
              <Volume2 className="w-3.5 h-3.5" />
              <span>Suno</span>
            </button>
          </div>
          <p className="text-xs text-slate-600 leading-relaxed font-medium">
            "{morningBrief.spoken_script || "Suprabhat Sharma ji! Kal dukaan par acchi bikri hui. Phone pe pura brief dekhein."}"
          </p>
        </div>
      )}

      {/* 3. Munim Score Ring & Indicative Limit Band */}
      <div 
        onClick={() => onNavigateTab("score")}
        className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm cursor-pointer hover:border-paytm-blue transition-all"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span className="text-xs font-bold text-slate-800">MUNIM SCORE</span>
          </div>
          <span className="simulated-badge">Simulated</span>
        </div>

        <div className="flex items-center gap-4">
          {/* Circular Score Gauge */}
          <div className="relative w-16 h-16 flex items-center justify-center flex-shrink-0">
            <div className="w-16 h-16 rounded-full border-4 border-slate-100 absolute" />
            <div 
              className="w-16 h-16 rounded-full border-4 border-emerald-500 absolute border-t-transparent -rotate-45"
              style={{ clipPath: 'polygon(0 0, 100% 0, 100% 100%, 0 100%)' }}
            />
            <span className="text-lg font-black text-slate-800">{score}</span>
          </div>

          <div className="flex-1">
            <div className="text-xs text-slate-500">Indicative Loan Limit Band:</div>
            <div className="text-sm font-bold text-slate-800">
              {scoreData?.indicative_limit_band || "₹65,000 - ₹85,000"}
            </div>
            <p className="text-[10px] text-slate-400 mt-1 leading-tight">
              {scoreData?.disclaimer || "Illustrative signal for Paytm's existing underwriting, not a credit decision."}
            </p>
          </div>
          <ArrowUpRight className="w-4 h-4 text-slate-400" />
        </div>
      </div>

      {/* 4. Top Opportunity Card (e.g. Tuesday Dead Slot or Churned Customers) */}
      {topOpportunity && (
        <div className="bg-gradient-to-br from-amber-50 to-orange-50 p-4 rounded-2xl border border-amber-200 shadow-sm">
          <div className="flex items-center justify-between mb-1.5">
            <span className="inline-flex items-center gap-1 text-[11px] font-bold text-amber-900 bg-amber-200/70 px-2 py-0.5 rounded-full">
              <Sparkles className="w-3 h-3 text-amber-700" />
              TOP GROWTH OPPORTUNITY
            </span>
            <span className="text-xs font-bold text-emerald-700">
              +₹{topOpportunity.estimated_impact_max || "2,800"} Est.
            </span>
          </div>
          <h4 className="text-sm font-bold text-slate-900 mb-1">
            {topOpportunity.title}
          </h4>
          <p className="text-xs text-slate-600 mb-3 leading-relaxed">
            {topOpportunity.description}
          </p>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onApproveOpportunity(topOpportunity)}
              className="flex-1 py-2 px-3 bg-paytm-blue hover:bg-cyan-600 text-white font-bold text-xs rounded-xl shadow flex items-center justify-center gap-1.5 transition-colors"
            >
              <Check className="w-3.5 h-3.5" />
              <span>Haan, Chalu Karein (Approve)</span>
            </button>
            <button
              className="py-2 px-3 bg-white text-slate-600 hover:bg-slate-100 font-semibold text-xs rounded-xl border border-slate-300"
            >
              Skip
            </button>
          </div>
        </div>
      )}

      {/* 5. Quick Action Links */}
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => onNavigateTab("talk")}
          className="p-3 bg-white hover:bg-slate-50 rounded-xl border border-slate-200 text-left transition-all flex items-center gap-2"
        >
          <div className="w-8 h-8 rounded-lg bg-cyan-100 text-paytm-blue flex items-center justify-center font-bold">
            🎙️
          </div>
          <div>
            <div className="text-xs font-bold text-slate-800">Munim Se Baat</div>
            <div className="text-[10px] text-slate-500">Voice Assistant</div>
          </div>
        </button>

        <button
          onClick={() => onNavigateTab("bahi_khata")}
          className="p-3 bg-white hover:bg-slate-50 rounded-xl border border-slate-200 text-left transition-all flex items-center gap-2"
        >
          <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center font-bold">
            📖
          </div>
          <div>
            <div className="text-xs font-bold text-slate-800">Bahi-Khata</div>
            <div className="text-[10px] text-slate-500">Cash & Udhaar</div>
          </div>
        </button>
      </div>
    </div>
  );
};
