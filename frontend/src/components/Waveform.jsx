import { useEffect, useRef } from "react";

const BAR_COUNT = 28;

// Draws a ring of bars around the call button. `level` (0..1) sets the
// target amplitude; the draw loop eases toward it each frame so motion
// stays smooth even though the level prop itself updates at ~20fps.
export default function Waveform({ level, color, radius = 100, active }) {
  const canvasRef = useRef(null);
  const levelRef = useRef(0);
  const smoothedRef = useRef(new Array(BAR_COUNT).fill(0.08));

  useEffect(() => {
    levelRef.current = level;
  }, [level]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const size = (radius + 20) * 2;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);

    let rafId;
    const center = size / 2;

    function draw() {
      ctx.clearRect(0, 0, size, size);
      const smoothed = smoothedRef.current;
      const baseLevel = active ? levelRef.current : 0;

      for (let i = 0; i < BAR_COUNT; i++) {
        const angle = (i / BAR_COUNT) * Math.PI * 2;
        const jitter = active ? Math.sin(Date.now() / 220 + i * 1.7) * 0.12 : 0;
        const target = active ? Math.max(0.06, baseLevel + jitter * baseLevel) : 0.05;
        smoothed[i] += (target - smoothed[i]) * 0.18;

        const barLen = 10 + smoothed[i] * 34;
        const x1 = center + Math.cos(angle) * radius;
        const y1 = center + Math.sin(angle) * radius;
        const x2 = center + Math.cos(angle) * (radius + barLen);
        const y2 = center + Math.sin(angle) * (radius + barLen);

        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.lineCap = "round";
        ctx.lineWidth = 2.4;
        ctx.strokeStyle = color;
        ctx.globalAlpha = active ? 0.35 + smoothed[i] * 0.65 : 0.25;
        ctx.stroke();
      }
      rafId = requestAnimationFrame(draw);
    }
    draw();

    return () => cancelAnimationFrame(rafId);
  }, [color, radius, active]);

  return <canvas ref={canvasRef} style={{ position: "absolute", inset: 0, margin: "auto" }} />;
}
