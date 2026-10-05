import React, { useState } from "react";
import { BookOpen, Mic, Check, Send, AlertTriangle, Clock, User, ShieldAlert } from "lucide-react";

interface BahiKhataScreenProps {
  summary: any;
  udhaarList: any[];
  onLogCashExpense: (data: any) => void;
  onSendReminder: (udhaarId: number, tone: string) => void;
  onAddUdhaar: (name: string, amount: number) => void;
}

export const BahiKhataScreen: React.FC<BahiKhataScreenProps> = ({
  summary,
  udhaarList,
  onLogCashExpense,
  onSendReminder,
  onAddUdhaar
}) => {
  const [activeTab, setActiveTab] = useState<"cash" | "udhaar">("cash");
  const [transcriptInput, setTranscriptInput] = useState("Cash 3200 aaya aur doodh ka 600 diya");
  const [parsedPreview, setParsedPreview] = useState<any>(null);
  const [selectedDebtor, setSelectedDebtor] = useState<any>(null);
  const [reminderTone, setReminderTone] = useState<"soft" | "firm" | "funny">("soft");

  // New Udhaar input state
  const [newCustName, setNewCustName] = useState("");
  const [newCustAmount, setNewCustAmount] = useState("");

  const handleParseVoice = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/bahi-khata/parse-voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcript: transcriptInput })
      });
      const data = await res.json();
      setParsedPreview(data);
    } catch (err) {
      alert("Voice parsing error");
    }
  };

  const handleConfirmLog = () => {
    if (!parsedPreview) return;
    const cat = parsedPreview.expenses[0]?.category || "milk";
    const amt = parsedPreview.expenses[0]?.amount || 0;
    onLogCashExpense({
      cash_in: parsedPreview.cash_in,
      expense_category: cat,
      expense_amount: amt,
      expense_desc: parsedPreview.transcript
    });
    setParsedPreview(null);
  };

  return (
    <div className="space-y-4 pb-20">
      {/* Subnavigation Switcher */}
      <div className="flex bg-slate-200/80 p-1 rounded-xl">
        <button
          onClick={() => setActiveTab("cash")}
          className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all ${
            activeTab === "cash" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
          }`}
        >
          Daily Cash & Expenses
        </button>
        <button
          onClick={() => setActiveTab("udhaar")}
          className={`flex-1 py-1.5 text-xs font-bold rounded-lg transition-all ${
            activeTab === "udhaar" ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
          }`}
        >
          Udhaar Ledger ({udhaarList?.length || 0})
        </button>
      </div>

      {/* --- Tab 1: Daily Cash & Expense Ritual --- */}
      {activeTab === "cash" && (
        <div className="space-y-4">
          {/* End-of-Day Ritual Prompt */}
          <div className="bg-amber-50 p-4 rounded-2xl border border-amber-200 shadow-sm">
            <div className="flex items-center gap-2 mb-1.5 text-xs font-bold text-amber-900">
              <Clock className="w-4 h-4 text-amber-700" />
              <span>ROZANA BAHI-KHATA RITUAL</span>
            </div>
            <p className="text-xs text-slate-700 mb-3 leading-relaxed">
              "Aaj cash kitna aaya? Kharcha kitna hua?" Bolein ya neeche likhein:
            </p>

            <div className="flex gap-2 mb-3">
              <input
                type="text"
                value={transcriptInput}
                onChange={e => setTranscriptInput(e.target.value)}
                placeholder="Jaise: Cash 3200 mila aur doodh ka 600 diya"
                className="flex-1 px-3 py-2 bg-white rounded-xl text-xs border border-amber-300 focus:outline-none focus:ring-2 focus:ring-paytm-blue"
              />
              <button
                onClick={handleParseVoice}
                className="px-3 py-2 bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs rounded-xl shadow-sm"
              >
                Parse
              </button>
            </div>

            {/* Confirmation Preview */}
            {parsedPreview && (
              <div className="p-3 bg-white rounded-xl border border-amber-300 space-y-2">
                <div className="text-xs font-bold text-slate-800">
                  {parsedPreview.confirmation_message}
                </div>
                <div className="text-[11px] text-slate-500">
                  Cash In: ₹{parsedPreview.cash_in} | Total Expense: ₹{parsedPreview.total_expense}
                </div>
                <button
                  onClick={handleConfirmLog}
                  className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-lg flex items-center justify-center gap-1.5"
                >
                  <Check className="w-3.5 h-3.5" /> Sahi Hai, Darj Karo (Confirm Log)
                </button>
              </div>
            )}
          </div>

          {/* Today's Expense Breakdown */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-2">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Aaj Ke Kharchon Ki List
            </h4>
            {summary?.expense_breakdown?.length > 0 ? (
              summary.expense_breakdown.map((exp: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-100">
                  <div>
                    <span className="font-semibold text-slate-800 capitalize">{exp.category}</span>
                    <span className="text-[10px] text-slate-400 block">{exp.description}</span>
                  </div>
                  <span className="font-bold text-rose-600">₹{exp.amount}</span>
                </div>
              ))
            ) : (
              <div className="text-xs text-slate-400 py-2 text-center">Koi kharcha darj nahi hua.</div>
            )}
          </div>
        </div>
      )}

      {/* --- Tab 2: Udhaar Ledger & Reminders --- */}
      {activeTab === "udhaar" && (
        <div className="space-y-4">
          {/* Quick Add Debtor */}
          <div className="bg-white p-3.5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-2">
            <input
              type="text"
              placeholder="Grahak ka naam"
              value={newCustName}
              onChange={e => setNewCustName(e.target.value)}
              className="flex-1 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs"
            />
            <input
              type="number"
              placeholder="₹ Rakam"
              value={newCustAmount}
              onChange={e => setNewCustAmount(e.target.value)}
              className="w-24 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs"
            />
            <button
              onClick={() => {
                if (newCustName && newCustAmount) {
                  onAddUdhaar(newCustName, parseFloat(newCustAmount));
                  setNewCustName("");
                  setNewCustAmount("");
                }
              }}
              className="px-3 py-1.5 bg-paytm-blue text-white font-bold text-xs rounded-lg hover:bg-cyan-600"
            >
              Add
            </button>
          </div>

          {/* Ledger Table */}
          <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Pending Udhaar & Aging
              </h4>
              <span className="text-[10px] text-slate-400">Private Merchant View</span>
            </div>

            <div className="space-y-2">
              {udhaarList.map((item: any) => (
                <div
                  key={item.id}
                  className={`p-3 rounded-xl border flex items-center justify-between ${
                    item.is_critical
                      ? "bg-rose-50/70 border-rose-200"
                      : "bg-slate-50 border-slate-200"
                  }`}
                >
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-bold text-slate-900">{item.customer_name}</span>
                      {item.is_critical && (
                        <span className="text-[9px] bg-rose-200 text-rose-800 px-1.5 py-0.2 rounded font-bold">
                          15+ Din Overdue
                        </span>
                      )}
                    </div>
                    <div className="text-[10px] text-slate-500 mt-0.5">
                      Due: {item.due_date} • {item.days_overdue > 0 ? `${item.days_overdue} din late` : 'Time par'}
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="font-bold text-xs text-slate-900">₹{item.amount}</span>
                    <button
                      onClick={() => setSelectedDebtor(item)}
                      className="px-2.5 py-1 bg-paytm-blue hover:bg-cyan-600 text-white rounded-lg text-xs font-semibold flex items-center gap-1 shadow-sm"
                    >
                      <Send className="w-3 h-3" /> Remind
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tone Selector & Reminder Dispatch Modal */}
          {selectedDebtor && (
            <div className="p-4 bg-slate-900 text-white rounded-2xl shadow-xl space-y-3 border border-slate-700">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-cyan-400">
                  PAYTM UPI-COLLECT REMINDER (Tier 2 Guardrail)
                </span>
                <button onClick={() => setSelectedDebtor(null)} className="text-slate-400 hover:text-white">
                  ✕
                </button>
              </div>

              <div className="text-xs text-slate-300">
                Debtor: <strong className="text-white">{selectedDebtor.customer_name}</strong> (₹{selectedDebtor.amount})
              </div>

              {/* 3 Tone Pickers */}
              <div className="flex gap-1.5">
                {(["soft", "firm", "funny"] as const).map(tone => (
                  <button
                    key={tone}
                    onClick={() => setReminderTone(tone)}
                    className={`flex-1 py-1.5 text-xs font-bold rounded-lg capitalize border ${
                      reminderTone === tone
                        ? "bg-paytm-blue border-cyan-300 text-white shadow-sm"
                        : "bg-slate-800 border-slate-700 text-slate-300"
                    }`}
                  >
                    {tone}
                  </button>
                ))}
              </div>

              {/* Draft Message Preview */}
              <div className="p-2.5 bg-slate-950 rounded-xl text-xs text-slate-300 leading-relaxed border border-slate-800">
                {reminderTone === "firm" && `Namaste ${selectedDebtor.customer_name} ji, aapka ₹${selectedDebtor.amount} ka hisab overdue hai. Kripya UPI link se settle karein.`}
                {reminderTone === "funny" && `Arrey ${selectedDebtor.customer_name} bhai! Chai ki dosti barkarar rahe, bas ₹${selectedDebtor.amount} ka hisab clear kar dein! 😊`}
                {reminderTone === "soft" && `Namaste ${selectedDebtor.customer_name} ji, aasha hai sab badhiya hai. Ek chhota sa reminder aapke ₹${selectedDebtor.amount} ke hisab ke liye. Shukriya!`}
              </div>

              <button
                onClick={() => {
                  onSendReminder(selectedDebtor.id, reminderTone);
                  setSelectedDebtor(null);
                }}
                className="w-full py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs rounded-xl flex items-center justify-center gap-1.5 shadow"
              >
                <Check className="w-4 h-4" /> Bhejo (Request Tier 2 Approval)
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
