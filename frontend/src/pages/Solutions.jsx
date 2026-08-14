import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  AnimatePresence,
  motion,
  useMotionTemplate,
  useMotionValue,
  useScroll,
  useSpring,
  useTransform,
} from "framer-motion";
import Nav from "../components/Nav";
import Footer from "../components/Footer";
import ParticleField from "../components/ParticleField";
import MagneticButton from "../components/MagneticButton";
import "./Solutions.css";

function useReveal() {
  useEffect(() => {
    const els = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window)) {
      els.forEach((el) => el.classList.add("is-visible"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            io.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
}

const USE_CASES = [
  {
    title: "Customer support triage",
    body: "Route and resolve inbound calls before they reach a human. The agent asks the right questions, updates records, and escalates only when needed.",
    tag: "Support",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.3 1.8.6 2.7a2 2 0 0 1-.4 2.1L8 9.9a16 16 0 0 0 6 6l1.4-1.4a2 2 0 0 1 2.1-.4c.9.3 1.8.5 2.7.6a2 2 0 0 1 1.8 2.2z" />
      </svg>
    ),
  },
  {
    title: "AI phone interview",
    body: "Screen candidates at scale with a natural back-and-forth voice interview. Transcripts and summaries land in your ATS automatically.",
    tag: "Recruiting",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  {
    title: "Appointment scheduling",
    body: "Let patients, clients, or customers book and reschedule by speaking naturally. No hold music, no forms, no frustration.",
    tag: "Scheduling",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" />
        <line x1="16" y1="2" x2="16" y2="6" />
        <line x1="8" y1="2" x2="8" y2="6" />
        <line x1="3" y1="10" x2="21" y2="10" />
      </svg>
    ),
  },
  {
    title: "Sales qualification",
    body: "Engage inbound leads the moment they arrive — qualify intent, answer objections, and hand off warm opportunities to your team.",
    tag: "Sales",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
        <polyline points="16 7 22 7 22 13" />
      </svg>
    ),
  },
  {
    title: "Field operations dispatch",
    body: "Technicians call in updates, request parts, and log job status by voice — no app, no screen, no stopping what they're doing.",
    tag: "Operations",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3" />
        <path d="M12 2v3M12 19v3M4.22 4.22l2.12 2.12M17.66 17.66l2.12 2.12M2 12h3M19 12h3M4.22 19.78l2.12-2.12M17.66 6.34l2.12-2.12" />
      </svg>
    ),
  },
  {
    title: "Developer platform",
    body: "A self-hostable WebRTC + LiveKit stack you can fork, instrument, and ship under your own brand — full source, no vendor lock-in.",
    tag: "Platform",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    ),
  },
];

const PIPELINE = [
  {
    num: "01",
    title: "Browser WebRTC",
    body: "Your microphone audio streams to the agent over a peer-to-peer WebRTC connection the moment you connect.",
    badge: "getUserMedia → RTCPeerConnection",
  },
  {
    num: "02",
    title: "LiveKit room",
    body: "LiveKit handles the media server layer — track publishing, subscribing, and the data channel for transcript events.",
    badge: "livekit-client SDK",
  },
  {
    num: "03",
    title: "Agent worker",
    body: "A Python agent worker running on the backend subscribes to the room, STT-decodes audio, calls the LLM, and TTS-streams the reply.",
    badge: "livekit-agents",
  },
  {
    num: "04",
    title: "Audio reply",
    body: "The TTS audio track streams back into the room. The browser subscribes and plays it automatically — no latency buffer.",
    badge: "AudioTrack → HTMLAudioElement",
  },
];

/* ============================================================
   SMOOTH PAGE LOADER — brief branded entrance before the hero
   reveals itself. Purely cosmetic, auto-dismisses.
   ============================================================ */
function PageLoader({ onDone }) {
  useEffect(() => {
    const t = setTimeout(onDone, 900);
    return () => clearTimeout(t);
  }, [onDone]);

  return (
    <motion.div
      className="page-loader"
      initial={{ opacity: 1 }}
      exit={{ opacity: 0, scale: 1.04, transition: { duration: 0.5, ease: [0.19, 1, 0.22, 1] } }}
    >
      <motion.div
        className="page-loader__mark"
        initial={{ scale: 0.6, opacity: 0, rotate: -12 }}
        animate={{ scale: 1, opacity: 1, rotate: 0 }}
        transition={{ duration: 0.5, ease: [0.19, 1, 0.22, 1] }}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="16 18 22 12 16 6" />
          <polyline points="8 6 2 12 8 18" />
        </svg>
      </motion.div>
      <div className="page-loader__bars" aria-hidden="true">
        {Array.from({ length: 5 }, (_, i) => (
          <span key={i} style={{ animationDelay: `${i * 0.09}s` }} />
        ))}
      </div>
      <motion.span
        className="page-loader__label"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.4 }}
      >
        Loading solutions…
      </motion.span>
    </motion.div>
  );
}

/* ============================================================
   TILT CARD — wraps each use-case in a cursor-reactive 3D tilt
   plus a soft spotlight that follows the pointer. Entrance is a
   staggered fade/rise on scroll (whileInView).
   ============================================================ */
function TiltCard({ index, children }) {
  const ref = useRef(null);
  const rotateX = useMotionValue(0);
  const rotateY = useMotionValue(0);
  const springRX = useSpring(rotateX, { stiffness: 210, damping: 20, mass: 0.5 });
  const springRY = useSpring(rotateY, { stiffness: 210, damping: 20, mass: 0.5 });
  const spotX = useMotionValue(50);
  const spotY = useMotionValue(50);
  const spotlight = useMotionTemplate`radial-gradient(220px circle at ${spotX}% ${spotY}%, rgba(124,140,255,0.16), transparent 70%)`;

  function handleMove(e) {
    const b = ref.current.getBoundingClientRect();
    const px = (e.clientX - b.left) / b.width;
    const py = (e.clientY - b.top) / b.height;
    rotateY.set((px - 0.5) * 10);
    rotateX.set((0.5 - py) * 10);
    spotX.set(px * 100);
    spotY.set(py * 100);
  }

  function handleLeave() {
    rotateX.set(0);
    rotateY.set(0);
  }

  return (
    <motion.article
      ref={ref}
      className="use-case"
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      style={{ rotateX: springRX, rotateY: springRY, transformPerspective: 900 }}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, delay: (index % 3) * 0.08, ease: [0.19, 1, 0.22, 1] }}
    >
      <motion.div className="use-case__spotlight" style={{ background: spotlight }} aria-hidden="true" />
      {children}
    </motion.article>
  );
}

const heroReveal = {
  hidden: {},
  show: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
};
const heroItem = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.19, 1, 0.22, 1] } },
};

const gridStagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.09 } },
};
const gridItem = {
  hidden: { opacity: 0, y: 26 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.19, 1, 0.22, 1] } },
};

export default function Solutions() {
  useReveal();
  const [loading, setLoading] = useState(true);

  const heroRef = useRef(null);
  const { scrollYProgress: heroProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const glowY = useTransform(heroProgress, [0, 1], [0, 90]);
  const gridY = useTransform(heroProgress, [0, 1], [0, -40]);
  const orbAY = useTransform(heroProgress, [0, 1], [0, 70]);
  const orbBY = useTransform(heroProgress, [0, 1], [0, -50]);

  const pipelineRef = useRef(null);
  const { scrollYProgress: pipelineProgress } = useScroll({
    target: pipelineRef,
    offset: ["start 85%", "start 35%"],
  });
  const lineScale = useSpring(pipelineProgress, { stiffness: 90, damping: 22, mass: 0.6 });

  return (
    <>
      <AnimatePresence>
        {loading && <PageLoader onDone={() => setLoading(false)} />}
      </AnimatePresence>

      <Nav variant="default" />
      <main>
        {/* ===== HERO ===== */}
        <section className="solutions-hero" ref={heroRef}>
          <motion.div className="solutions-hero__glow" style={{ y: glowY }} aria-hidden="true" />
          <motion.div className="solutions-hero__grid" style={{ y: gridY }} aria-hidden="true" />
          <motion.div className="solutions-hero__orb solutions-hero__orb--a" style={{ y: orbAY }} aria-hidden="true" />
          <motion.div className="solutions-hero__orb solutions-hero__orb--b" style={{ y: orbBY }} aria-hidden="true" />
          <div className="solutions-hero__particles" aria-hidden="true">
            <ParticleField count={34} color="124, 140, 255" />
          </div>

          <motion.div
            className="wrap solutions-hero__inner"
            variants={heroReveal}
            initial="hidden"
            animate={loading ? "hidden" : "show"}
          >
            <motion.span className="eyebrow eyebrow--violet" style={{ justifyContent: "center" }} variants={heroItem}>
              Solutions
            </motion.span>
            <motion.h1 variants={heroItem}>
              One voice pipeline,{" "}
              <em>configured for your front line</em>.
            </motion.h1>
            <motion.p className="solutions-hero__sub" variants={heroItem}>
              Real-time voice AI that slots into the conversations your business
              already has — support, sales, recruiting, ops, and beyond.
            </motion.p>
            <motion.div className="solutions-hero__cta" variants={heroItem}>
              <MagneticButton>
                <Link to="/console" className="btn btn-primary">
                  Try it live
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M13 6l6 6-6 6" />
                  </svg>
                </Link>
              </MagneticButton>
              <MagneticButton strength={10}>
                <Link to="/walkthrough" className="btn btn-ghost">
                  See the walkthrough
                </Link>
              </MagneticButton>
            </motion.div>
          </motion.div>
        </section>

        {/* ===== USE CASES ===== */}
        <section className="use-cases section">
          <div className="wrap">
            <div className="section__head reveal">
              <span className="eyebrow">Use cases</span>
              <h2>Where Git Voice AI Agent fits in.</h2>
              <p>Six scenarios where a real-time voice agent already makes sense today.</p>
            </div>
            <motion.div
              className="use-cases__grid"
              variants={gridStagger}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-80px" }}
            >
              {USE_CASES.map((uc, i) => (
                <TiltCard key={uc.title} index={i}>
                  <div className="use-case__icon">{uc.icon}</div>
                  <h3>{uc.title}</h3>
                  <p>{uc.body}</p>
                  <span className="use-case__tag">{uc.tag}</span>
                </TiltCard>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ===== PIPELINE ===== */}
        <section className="pipeline-section" ref={pipelineRef}>
          <div className="wrap">
            <div className="section__head reveal">
              <span className="eyebrow eyebrow--teal">The stack</span>
              <h2>Under the hood.</h2>
              <p>Four layers, each inspectable and replaceable — no black boxes.</p>
            </div>
            <motion.div
              className="pipeline-steps"
              variants={gridStagger}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-60px" }}
            >
              <motion.div className="pipeline-line" style={{ scaleX: lineScale }} aria-hidden="true" />
              {PIPELINE.map((step) => (
                <motion.div
                  key={step.num}
                  className="pipeline-step"
                  variants={gridItem}
                  whileHover={{ y: -6, transition: { duration: 0.3, ease: [0.19, 1, 0.22, 1] } }}
                >
                  <div className="pipeline-step__num">{step.num}</div>
                  <h3>{step.title}</h3>
                  <p>{step.body}</p>
                  <span className="pipeline-step__badge">{step.badge}</span>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ===== CTA ===== */}
        <section className="solutions-cta">
          <div className="wrap">
            <motion.div
              className="solutions-cta__card reveal"
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.6, ease: [0.19, 1, 0.22, 1] }}
            >
              <div className="solutions-cta__orb" aria-hidden="true" />
              <div className="solutions-cta__particles" aria-hidden="true">
                <ParticleField count={26} color="255, 90, 54" />
              </div>
              <h2>Ready to hear it for yourself?</h2>
              <p>
                One button, no sign-up. The console is live — press connect
                and you're talking to the agent in seconds.
              </p>
              <div className="solutions-cta__btns">
                <MagneticButton>
                  <Link to="/console" className="btn btn-primary">
                    Launch the console
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M5 12h14M13 6l6 6-6 6" />
                    </svg>
                  </Link>
                </MagneticButton>
                <MagneticButton strength={10}>
                  <Link to="/walkthrough" className="btn btn-ghost">
                    Watch the walkthrough
                  </Link>
                </MagneticButton>
              </div>
            </motion.div>
          </div>
        </section>
      </main>
      <Footer variant="default" />
    </>
  );
}