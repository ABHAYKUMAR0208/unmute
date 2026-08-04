import { useEffect, useRef } from "react";

const TOTAL = 32;

/**
 * BarRing — 32-span DOM bar ring.
 * Each bar's transform is pre-computed via CSS custom property --i.
 * The audio level is distributed across bars via JS each animation frame.
 *
 * Props:
 *   level     — 0..1 audio level
 *   active    — bool, whether the call is live
 *   tone      — "you" | "agent" | "idle"
 */
export default function BarRing({ level = 0, active = false, tone = "idle" }) {
  const containerRef = useRef(null);
  const smoothedRef = useRef(new Array(TOTAL).fill(0));
  const levelRef = useRef(level);
  const rafRef = useRef(null);

  useEffect(() => {
    levelRef.current = level;
  }, [level]);

  useEffect(() => {
    const bars = containerRef.current?.querySelectorAll(".bar-ring__bar");
    if (!bars) return;

    function frame() {
      const baseLevel = active ? levelRef.current : 0;
      const smoothed = smoothedRef.current;

      for (let i = 0; i < TOTAL; i++) {
        const jitter = active
          ? Math.sin(Date.now() / 200 + i * 1.8) * 0.15
          : 0;
        const target = active ? Math.max(0.04, baseLevel + jitter * baseLevel) : 0;
        smoothed[i] += (target - smoothed[i]) * 0.2;
        bars[i].style.setProperty("--level", smoothed[i].toFixed(3));
      }
      rafRef.current = requestAnimationFrame(frame);
    }

    rafRef.current = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(rafRef.current);
  }, [active]);

  return (
    <div ref={containerRef} className={`bar-ring bar-ring--${tone}`} aria-hidden="true">
      {Array.from({ length: TOTAL }, (_, i) => (
        <span
          key={i}
          className="bar-ring__bar"
          style={{ "--i": i, transform: `rotate(${(i / TOTAL) * 360}deg) translateY(-118px)` }}
        />
      ))}
    </div>
  );
}
