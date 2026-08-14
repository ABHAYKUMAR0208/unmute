import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import {
  AnimatePresence,
  motion,
  useInView,
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
import "./About.css";

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

/* ============================================================
   DATA — sourced from gitsoftwaretech.com/about (paraphrased,
   not copied) plus the site's own product/service listing. Stat
   values below are real facts (founding year, certifications,
   service-line count, HQ) rather than invented metrics.
   ============================================================ */
const STATS = [
  { value: "2012", label: "Founded" },
  { value: "2", label: "ISO certifications" },
  { value: "6", label: "Service pillars" },
  { value: "London, UK", label: "Global HQ" },
];

const PILLARS = [
  {
    title: "Data Engineering & Analytics",
    body: "Data warehousing, ETL pipelines, BI tooling, and real-time dashboards that turn raw data into decisions.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="8" ry="3" />
        <path d="M4 5v14c0 1.66 3.58 3 8 3s8-1.34 8-3V5" />
        <path d="M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3" />
      </svg>
    ),
  },
  {
    title: "AI, ML & GenAI",
    body: "Model development, deep learning for NLP and vision, and generative AI — including voice agents like this one.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3v3M12 18v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M3 12h3M18 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" />
        <circle cx="12" cy="12" r="4" />
      </svg>
    ),
  },
  {
    title: "Robotics & Intelligent Automation",
    body: "AI-powered industrial robotics, ROS-based solutions, and robotic process automation for physical and digital workflows.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="4" y="8" width="16" height="12" rx="4" />
        <path d="M12 8V4M9 4h6" />
        <circle cx="9" cy="14" r="1.2" fill="currentColor" stroke="none" />
        <circle cx="15" cy="14" r="1.2" fill="currentColor" stroke="none" />
      </svg>
    ),
  },
  {
    title: "Digital Transformation",
    body: "Business process reengineering, legacy system modernization, and cloud or SaaS adoption strategy for growing teams.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="22 7 13.5 15.5 8.5 10.5 2 17" />
        <polyline points="16 7 22 7 22 13" />
      </svg>
    ),
  },
  {
    title: "Enterprise Systems & Database",
    body: "ERP and CRM implementation, migration and upgrades (Oracle, SAP, Salesforce), identity management, and managed support.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="4" width="18" height="18" rx="2" />
        <line x1="3" y1="10" x2="21" y2="10" />
        <line x1="9" y1="10" x2="9" y2="22" />
      </svg>
    ),
  },
  {
    title: "Cloud Infrastructure & Services",
    body: "Cloud consulting across AWS, Azure, GCP, and OCI, plus security, cost optimization, MLOps, and DevOps implementation.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17.5 19H9a6 6 0 1 1 1.3-11.9A5.5 5.5 0 0 1 20 10.5a4 4 0 0 1-.5 8H17.5" />
      </svg>
    ),
  },
];

const PRODUCTS = [
  {
    name: "Git Voice AI Agent",
    tag: "This project",
    body: "The real-time voice agent you're using right now — a self-hostable WebRTC + LiveKit voice pipeline built as part of GIT's GenAI product line.",
    href: "/console",
    internal: true,
    current: true,
  },
  {
    name: "Fintegra",
    tag: "Product",
    body: "One of GIT Software Technologies' product-line platforms. See gitsoftwaretech.com for full details.",
    href: "https://gitsoftwaretech.com/fintegra/",
  },
  {
    name: "AstroJyotish",
    tag: "Product",
    body: "One of GIT Software Technologies' product-line platforms. See gitsoftwaretech.com for full details.",
    href: "https://gitsoftwaretech.com/astrojyotish/",
  },
];

/* ============================================================
   SMOOTH PAGE LOADER
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
          <path d="M20 6 9 17l-5-5" />
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
        Loading about…
      </motion.span>
    </motion.div>
  );
}

/* ============================================================
   TILT CARD — same cursor-tilt + spotlight recipe used on the
   Solutions page, kept local so this page has no cross-page
   dependency.
   ============================================================ */
function TiltCard({ index, className, children }) {
  const ref = useRef(null);
  const rotateX = useMotionValue(0);
  const rotateY = useMotionValue(0);
  const springRX = useSpring(rotateX, { stiffness: 210, damping: 20, mass: 0.5 });
  const springRY = useSpring(rotateY, { stiffness: 210, damping: 20, mass: 0.5 });
  const spotX = useMotionValue(50);
  const spotY = useMotionValue(50);
  const spotlight = useMotionTemplate`radial-gradient(220px circle at ${spotX}% ${spotY}%, rgba(99,55,222,0.14), transparent 70%)`;

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
      className={className}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      style={{ rotateX: springRX, rotateY: springRY, transformPerspective: 900 }}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, delay: (index % 3) * 0.08, ease: [0.19, 1, 0.22, 1] }}
    >
      <motion.div className="about-pillar__spotlight" style={{ background: spotlight }} aria-hidden="true" />
      {children}
    </motion.article>
  );
}

/* ============================================================
   STAT CARD — counts up if the value is numeric, otherwise just
   fades/rises into place (e.g. "London, UK").
   ============================================================ */
function useCountUp(target, inView, duration = 1.2) {
  const [value, setValue] = useState(0);
  const started = useRef(false);

  useEffect(() => {
    if (!inView || started.current || target === null) return;
    started.current = true;
    const start = performance.now();
    let raf;
    function tick(now) {
      const progress = Math.min((now - start) / (duration * 1000), 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(target * eased));
      if (progress < 1) raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, target, duration]);

  return value;
}

function StatCard({ stat, index }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });
  const numeric = /^\d+$/.test(stat.value) ? parseInt(stat.value, 10) : null;
  const counted = useCountUp(numeric, inView, 1 + index * 0.12);

  return (
    <motion.div
      ref={ref}
      className="about-stat-card"
      initial={{ opacity: 0, y: 22 }}
      animate={inView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.55, delay: index * 0.08, ease: [0.19, 1, 0.22, 1] }}
    >
      <div className="about-stat-card__value">{numeric !== null ? counted : stat.value}</div>
      <div className="about-stat-card__label">{stat.label}</div>
    </motion.div>
  );
}

const gridStagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};
const gridItem = {
  hidden: { opacity: 0, y: 24 },
  show: { opacity: 1, y: 0, transition: { duration: 0.55, ease: [0.19, 1, 0.22, 1] } },
};

function ArrowIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

export default function About() {
  useReveal();
  const [loading, setLoading] = useState(true);

  const heroRef = useRef(null);
  const { scrollYProgress: heroProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const glowY = useTransform(heroProgress, [0, 1], [0, 90]);
  const gridY = useTransform(heroProgress, [0, 1], [0, -40]);
  const orbAY = useTransform(heroProgress, [0, 1], [0, 60]);
  const orbBY = useTransform(heroProgress, [0, 1], [0, -50]);

  const heroReveal = {
    hidden: {},
    show: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } },
  };
  const heroItem = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.19, 1, 0.22, 1] } },
  };

  return (
    <>
      <AnimatePresence>
        {loading && <PageLoader onDone={() => setLoading(false)} />}
      </AnimatePresence>

      <Nav variant="default" />
      <main>
        {/* ===== HERO ===== */}
        <section className="hero" style={{ paddingBottom: "70px" }} ref={heroRef}>
          <motion.div className="hero__glow" style={{ y: glowY }} aria-hidden="true" />
          <motion.div className="hero__grid" style={{ y: gridY }} aria-hidden="true" />
          <motion.div className="about-hero__orb about-hero__orb--a" style={{ y: orbAY }} aria-hidden="true" />
          <motion.div className="about-hero__orb about-hero__orb--b" style={{ y: orbBY }} aria-hidden="true" />
          <div className="about-hero__particles" aria-hidden="true">
            <ParticleField count={34} color="99, 55, 222" />
          </div>

          <motion.div
            className="wrap hero__inner"
            variants={heroReveal}
            initial="hidden"
            animate={loading ? "hidden" : "show"}
          >
            <motion.span className="eyebrow eyebrow--violet" style={{ justifyContent: "center" }} variants={heroItem}>
              About GIT
            </motion.span>
            <motion.h1 variants={heroItem}>
              The team behind <em>Git Voice AI Agent</em>.
            </motion.h1>
            <motion.p className="hero__sub" variants={heroItem}>
              This voice agent is built by GIT Software Technologies — an IT
              services company shipping data, AI, and cloud systems for
              enterprise clients since 2012.
            </motion.p>
            <motion.div className="about-hero__cta" variants={heroItem}>
              <MagneticButton>
                <Link to="/console" className="btn btn-primary">
                  Try the voice agent
                  <ArrowIcon />
                </Link>
              </MagneticButton>
              <MagneticButton strength={10}>
                <a href="https://gitsoftwaretech.com" target="_blank" rel="noopener noreferrer" className="btn btn-ghost">
                  Visit gitsoftwaretech.com
                </a>
              </MagneticButton>
            </motion.div>
          </motion.div>
        </section>

        {/* ===== COMPANY INTRO + STATS ===== */}
        <section className="about-intro">
          <div className="wrap about-intro__grid">
            <div className="about-intro__copy reveal">
              <span className="eyebrow">Who we are</span>
              <h2 style={{ marginBottom: 18 }}>An IT services company.</h2>
              <p>
                GIT Software Technologies works across database management,
                analytics, and application development, drawing on deep
                industry experience to deliver IT solutions tailored to a
                client's needs, timeline, and budget.
              </p>
              <p>
                Its services span cloud consulting, technology advisory,
                implementation, integration, and managed services — backed by
                ISO 27001:2013 (information security) and ISO 9001:2015
                (quality management) certification.
              </p>
              <p>
                Git Voice AI Agent — the real-time voice product on this site —
                is one output of GIT's AI, ML & GenAI practice: a
                self-hostable WebRTC + LiveKit voice pipeline you can try
                right now from the console.
              </p>
            </div>
            <div className="about-stats">
              {STATS.map((stat, i) => (
                <StatCard key={stat.label} stat={stat} index={i} />
              ))}
            </div>
          </div>
        </section>

        {/* ===== SERVICE PILLARS ===== */}
        <section className="section" style={{ borderTop: "1px solid var(--border)" }}>
          <div className="wrap">
            <div className="section__head reveal">
              <span className="eyebrow eyebrow--teal">What GIT does</span>
              <h2>Six practices, one team.</h2>
              <p>The disciplines GIT Software Technologies works across for its enterprise clients.</p>
            </div>
            <motion.div
              className="about-pillars__grid"
              variants={gridStagger}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-80px" }}
            >
              {PILLARS.map((p, i) => (
                <TiltCard key={p.title} index={i} className="about-pillar">
                  <div className="about-pillar__icon">{p.icon}</div>
                  <h3>{p.title}</h3>
                  <p>{p.body}</p>
                </TiltCard>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ===== PRODUCTS ===== */}
        <section className="section" style={{ paddingTop: 0 }}>
          <div className="wrap">
            <div className="section__head reveal">
              <span className="eyebrow eyebrow--amber">Products</span>
              <h2>What GIT has shipped.</h2>
              <p>A few of the products built under the GIT Software Technologies umbrella.</p>
            </div>
            <motion.div
              className="about-products__grid"
              variants={gridStagger}
              initial="hidden"
              whileInView="show"
              viewport={{ once: true, margin: "-60px" }}
            >
              {PRODUCTS.map((prod) => (
                <motion.div
                  key={prod.name}
                  className={`about-product${prod.current ? " about-product--current" : ""}`}
                  variants={gridItem}
                  whileHover={{ y: -5, transition: { duration: 0.3, ease: [0.19, 1, 0.22, 1] } }}
                >
                  <span className="about-product__tag">{prod.tag}</span>
                  <h3>{prod.name}</h3>
                  <p>{prod.body}</p>
                  {prod.internal ? (
                    <Link to={prod.href} className="about-product__link">
                      Open console <ArrowIcon />
                    </Link>
                  ) : (
                    <a href={prod.href} target="_blank" rel="noopener noreferrer" className="about-product__link">
                      Learn more <ArrowIcon />
                    </a>
                  )}
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* ===== CERTIFICATIONS + CONTACT ===== */}
        <section className="about-certs-contact">
          <div className="wrap about-certs-contact__grid">
            <div className="reveal">
              <span className="eyebrow eyebrow--violet">Certifications</span>
              <h2 style={{ marginBottom: 24 }}>Held to a higher standard.</h2>
              <div className="about-cert">
                <div className="about-cert__badge">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M12 2 3 6v6c0 5 4 8.7 9 10 5-1.3 9-5 9-10V6l-9-4z" />
                    <path d="m9 12 2 2 4-4" />
                  </svg>
                </div>
                <div>
                  <h4>ISO 27001:2013</h4>
                  <p>Information security management, applied across GIT's client data and delivery processes.</p>
                </div>
              </div>
              <div className="about-cert">
                <div className="about-cert__badge">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="8" r="5" />
                    <path d="M8.5 13.5 6 22l6-3 6 3-2.5-8.5" />
                  </svg>
                </div>
                <div>
                  <h4>ISO 9001:2015</h4>
                  <p>Quality management standards covering how GIT plans, builds, and supports its solutions.</p>
                </div>
              </div>
            </div>

            <motion.div
              className="about-contact-card reveal"
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.55, ease: [0.19, 1, 0.22, 1] }}
            >
              <h3>Get in touch with GIT</h3>
              <div className="about-contact-row">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0z" />
                  <circle cx="12" cy="10" r="3" />
                </svg>
                <span>71-75 Shelton Street, Covent Garden, London, United Kingdom, WC2H 9JQ</span>
              </div>
              <div className="about-contact-row">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.3 1.8.6 2.7a2 2 0 0 1-.4 2.1L8 9.9a16 16 0 0 0 6 6l1.4-1.4a2 2 0 0 1 2.1-.4c.9.3 1.8.5 2.7.6a2 2 0 0 1 1.8 2.2z" />
                </svg>
                <a href="tel:+447442678628">+44 7442 678628</a>
              </div>
              <div className="about-contact-row">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2" />
                  <path d="m2 7 10 6 10-6" />
                </svg>
                <a href="mailto:sales@gitsoftwaretech.com">sales@gitsoftwaretech.com</a>
              </div>
            </motion.div>
          </div>
        </section>

        {/* ===== CTA ===== */}
        <section className="about-cta">
          <div className="wrap">
            <motion.div
              className="about-cta__card reveal"
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.6, ease: [0.19, 1, 0.22, 1] }}
            >
              <h2>Built by GIT. Ready when you are.</h2>
              <p>
                Press connect and talk to Git Voice AI Agent yourself — or head
                to GIT Software Technologies for the rest of what the team
                builds.
              </p>
              <div className="about-cta__btns">
                <MagneticButton>
                  <Link to="/console" className="btn btn-primary">
                    Launch the console
                    <ArrowIcon />
                  </Link>
                </MagneticButton>
                <MagneticButton strength={10}>
                  <a href="https://gitsoftwaretech.com" target="_blank" rel="noopener noreferrer" className="btn btn-ghost">
                    Visit GIT Software Technologies
                  </a>
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