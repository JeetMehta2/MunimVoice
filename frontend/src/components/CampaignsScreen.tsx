import React, { useState } from "react";
import { ShieldCheck, Check, X, ArrowUpRight, BarChart2, History, Sparkles } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

interface CampaignsScreenProps {
  approvals: any[];
  campaigns: any[];
  auditLogs: any[];
  onResolveApproval: (approvalId: number, decision: string) => void;
  onRunUpliftSimulation: (campaignId: number) => void;
}

export const CampaignsScreen: React.FC<CampaignsScreenProps> = ({
  approvals,
  campaigns,
  auditLogs,
  onResolveApproval,
  onRunUpliftSimulation
}) => {
  const [selectedUpliftCampaign, setSelectedUpliftCampaign] = useState<any>(null);

  return (
    <div className="space-y-4 pb-20">
      {/* 1. Approvals Queue (Tier 2 Actions) */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-amber-600" />
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              APPROVALS QUEUE (Tier 2 Governed Actions)
            </h3>
          </div>
          <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">
            {approvals.length} Pending
          </span>
        </div>

        {approvals.length > 0 ? (
          approvals.map((app: any) => (
            <div key={app.id} className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-900">{app.action}</span>
                <span className="text-[10px] text-amber-800 font-bold bg-amber-200/60 px-1.5 py-0.5 rounded">
                  Risk Tier 2
                </span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-medium">
                {app.payload?.offer_text || app.payload?.message || "Outbound campaign awaiting approval."}
              </p>
              <div className="flex gap-2 pt-1">
                <button
                  onClick={() => onResolveApproval(app.id, "APPROVED")}
                  className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg flex items-center justify-center gap-1 shadow-sm"
                >
                  <Check className="w-3.5 h-3.5" /> Haan, Approve Karein
                </button>
                <button
                  onClick={() => onResolveApproval(app.id, "REJECTED")}
                  className="py-1.5 px-3 bg-slate-200 hover:bg-slate-300 text-slate-700 text-xs font-semibold rounded-lg"
                >
                  Nahi
                </button>
              </div>
            </div>
          ))
        ) : (
          <div className="text-xs text-slate-400 py-3 text-center bg-slate-50 rounded-xl border border-dashed border-slate-200">
            Koi pending approval nahi hai. Sabhi actions updated hain.
          </div>
        )}
      </div>

      {/* 2. Active & Completed Campaigns with Uplift Measurement */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
            RUNNING CAMPAIGNS & UPLIFT
          </h3>
          <span className="simulated-badge">Simulated</span>
        </div>

        <div className="space-y-2.5">
          {campaigns.map((camp: any) => {
            const uplift = camp.simulated_uplift ? JSON.parse(camp.simulated_uplift) : null;
            return (
              <div key={camp.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-900">{camp.name}</span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    camp.status === 'COMPLETED' ? 'bg-emerald-100 text-emerald-800' : 'bg-cyan-100 text-paytm-blue'
                  }`}>
                    {camp.status}
                  </span>
                </div>
                <p className="text-xs text-slate-600">{camp.offer_text}</p>

                {uplift ? (
                  <div className="p-2.5 bg-emerald-50/70 border border-emerald-200 rounded-lg text-xs space-y-1.5">
                    <div className="flex items-center justify-between font-bold text-emerald-900">
                      <span>Uplift vs Holdout (80/20):</span>
                      <span className="text-emerald-700">+{uplift.uplift_pct}%</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] text-slate-600">
                      <div>Treatment Conversion: <strong>{uplift.treatment_conversion_rate}%</strong></div>
                      <div>Holdout Baseline: <strong>{uplift.holdout_conversion_rate}%</strong></div>
                    </div>
                    <div className="text-[10px] text-emerald-800 italic">
                      {uplift.verdict}
                    </div>
                  </div>
                ) : (
                  <button
                    onClick={() => onRunUpliftSimulation(camp.id)}
                    className="w-full py-1.5 bg-paytm-blue hover:bg-cyan-600 text-white text-xs font-bold rounded-lg flex items-center justify-center gap-1.5"
                  >
                    <BarChart2 className="w-3.5 h-3.5" /> Measure Uplift vs Holdout
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. Immutable Audit Log */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-slate-600" />
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wide">
              IMMUTABLE AUDIT LOG (Tier 0/1/2)
            </h3>
          </div>
          <span className="text-[10px] text-slate-400">Tamper-Proof</span>
        </div>

        <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1 text-xs">
          {auditLogs.slice(0, 10).map((log: any) => (
            <div key={log.id} className="p-2 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between">
              <div>
                <span className="font-bold text-slate-800 block text-[11px]">{log.action}</span>
                <span className="text-[10px] text-slate-400">{log.timestamp?.slice(11, 19)} • Actor: {log.actor}</span>
              </div>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
                Tier {log.risk_tier}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
