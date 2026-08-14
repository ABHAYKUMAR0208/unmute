import { useEffect, useState } from "react";

function AgentGlyph() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="8" width="16" height="12" rx="4" />
      <path d="M12 8V4M9 4h6" />
      <circle cx="9" cy="14" r="1.2" fill="currentColor" stroke="none" />
      <circle cx="15" cy="14" r="1.2" fill="currentColor" stroke="none" />
    </svg>
  );
}

function ErrorGlyph() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="13" />
      <line x1="12" y1="16.5" x2="12" y2="16.51" />
    </svg>
  );
}

function MicGlyph() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
      <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
      <line x1="12" y1="18" x2="12" y2="22" />
    </svg>
  );
}

/**
 * VoiceCore — one organic, breathing blob standing in for the whole
 * conversation. It sits neutral while idle/connecting, and fills with a
 * radial gradient (orange-red for the agent, blue for the user) the moment
 * that party is actually speaking, growing an internal waveform and
 * sending soft ripples outward. A small mic badge floats on its rim to
 * show live mic/mute status once the call is connected.
 *
 * `state` is one of: idle | connecting | connected | agent-speaking |
 * user-speaking | error
 */
export default function VoiceCore({ state, isLive, micMuted, level = 0 }) {
  const [ripples, setRipples] = useState([]);
  const speaking = state === "agent-speaking" || state === "user-speaking";
  const tone = state === "agent-speaking" ? "agent" : state === "user-speaking" ? "user" : null;

  useEffect(() => {
    if (!speaking) {
      setRipples([]);
      return undefined;
    }
    const spawn = () => {
      const id = `${Date.now()}-${Math.random()}`;
      setRipples((prev) => [...prev.slice(-4), id]);
      setTimeout(() => {
        setRipples((prev) => prev.filter((r) => r !== id));
      }, 1900);
    };
    spawn();
    const interval = setInterval(spawn, 560);
    return () => clearInterval(interval);
  }, [speaking]);

  const badgeState = micMuted ? "muted" : state === "user-speaking" ? "user" : "idle";

  return (
    <div className="core-wrap">
      <div className="ripples" aria-hidden="true">
        {ripples.map((id) => (
          <span key={id} className="ripple" data-tone={tone} />
        ))}
      </div>

      <div className="core" data-state={state}>
        <span className="core__icon">
          {state === "error" ? <ErrorGlyph /> : <AgentGlyph />}
        </span>
        <div className="core__bars" style={{ "--level": Math.min(level, 1) }} aria-hidden="true">
          <span /><span /><span /><span /><span /><span />
        </div>
      </div>

      <div className="mic-badge" data-visible={isLive ? "true" : "false"} data-state={badgeState}>
        <MicGlyph />
      </div>
    </div>
  );
}