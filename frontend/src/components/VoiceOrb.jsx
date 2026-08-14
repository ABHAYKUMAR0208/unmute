import { motion } from "framer-motion";
import BarRing from "./BarRing";

const WAVE_BARS = 5;

function OrbWave({ level = 0 }) {
  return (
    <div className="voice-orb__wave" aria-hidden="true">
      {Array.from({ length: WAVE_BARS }, (_, i) => {
        const base = 0.35 + Math.min(level, 1) * 0.55;
        return (
          <motion.span
            key={i}
            className="voice-orb__wave-bar"
            animate={{ scaleY: [base * 0.5, base + 0.25, base * 0.6, base + 0.15, base * 0.5] }}
            transition={{
              duration: 0.9 + i * 0.08,
              repeat: Infinity,
              ease: "easeInOut",
              delay: i * 0.09,
            }}
          />
        );
      })}
    </div>
  );
}

function MicGlyph() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
      <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
      <line x1="12" y1="18" x2="12" y2="22" />
    </svg>
  );
}

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

/**
 * A single speaker orb — used twice in CallConsole (once for the user, once
 * for the agent). When `active` it fills with the role's gradient, grows a
 * ring of live waveform bars around its rim, and shows a small internal
 * waveform too — so it's unmistakable which party is currently talking.
 * Otherwise it sits as a quiet outlined circle with no ring at all.
 */
export default function VoiceOrb({ role, label, active, level = 0, disabled = false }) {
  const tone = role === "user" ? "you" : "agent";

  return (
    <div className="voice-orb" data-role={role} data-disabled={disabled ? "true" : "false"}>
      <div className="voice-orb__ringwrap">
        <BarRing level={level} active={active} tone={tone} radius={70} />

        <motion.div
          className="voice-orb__circle"
          data-active={active ? "true" : "false"}
          animate={{
            scale: active ? 1 + Math.min(level, 1) * 0.1 : 1,
          }}
          transition={{ type: "spring", stiffness: 260, damping: 22 }}
        >
          <motion.div
            className="voice-orb__glow"
            animate={{ opacity: active ? 1 : 0 }}
            transition={{ duration: 0.4 }}
          />
          <span className="voice-orb__idle-icon">
            {role === "user" ? <MicGlyph /> : <AgentGlyph />}
          </span>
          {active && <OrbWave level={level} />}
        </motion.div>
      </div>
      <span className="voice-orb__label">{label}</span>
    </div>
  );
}