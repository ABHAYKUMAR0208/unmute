import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import MagneticButton from "./MagneticButton";

export default function CtaBanner() {
  return (
    <section className="section cta-banner-section">
      <div className="wrap">
        <motion.div
          className="cta-banner reveal"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }}
          transition={{ duration: 0.7, ease: [0.19, 1, 0.22, 1] }}
        >
          <div className="cta-banner__glow" aria-hidden="true" />
          <div className="cta-banner__content">
            <span className="eyebrow eyebrow--violet">Get started</span>
            <h2>Give your front desk a voice that never clocks out.</h2>
            <p>Spin up the console in minutes and hear it handle a real guest request.</p>
            <div className="cta-banner__actions">
              <MagneticButton>
                <Link to="/console" className="btn btn-primary">
                  Try it live
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M13 6l6 6-6 6" />
                  </svg>
                </Link>
              </MagneticButton>
              <MagneticButton>
                <Link to="/solutions" className="btn btn-ghost">
                  See solutions
                </Link>
              </MagneticButton>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
