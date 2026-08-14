import { useEffect, useRef, useState } from "react";
import { motion, useInView } from "framer-motion";

const STATS = [
  { value: 500, suffix: "+", label: "Properties live" },
  { value: 2.4, suffix: "M", decimals: 1, label: "Calls handled" },
  { value: 280, suffix: "ms", label: "Avg. response time" },
  { value: 99.9, suffix: "%", decimals: 1, label: "Uptime" },
];

function useCountUp(target, inView, duration = 1.4, decimals = 0) {
  const [value, setValue] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    if (!inView || started.current) return;
    started.current = true;
    const start = performance.now();
    let raf;

    function tick(now) {
      const progress = Math.min((now - start) / (duration * 1000), 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(target * eased);
      if (progress < 1) raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, target, duration]);

  return value.toFixed(decimals);
}

function Stat({ stat, index }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const display = useCountUp(stat.value, inView, 1.2 + index * 0.15, stat.decimals ?? 0);

  return (
    <motion.div
      ref={ref}
      className="stat-card"
      initial={{ opacity: 0, y: 24 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.6, delay: index * 0.08, ease: [0.19, 1, 0.22, 1] }}
      whileHover={{ y: -4 }}
    >
      <div className="stat-card__value">
        {display}
        <span className="stat-card__suffix">{stat.suffix}</span>
      </div>
      <div className="stat-card__label">{stat.label}</div>
    </motion.div>
  );
}

export default function StatsBand() {
  return (
    <section className="stats-band" aria-label="Key metrics">
      <div className="wrap stats-band__grid">
        {STATS.map((stat, i) => (
          <Stat key={stat.label} stat={stat} index={i} />
        ))}
      </div>
    </section>
  );
}