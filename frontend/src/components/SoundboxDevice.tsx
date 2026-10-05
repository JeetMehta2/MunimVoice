import React, { useState, useEffect } from "react";
import { Volume2, Radio, Sparkles, CheckCircle2, AlertCircle } from "lucide-react";

interface SoundboxDeviceProps {
  lastAnnouncement: string;
  isBroadcasting: boolean;
  audioUrl?: string | null;
  onPlayAudio?: () => void;
}

export const SoundboxDevice: React.FC<SoundboxDeviceProps> = ({
  lastAnnouncement,
  isBroadcasting,
  audioUrl,
  onPlayAudio
}) => {
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    if (isBroadcasting) {
      setPulse(true);
      const timer = setTimeout(() => setPulse(false), 4000);
      return () => clearTimeout(timer);
    }
  }, [isBroadcasting, lastAnnouncement]);

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900 rounded-3xl shadow-2xl border-4 border-slate-700 text-white w-full max-w-sm mx-auto">
      {/* Device Header Bar */}
      <div className="w-full flex items-center justify-between pb-3 border-b border-slate-700/60 mb-4">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-xs font-bold tracking-wider text-slate-300">PAYTM SOUNDBOX 5G</span>
        </div>
        <span className="simulated-badge">
          Simulated Device
        </span>
      </div>

      {/* Speaker Grill Housing */}
      <div className="relative my-4 flex items-center justify-center">
        {/* Animated Sound Pulse Rings */}
        {pulse && (
          <>
            <div className="absolute w-52 h-52 rounded-full border-2 border-cyan-400/40 animate-pulse-ring" />
            <div className="absolute w-64 h-64 rounded-full border border-cyan-400/20 animate-pulse-ring delay-300" />
          </>
        )}

        {/* Physical Circular Speaker Unit */}
        <div className={`relative w-44 h-44 rounded-full bg-gradient-to-tr from-slate-950 to-slate-800 border-8 ${pulse ? 'border-cyan-400 shadow-cyan-500/50 shadow-xl' : 'border-slate-600'} flex flex-col items-center justify-center transition-all duration-500`}>
          <div className="w-32 h-32 rounded-full bg-slate-900 border-4 border-slate-700/80 flex flex-col items-center justify-center shadow-inner">
            <Volume2 className={`w-12 h-12 ${pulse ? 'text-cyan-400 animate-bounce' : 'text-slate-400'}`} />
            <div className="flex gap-1 mt-2">
              <span className={`w-1.5 h-3 rounded-full bg-cyan-400 ${pulse ? 'animate-wave-bar' : 'opacity-40'}`} />
              <span className={`w-1.5 h-5 rounded-full bg-cyan-400 ${pulse ? 'animate-wave-bar delay-100' : 'opacity-40'}`} />
              <span className={`w-1.5 h-7 rounded-full bg-cyan-400 ${pulse ? 'animate-wave-bar delay-200' : 'opacity-40'}`} />
              <span className={`w-1.5 h-5 rounded-full bg-cyan-400 ${pulse ? 'animate-wave-bar delay-100' : 'opacity-40'}`} />
              <span className={`w-1.5 h-3 rounded-full bg-cyan-400 ${pulse ? 'animate-wave-bar' : 'opacity-40'}`} />
            </div>
          </div>
        </div>
      </div>

      {/* Output-Only Status Label */}
      <div className="flex items-center gap-1.5 text-xs text-cyan-300 bg-cyan-950/70 px-3 py-1 rounded-full border border-cyan-700/50 mb-4">
        <Radio className="w-3.5 h-3.5 animate-pulse" />
        <span>AUDIO OUTPUT-ONLY (Mic & Approvals on Phone)</span>
      </div>

      {/* Live Announcement Caption Display */}
      <div className="w-full bg-slate-950/90 rounded-2xl p-4 border border-slate-700/80 shadow-inner">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
          <span>Speaker Announcement:</span>
          {pulse && <span className="text-cyan-400 text-xs">Playing...</span>}
        </div>
        <p className="text-sm font-medium text-slate-100 leading-relaxed min-h-[44px]">
          "{lastAnnouncement || "Paytm par ₹20 prapt hue."}"
        </p>
      </div>

      {/* Manual Audio Replay Trigger */}
      <button
        onClick={onPlayAudio}
        className="mt-4 w-full py-2.5 px-4 bg-cyan-600 hover:bg-cyan-500 active:scale-98 rounded-xl text-xs font-bold text-white flex items-center justify-center gap-2 transition-all shadow-md hover:shadow-cyan-500/25 border border-cyan-400"
      >
        <Volume2 className="w-4 h-4 text-white" />
        <span>Play Announcement Audio</span>
      </button>

      {/* Embedded Native Audio Stream Controls */}
      {audioUrl && (
        <div className="w-full mt-3 bg-slate-950/80 p-2 rounded-xl border border-slate-700/60">
          <audio
            key={audioUrl}
            controls
            src={audioUrl.startsWith("http") ? audioUrl : audioUrl.startsWith("/") ? audioUrl : `/${audioUrl}`}
            className="w-full h-7 opacity-90"
          />
        </div>
      )}

      {/* Bottom Hardware Tag */}
      <div className="mt-4 text-[10px] text-slate-500 flex items-center gap-1">
        <span>Protected Hardware Layer</span> • <span>Non-interactive Output</span>
      </div>
    </div>
  );
};
