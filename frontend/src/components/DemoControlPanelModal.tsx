import React from "react";
import { Zap, RotateCcw, CloudRain, Users, ShieldAlert, Check } from "lucide-react";

interface DemoControlPanelModalProps {
  isOpen: boolean;
  onClose: () => void;
  onInjectBurst: () => void;
  onSwitchMerchant: (merchantId: string) => void;
  onReseed: () => void;
  currentMerchantId: string;
}

export const DemoControlPanelModal: React.FC<DemoControlPanelModalProps> = ({
  isOpen,
  onClose,
  onInjectBurst,
  onSwitchMerchant,
  onReseed,
  currentMerchantId
}) => {
  if (!isOpen) return null;

  const merchants = [
    { id: "merchant_sharma_chai", name: "Sharma Chai & Snacks (Hero)", type: "Chai Stall" },
    { id: "merchant_gupta_kirana", name: "Gupta Daily Needs", type: "Kirana" },
    { id: "merchant_annapurna_tiffin", name: "Annapurna Tiffin", type: "Tiffin" },
    { id: "merchant_star_salon", name: "Star Men's Grooming", type: "Salon" },
    { id: "merchant_fresh_juice", name: "Fresh Squeeze Corner", type: "Juice Bar" },
    { id: "merchant_golden_crust", name: "Golden Crust Bakery", type: "Bakery" }
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="bg-slate-900 text-white rounded-3xl p-5 w-full max-w-md border border-slate-700 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-700 pb-3">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-amber-400" />
            <h3 className="text-sm font-bold tracking-wider uppercase text-slate-100">
              DEMO CONTROL PANEL
            </h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white text-lg font-bold">
            ✕
          </button>
        </div>

        {/* 1. Live Payment Burst Injection */}
        <div className="p-3 bg-slate-800 rounded-2xl border border-slate-700 space-y-2">
          <div className="text-xs font-bold text-amber-300">
            ⚡ LIVE PAYMENT BURST (Footfall Rush Trigger)
          </div>
          <p className="text-[11px] text-slate-300 leading-relaxed">
            Instantly injects 16 simulated payments in 5 minutes. Triggers Z-score &gt; 2.0 surge
            and activates Soundbox rush voice announcement!
          </p>
          <button
            onClick={() => {
              onInjectBurst();
              onClose();
            }}
            className="w-full py-2 bg-amber-500 hover:bg-amber-600 text-slate-950 font-black text-xs rounded-xl shadow flex items-center justify-center gap-1.5"
          >
            <Zap className="w-4 h-4 fill-slate-950" />
            Inject 16 Payments Now (Trigger Rush)
          </button>
        </div>

        {/* 2. Switch Merchant Archetype */}
        <div className="p-3 bg-slate-800 rounded-2xl border border-slate-700 space-y-2">
          <div className="text-xs font-bold text-cyan-400 flex items-center gap-1">
            <Users className="w-3.5 h-3.5" />
            SWITCH MERCHANT PERSONA (6 Profiles)
          </div>
          <div className="grid grid-cols-2 gap-1.5 text-xs">
            {merchants.map(m => (
              <button
                key={m.id}
                onClick={() => {
                  onSwitchMerchant(m.id);
                  onClose();
                }}
                className={`p-2 rounded-xl text-left border transition-all ${
                  currentMerchantId === m.id
                    ? "bg-paytm-blue text-white border-cyan-400 font-bold"
                    : "bg-slate-900 text-slate-300 border-slate-700 hover:border-slate-500"
                }`}
              >
                <div className="font-semibold truncate">{m.name}</div>
                <div className="text-[10px] opacity-70">{m.type}</div>
              </button>
            ))}
          </div>
        </div>

        {/* 3. Reseed All Data */}
        <div className="pt-2 border-t border-slate-800 flex justify-between items-center">
          <span className="text-[11px] text-slate-400">Deterministic Seed (Seed=42)</span>
          <button
            onClick={() => {
              onReseed();
              onClose();
            }}
            className="px-3 py-1.5 bg-rose-900/60 hover:bg-rose-900 text-rose-200 rounded-lg text-xs font-bold border border-rose-700 flex items-center gap-1"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reseed All 6 Merchants
          </button>
        </div>
      </div>
    </div>
  );
};
