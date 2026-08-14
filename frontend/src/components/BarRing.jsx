import { useEffect, useRef } from "react";

const TOTAL = 32;

/**
 * BarRing — circular waveform ring of thin bars fanned out around a
 * center point. Drives its animation purely through CSS custom
 * properties (--i is set once per bar, --level is updated every frame),
 * so the actual transform — rotate + outward offset + scale — lives in
 * CSS and stays snappy without React re-renders.
 *
 * Props:
 *   level   — 0..1 audio level for the speaker this ring represents
 *   active  — bool, whether this party is currently speaking
 *   tone    — "you" | "agent" | "idle" — controls the ring's color
 *   radius  — px distance from center to each bar's resting point
 */
export default function BarRing({ level = 0, active = false, tone = "idle", radius = 74 }) {
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
        // Each bar gets its own gentle sine jitter so the ring reads as a
        // live waveform rather than a uniform pulsing circle.
        const jitter = active ? Math.sin(Date.now() / 180 + i * 1.7) * 0.35 : 0;
        const target = active ? Math.max(0.08, baseLevel + jitter * baseLevel) : 0;
        smoothed[i] += (target - smoothed[i]) * 0.22;
        bars[i].style.setProperty("--level", smoothed[i].toFixed(3));
      }
      rafRef.current = requestAnimationFrame(frame);
    }

    rafRef.current = requestAnimationFrame(frame);
    return () => cancelAnimationFrame(rafRef.current);
  }, [active]);

  return (
    <div
      ref={containerRef}
      className={`bar-ring bar-ring--${tone}`}
      data-active={active ? "true" : "false"}
      style={{ "--radius": `${radius}px` }}
      aria-hidden="true"
    >
      {Array.from({ length: TOTAL }, (_, i) => (
        <span key={i} className="bar-ring__bar" style={{ "--i": i, "--total": TOTAL }} />
      ))}
    </div>
  );
}