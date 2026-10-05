import React from "react";
import { ShieldCheck, TrendingUp, Users, CheckCircle2, AlertCircle, ArrowUp } from "lucide-react";

interface ScoreScreenProps {
  scoreData: any;
}

export const ScoreScreen: React.FC<ScoreScreenProps> = ({ scoreData }) => {
  const score = scoreData?.score || 78;
  const factors = scoreData?.factors || {
    consistency: { score: 21, max: 25, label: "Business Consistency" },
    growth: { score: 15, max: 20, label: "Month-over-Month Growth" },
    repeat_rate: { score: 16, max: 20, label: "Customer Loyalty" },
    udhaar_recovery: { score: 13, max: 20, label: "Udhaar Recovery Discipline" },
    cash_discipline: { score: 13, max: 15, label: "Daily Bahi-Khata Logging" }
  };

  return (
    <div className="space-y-4 pb-20">
      {/* 1. Main Score Card */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 text-white p-5 rounded-2xl shadow-xl relative overflow-hidden">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span className="text-xs font-bold tracking-wide uppercase text-slate-300">
              PAYTM MUNIM SCORE
            </span>
          </div>
          <span className="simulated-badge">Simulated</span>
        </div>

        <div className="flex items-center gap-5 my-2">
          <div className="w-20 h-20 rounded-full border-4 border-emerald-400 flex items-center justify-center text-3xl font-black text-white shadow-lg shadow-emerald-500/20">
            {score}
          </div>
          <div>
            <div className="text-xs text-slate-400">Indicative Credit Limit Band:</div>
            <div className="text-xl font-extrabold text-cyan-400">
              {scoreData?.indicative_limit_band || "₹65,000 - ₹85,000"}
            </div>
            <div className="text-[11px] text-emerald-300 mt-1 flex items-center gap-1 font-semibold">
              <ArrowUp className="w-3 h-3" /> Ready for Working Capital Top-up
            </div>
          </div>
        </div>

        {/* Mandatory Underwriting Disclaimer */}
        <div className="mt-4 pt-3 border-t border-slate-700/80 text-[10px] text-slate-400 leading-normal flex items-start gap-1.5">
          <AlertCircle className="w-3.5 h-3.5 text-amber-400 flex-shrink-0 mt-0.5" />
          <span>
            {scoreData?.disclaimer || "Illustrative signal for Paytm's existing underwriting, not a credit decision."}
          </span>
        </div>
      </div>

      {/* 2. 5-Factor Score Breakdown */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
          5-Factor Transparent Formula (100 pts)
        </h4>

        <div className="space-y-3 text-xs">
          {Object.entries(factors).map(([key, f]: [string, any]) => {
            const pct = Math.round((f.score / f.max) * 100);
            return (
              <div key={key} className="space-y-1">
                <div className="flex justify-between font-semibold text-slate-700">
                  <span>{f.label}</span>
                  <span className="font-bold text-slate-900">{f.score} / {f.max} pts</span>
                </div>
                <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-paytm-blue rounded-full transition-all duration-500" 
                    style={{ width: `${pct}%` }} 
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Actionable Advice: What Will Raise It */}
      <div className="bg-emerald-50/70 p-4 rounded-2xl border border-emerald-200 shadow-sm space-y-2">
        <h4 className="text-xs font-bold text-emerald-950 uppercase tracking-wide flex items-center gap-1.5">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          Score Kaise Badhayein (What Raises It)
        </h4>
        <ul className="space-y-1.5 text-xs text-slate-700">
          {(scoreData?.what_raises_it || [
            "Overdue udhaar recover karein (+5 pts).",
            "Rozana cash hisab log karein (+4 pts).",
            "Tuesday slow slot par combo offer chala kar sales badhayein (+3 pts)."
          ]).map((tip: string, idx: number) => (
            <li key={idx} className="flex items-start gap-1.5 leading-relaxed">
              <span className="text-emerald-600 font-bold">•</span>
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};
