import React, { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Check, HelpCircle, Sparkles, RefreshCw } from "lucide-react";

interface ProductMixItem {
  amount: number;
  frequency: number;
  percentage: number;
  confirmed: boolean;
  confirmed_item?: string;
  confidence: number;
  candidates: Array<{ name: string; confidence: number; composition: string }>;
}

interface WhatISellScreenProps {
  productMix: ProductMixItem[];
  onConfirmItem: (amount: number, itemName: string) => void;
  onRefresh: () => void;
}

export const WhatISellScreen: React.FC<WhatISellScreenProps> = ({
  productMix,
  onConfirmItem,
  onRefresh
}) => {
  const [selectedItem, setSelectedItem] = useState<ProductMixItem | null>(null);

  const chartData = (productMix || []).slice(0, 8).map(item => ({
    name: `₹${item.amount}`,
    amount: item.amount,
    frequency: item.frequency,
    itemName: item.confirmed ? item.confirmed_item : (item.candidates[0]?.name || "Inferred"),
    confirmed: item.confirmed
  }));

  return (
    <div className="space-y-4 pb-20">
      {/* Header Banner */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-paytm-blue" />
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
              WHAT I SELL (Inferred Product Mix)
            </h3>
          </div>
          <button onClick={onRefresh} className="text-slate-400 hover:text-slate-600">
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
        <p className="text-xs text-slate-500 leading-relaxed">
          POS machine ke bina, sirf payment amounts se aapka menu infer kiya gaya hai.
          Confirm karne par prior models update ho jate hain.
        </p>
      </div>

      {/* Frequency Distribution Chart */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-3">
          Top Price Points by Volume
        </h4>
        <div className="h-44 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 5, right: 10, left: -25, bottom: 0 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload;
                    return (
                      <div className="bg-slate-900 text-white p-2 rounded-xl text-xs shadow-lg">
                        <div className="font-bold">{data.name}: {data.itemName}</div>
                        <div className="text-slate-300">{data.frequency} orders</div>
                        {data.confirmed && <div className="text-emerald-400 text-[10px]">✓ Confirmed by Merchant</div>}
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar dataKey="frequency" radius={[6, 6, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.confirmed ? "#10B981" : "#00BAF2"} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Interactive Bayesian Confirmation Chips */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Confirm Inferred Items (Bayesian Priors)
          </h4>
          <span className="text-[10px] text-slate-400">Tap to confirm</span>
        </div>

        <div className="space-y-2">
          {productMix.slice(0, 6).map(item => {
            const topCandidate = item.candidates[0]?.name || "Item";
            return (
              <div
                key={item.amount}
                className={`p-3 rounded-xl border flex items-center justify-between transition-all ${
                  item.confirmed
                    ? "bg-emerald-50/60 border-emerald-200"
                    : "bg-slate-50 border-slate-200 hover:border-paytm-blue"
                }`}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-xs text-slate-900">₹{item.amount}</span>
                    <span className="text-xs text-slate-600 font-medium">
                      = {item.confirmed ? item.confirmed_item : topCandidate}
                    </span>
                    {item.confirmed ? (
                      <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-bold">
                        Confirmed (Prior 1.0)
                      </span>
                    ) : (
                      <span className="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-bold">
                        {Math.round(item.confidence * 100)}% Conf.
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-400 mt-0.5">
                    {item.frequency} payments ({item.percentage}% volume)
                  </div>
                </div>

                {!item.confirmed && (
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => onConfirmItem(item.amount, topCandidate)}
                      className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold flex items-center gap-1 shadow-sm"
                    >
                      <Check className="w-3 h-3" /> Sahi Hai (Haan)
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
