import { useRef } from "react";
import { motion, useMotionValue, useSpring } from "framer-motion";

/**
 * Wraps any button/link so it gently "pulls" toward the cursor on hover,
 * then springs back on leave. Purely a positioning wrapper — style the
 * child normally, this just adds the magnetic motion.
 */
export default function MagneticButton({ children, strength = 16, className = "" }) {
  const ref = useRef(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 200, damping: 14, mass: 0.4 });
  const springY = useSpring(y, { stiffness: 200, damping: 14, mass: 0.4 });

  function handleMouseMove(e) {
    const bounds = ref.current.getBoundingClientRect();
    const relX = e.clientX - bounds.left - bounds.width / 2;
    const relY = e.clientY - bounds.top - bounds.height / 2;
    x.set((relX / (bounds.width / 2)) * strength);
    y.set((relY / (bounds.height / 2)) * strength);
  }

  function handleMouseLeave() {
    x.set(0);
    y.set(0);
  }

  return (
    <motion.div
      ref={ref}
      className={`magnetic-btn ${className}`}
      style={{ x: springX, y: springY, display: "inline-flex" }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      {children}
    </motion.div>
  );
}
