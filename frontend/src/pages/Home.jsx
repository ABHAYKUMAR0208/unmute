import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AnimatePresence, motion, useMotionValue, useScroll, useSpring, useTransform } from "framer-motion";
import Nav from "../components/Nav";
import Footer from "../components/Footer";
import ParticleField from "../components/ParticleField";
import StatsBand from "../components/StatsBand";
import "./Home.css";

/* ============================================================
   DATA — use cases, testimonials, FAQ
   ============================================================ */
const USE_CASE_TABS = [
  {
    id: "inbound",
    label: "Inbound calls",
    cases: [
      {
        icon: "login",
        image: "/images/checkin.jpg",
        title: "Front Desk & Check-in",
        copy: "Verifies bookings, confirms ID details, and hands over room numbers and Wi-Fi codes.",
      },
      {
        icon: "room_service",
        image: "/images/room_service.jpg",
        title: "Room Service Orders",
        copy: "Takes orders straight from the in-room menu and confirms a realistic delivery time.",
      },
      {
        icon: "cleaning_services",
        image: "/images/housekeeping.jpg",
        title: "Housekeeping Requests",
        copy: "Logs extra towels, turn-down service, or a fresh cleaning — routed to staff instantly.",
      },
      {
        icon: "spa",
        image: "/images/spa.jpg",
        title: "Spa & Wellness Booking",
        copy: "Checks therapist availability, holds a slot, and answers treatment and pricing questions.",
      },
      {
        icon: "build",
        image: "/images/maintenance.jpg",
        title: "Maintenance Reports",
        copy: "Takes down what's broken, flags urgency, and creates a ticket before the guest hangs up.",
      },
      {
        icon: "restaurant",
        image: "/images/restaurant.jpg",
        title: "Dining Reservations",
        copy: "Holds a table, confirms party size, and notes allergies or dietary requirements.",
      },
    ],
  },
  {
    id: "outbound",
    label: "Outbound calls",
    cases: [
      {
        icon: "bedtime",
        image: "/images/wakeup.jpg",
        title: "Wake-up Calls",
        copy: "Rings every requested room on time with a warm, natural voice — never a robotic beep.",
      },
      {
        icon: "event_available",
        image: "/images/restaurant.jpg",
        title: "Reservation Confirmations",
        copy: "Calls ahead to confirm dinner bookings and flags any last-minute changes to staff.",
      },
      {
        icon: "local_taxi",
        image: "/images/taxi.jpg",
        title: "Airport Transfers",
        copy: "Arranges pickup windows with the front desk and relays driver details to the guest.",
      },
      {
        icon: "schedule",
        image: "/images/checkout.jpg",
        title: "Checkout Reminders",
        copy: "A courteous nudge an hour before checkout, with the option to extend the stay.",
      },
      {
        icon: "dry_cleaning",
        image: "/images/laundry.jpg",
        title: "Laundry Ready Alerts",
        copy: "Lets guests know their order is back and offers to have it sent up right away.",
      },
      {
        icon: "translate",
        image: "/images/language.jpg",
        title: "Language Callbacks",
        copy: "Follows up in the guest's own language when a request needs a human touch.",
      },
    ],
  },
];

const FEATURES = [
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3v3M12 18v3M4.2 4.2l2.1 2.1M17.7 17.7l2.1 2.1M3 12h3M18 12h3M4.2 19.8l2.1-2.1M17.7 6.3l2.1-2.1" />
        <circle cx="12" cy="12" r="4" />
      </svg>
    ),
    title: "Continuous Learning",
    copy: "Every call sharpens the model. Mis-steps become training data — accuracy compounds without lifting a finger.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" />
      </svg>
    ),
    title: "Contextual Understanding",
    copy: "Tracks intent across the whole call — interruptions, corrections, mid-sentence reroutes — without losing the thread.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="9" />
        <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
      </svg>
    ),
    title: "Speaks 40+ Languages",
    copy: "Code-switches naturally, keeps proper nouns intact, and adapts its cadence to the caller's own.",
  },
  {
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M13 2 3 14h7l-1 8 10-12h-7l1-8z" />
      </svg>
    ),
    title: "Intelligent Responses",
    copy: "Sub-300ms turn-taking with natural prosody. It pauses when humans pause, and never talks over a guest.",
  },
];

const TESTIMONIALS = [
  {
    stat: "Missed calls -92%",
    quote: "We used to lose late-night bookings to voicemail. Now the very first ring gets a real conversation, not a beep.",
    name: "Maya Chen",
    role: "Head of Guest Services, Lumen Hotels",
    avatar: "https://i.pravatar.cc/96?img=47",
  },
  {
    stat: "Response time 40s",
    quote: "Housekeeping requests used to sit in an inbox for an hour. The agent routes them to staff before the guest hangs up.",
    name: "David Okonkwo",
    role: "Operations Director, Northfield Resorts",
    avatar: "https://i.pravatar.cc/96?img=12",
  },
  {
    stat: "Guest CSAT 4.8 / 5",
    quote: "Guests genuinely don't realize they're talking to software until we tell them — and most say it's faster than the old desk phone.",
    name: "Priya Raman",
    role: "General Manager, Parallel Hotel Co.",
    avatar: "https://i.pravatar.cc/96?img=32",
  },
];

const FAQS = [
  {
    q: "How fast can we go live?",
    a: "Most properties launch within two weeks. Connect a phone number, point us at your PMS and menu data, and the agent handles hundreds of test calls before it ever takes a live one.",
  },
  {
    q: "Will guests know they're talking to AI?",
    a: "It introduces itself honestly at the start of every call. Most guests stop noticing within the first exchange because the pacing and turn-taking feel like a normal phone conversation.",
  },
  {
    q: "What happens when it doesn't know the answer?",
    a: "It says so, then transfers the call — or the request — to the right person on shift, along with a summary of what the guest already said, so nothing has to be repeated.",
  },
  {
    q: "How does pricing work?",
    a: "A flat monthly fee per property plus usage past your included minutes. No per-seat licensing, and no charge for the staff members who receive the routed requests.",
  },
  {
    q: "Is it PCI and data compliant?",
    a: "Call audio and transcripts are encrypted in transit and at rest, and payment details are never spoken back or stored by the agent. We can share our compliance documentation on request.",
  },
  {
    q: "Can it integrate with our PMS and phone system?",
    a: "Yes — it connects to common property management and phone systems, and forwards structured requests (orders, tickets, bookings) directly into the tools your staff already use.",
  },
];

const TRUST_NAMES = ["Lumen Hotels", "Northfield Resorts", "Parallel Hotel Co.", "AllHands Hospitality", "Ovate Collection", "Helix Suites"];

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
      { threshold: 0.15 }
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
}

export default function Home() {
  useReveal();
  const cursorRef = useRef(null);
  const heroRef = useRef(null);
  const sceneRef = useRef(null);
  const [activeTab, setActiveTab] = useState("inbound");
  const [openFaq, setOpenFaq] = useState(0);
  const activeCases = USE_CASE_TABS.find((t) => t.id === activeTab).cases;

  // Scroll-linked parallax — the ambient blobs drift slower than the
  // page as you scroll, giving the hero a sense of depth.
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const ambient1Y = useTransform(scrollYProgress, [0, 1], [0, 120]);
  const ambient2Y = useTransform(scrollYProgress, [0, 1], [0, -90]);
  const heroContentY = useTransform(scrollYProgress, [0, 1], [0, 60]);
  const heroContentOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0.35]);

  // 3D tilt — the scene reacts to the cursor position within hero-right,
  // and the two floating cards drift a touch more than the center card
  // for a subtle layered-depth (parallax) feel.
  const tiltX = useMotionValue(0);
  const tiltY = useMotionValue(0);
  const springTiltX = useSpring(tiltX, { stiffness: 120, damping: 16, mass: 0.4 });
  const springTiltY = useSpring(tiltY, { stiffness: 120, damping: 16, mass: 0.4 });
  const sceneRotateX = useTransform(springTiltY, [-0.5, 0.5], [10, -10]);
  const sceneRotateY = useTransform(springTiltX, [-0.5, 0.5], [-10, 10]);
  const card1X = useTransform(springTiltX, [-0.5, 0.5], [-18, 18]);
  const card1Y = useTransform(springTiltY, [-0.5, 0.5], [-14, 14]);
  const card2X = useTransform(springTiltX, [-0.5, 0.5], [14, -14]);
  const card2Y = useTransform(springTiltY, [-0.5, 0.5], [12, -12]);

  function handleSceneMouseMove(e) {
    const bounds = e.currentTarget.getBoundingClientRect();
    tiltX.set((e.clientX - bounds.left) / bounds.width - 0.5);
    tiltY.set((e.clientY - bounds.top) / bounds.height - 0.5);
  }

  function handleSceneMouseLeave() {
    tiltX.set(0);
    tiltY.set(0);
  }

  useEffect(() => {
    let mouseX = 0;
    let mouseY = 0;
    let glowX = 0;
    let glowY = 0;
    let animationFrameId;

    const handleMouseMove = (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      if (cursorRef.current && cursorRef.current.style.opacity === "0") {
        cursorRef.current.style.opacity = "1";
      }
    };

    const animateGlow = () => {
      glowX += (mouseX - glowX) * 0.1;
      glowY += (mouseY - glowY) * 0.1;
      if (cursorRef.current) {
        cursorRef.current.style.left = `${glowX}px`;
        cursorRef.current.style.top = `${glowY}px`;
      }
      animationFrameId = requestAnimationFrame(animateGlow);
    };

    document.addEventListener("mousemove", handleMouseMove);
    animationFrameId = requestAnimationFrame(animateGlow);

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <>
      <Nav variant="default" />
      <main>
        {/* Glow cursor */}
        <div ref={cursorRef} className="hero-glow-cursor" style={{ opacity: "0" }}></div>

        {/* ===== HERO ===== */}
        <section className="hero-section" ref={heroRef}>
          <div className="hero-ambient-bg">
            <motion.div className="hero-ambient-1" style={{ y: ambient1Y }}></motion.div>
            <motion.div className="hero-ambient-2" style={{ y: ambient2Y }}></motion.div>
            <ParticleField />
          </div>

          <motion.div className="hero-content" style={{ y: heroContentY, opacity: heroContentOpacity }}>
            <div className="hero-left">
              <div className="hero-badge">
                <span className="hero-badge-dot"></span>
                <span className="hero-badge-text">Git Voice AI Agent Engine v2.0</span>
              </div>
              <h1 className="hero-h1 animate-reveal">
                The AI Receptionist<br />
                <span className="hero-text-gradient">That Never Sleeps.</span>
              </h1>
              <p className="hero-subtitle animate-reveal" style={{ animationDelay: '100ms' }}>
                Handle guest requests instantly using natural voice conversations. The assistant can answer questions, book services, transfer requests, and improve hotel operations 24/7.
              </p>
              <div className="hero-actions animate-reveal" style={{ animationDelay: '200ms' }}>
                <Link to="/console" className="hero-btn-cta">
                  <span className="hero-btn-cta-hover"></span>
                  <span className="material-symbols-outlined" style={{ fontSize: "18px" }}>mic</span>
                  START DEMO
                </Link>
                <button className="hero-btn-secondary">
                  BOOK A MEETING
                </button>
              </div>
              <div className="hero-social-proof animate-reveal" style={{ animationDelay: '300ms' }}>
                <div className="hero-avatars">
                  <div className="hero-avatar">
                    <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuCNRl8ltIgIKct2ryKSYjEl73-8wsumHQ-xmM5LNXO9s9UtrROtYuuHG62-AKZT3mZ2NCL7iTjU_7pntOxIvJzWLD31zH3cgZlyfCzZFd1MnO_sWlcmALVa62eJLjmaK7kGxAKgmFrpsaD8ZXMrYDxkzY0hBPwBlX_V14DZffDBDS-QTlPcZ_9B5hILn8-GHOK0lgg160SIw2J_I7bwcO5p7SkTBfh14kEz0Jls1ElrMxQ4kjVeIkRFNg" alt="Avatar 1" />
                  </div>
                  <div className="hero-avatar">
                    <img src="https://lh3.googleusercontent.com/aida-public/AB6AXuBgBDBYeHT1qHE6LqhXqNRkrNDtwlhGiKSxylzjM9OaCBoapsHBjqS4xLCDPJJdWEAWPwnXO9pGFhWRr06yCI4SRSNEHOa93otORJCFvqjKQn9sbvbTl0ld4d608CVOGn8Fx7JgYprCaQPu1Unry-lnSeTzM2uso-g5M3GUuYkDkfb6IcEkR5HsGPn5drmkHiZXI6Ujw4EBN5yunKlEXCUhjPHPox02xZozfOKcNGgw8rRL5vOe2RGdYQ" alt="Avatar 2" />
                  </div>
                  <div className="hero-avatar hero-avatar-count">
                    +2k
                  </div>
                </div>
                <div className="hero-social-text">Trusted by leading hospitality brands worldwide.</div>
              </div>
            </div>
            
            <div className="hero-right" id="parallax-scene">
              <div className="hero-scene-center">
                <div className="hero-main-card">
                  <div className="hero-main-card-bg"></div>
                  <div className="hero-main-card-glow"></div>
                  <span className="material-symbols-outlined hero-main-card-icon">graphic_eq</span>
                </div>
              </div>

              <motion.div
                className="hero-card-0"
                initial={{ opacity: 0, y: -30, x: -20 }}
                animate={{ opacity: 1, y: 0, x: 0 }}
                transition={{ duration: 0.7, delay: 0.65, ease: [0.19, 1, 0.22, 1] }}
              >
                <motion.div
                  className="hero-parallax-card hero-mini-card"
                  animate={{ y: [0, -9, 0] }}
                  transition={{ duration: 6.5, repeat: Infinity, ease: "easeInOut", delay: 0.8 }}
                >
                  <div className="hero-mini-card-top">
                    <span className="hero-mini-card-label">Calls handled today</span>
                    <span className="hero-mini-card-badge">
                      <span className="material-symbols-outlined" style={{ fontSize: "12px" }}>trending_up</span>
                      +12%
                    </span>
                  </div>
                  <div className="hero-mini-card-value">128</div>
                  <svg className="hero-mini-card-chart" viewBox="0 0 120 34" preserveAspectRatio="none">
                    <polyline
                      points="0,28 14,24 28,26 42,16 56,19 70,10 84,14 98,6 112,9 120,3"
                      fill="none"
                      stroke="var(--hero-color-secondary)"
                      strokeWidth="2.4"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </motion.div>
              </motion.div>

              <motion.div
                className="hero-card-1"
                initial={{ opacity: 0, y: 36 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.35, ease: [0.19, 1, 0.22, 1] }}
              >
                <motion.div
                  className="hero-parallax-card"
                  animate={{ y: [0, -12, 0] }}
                  transition={{ duration: 6, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                >
                  <div className="hero-card-header">
                    <div className="hero-card-title-group">
                      <div className="hero-card-icon-wrap bg-sec">
                        <span className="material-symbols-outlined" style={{ color: "var(--hero-color-secondary)" }}>record_voice_over</span>
                      </div>
                      <div>
                        <div className="hero-card-title">Guest Request</div>
                        <div className="hero-card-subtitle">Room 304</div>
                      </div>
                    </div>
                    <span className="hero-card-status">ACTIVE</span>
                  </div>

                  <div className="hero-waveform-box">
                    <div className="hero-waveform-inner">
                      <div className="hero-wave-bar" style={{ animationDelay: "0.1s" }}></div>
                      <div className="hero-wave-bar" style={{ animationDelay: "0.2s" }}></div>
                      <div className="hero-wave-bar" style={{ animationDelay: "0.3s" }}></div>
                      <div className="hero-wave-bar" style={{ animationDelay: "0.4s" }}></div>
                      <div className="hero-wave-bar" style={{ animationDelay: "0.5s" }}></div>
                      <div className="hero-wave-bar" style={{ animationDelay: "0.6s" }}></div>
                      <div className="hero-wave-bar" style={{ animationDelay: "0.7s" }}></div>
                      <div className="hero-wave-bar" style={{ animationDelay: "0.8s" }}></div>
                      <div className="hero-wave-bar" style={{ animationDelay: "0.9s" }}></div>
                    </div>
                  </div>
                  <div className="hero-quote">"Could we get extra towels and a late checkout?"</div>
                </motion.div>
              </motion.div>

              <motion.div
                className="hero-card-2"
                initial={{ opacity: 0, y: 36 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.5, ease: [0.19, 1, 0.22, 1] }}
              >
                <motion.div
                  className="hero-parallax-card"
                  animate={{ y: [0, 12, 0] }}
                  transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1.2 }}
                >
                  <div className="hero-card-header" style={{ marginBottom: "24px" }}>
                    <div className="hero-card-icon-wrap bg-tert" style={{ marginRight: "12px" }}>
                      <span className="material-symbols-outlined" style={{ color: "var(--hero-color-tertiary-container)" }}>bolt</span>
                    </div>
                    <div className="hero-card-title">Auto-Resolved</div>
                  </div>
                  <div className="hero-check-list">
                    <div className="hero-check-item">
                      <span style={{ color: "var(--hero-color-on-surface-variant)" }}>Towels dispatched</span>
                      <span className="material-symbols-outlined" style={{ color: "var(--hero-color-secondary)", fontSize: "14px" }}>check_circle</span>
                    </div>
                    <div className="hero-progress-bg">
                      <div className="hero-progress-fill"></div>
                    </div>
                    <div className="hero-check-item">
                      <span style={{ color: "var(--hero-color-on-surface-variant)" }}>Checkout extended (2PM)</span>
                      <span className="material-symbols-outlined" style={{ color: "var(--hero-color-secondary)", fontSize: "14px" }}>check_circle</span>
                    </div>
                    <div className="hero-progress-bg">
                      <div className="hero-progress-fill"></div>
                    </div>
                  </div>
                </motion.div>
              </motion.div>
            </div>
          </motion.div>
        </section>

        {/* ===== TRUST STRIP ===== */}
        <section className="trust-strip reveal" aria-label="Trusted by">
          <div className="wrap trust-strip__inner">
            <span className="trust-strip__label">Trusted by teams answering 40M+ calls a month</span>
            <div className="trust-strip__marquee">
              <div className="trust-strip__track">
                {[...TRUST_NAMES, ...TRUST_NAMES].map((name, i) => (
                  <span className="trust-strip__name" key={`${name}-${i}`}>{name}</span>
                ))}
              </div>
            </div>
          </div>
        </section>

        <StatsBand />

        {/* ===== USE CASES ===== */}
        <section className="section usecases" id="use-cases">
          <div className="wrap">
            <div className="section__head center reveal">
              <span className="eyebrow eyebrow--violet" style={{ marginLeft: "auto", marginRight: "auto" }}>
                Use cases
              </span>
              <h2>One voice agent.<br />Every kind of guest request.</h2>
              <p style={{ marginLeft: "auto", marginRight: "auto" }}>
                Train it on your scripts, your tone, your menus. Drop it in front of any room phone
                or the front-desk line — inbound or outbound.
              </p>
            </div>

            <div className="usecases__tabs reveal" role="tablist" aria-label="Call direction">
              {USE_CASE_TABS.map((tab) => (
                <button
                  key={tab.id}
                  role="tab"
                  aria-selected={activeTab === tab.id}
                  className={`usecases__tab${activeTab === tab.id ? " is-active" : ""}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {activeTab === tab.id && (
                    <motion.span
                      layoutId="usecases-tab-pill"
                      className="usecases__tab-pill"
                      transition={{ type: "spring", stiffness: 420, damping: 34 }}
                    />
                  )}
                  <span className="usecases__tab-label">{tab.label}</span>
                </button>
              ))}
            </div>

            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                className="usecases__grid"
                initial="hidden"
                animate="show"
                exit="hidden"
                variants={{
                  hidden: {},
                  show: { transition: { staggerChildren: 0.06 } },
                }}
              >
                {activeCases.map((item) => (
                  <motion.div
                    className="usecase-card"
                    key={item.title}
                    variants={{
                      hidden: { opacity: 0, y: 18, scale: 0.98 },
                      show: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.45, ease: [0.19, 1, 0.22, 1] } },
                    }}
                    whileHover={{ y: -6 }}
                  >
                    <div className="usecase-card__image">
                      <img src={item.image} alt="" loading="lazy" />
                      <span className="usecase-card__icon">
                        <span className="material-symbols-outlined">{item.icon}</span>
                      </span>
                    </div>
                    <h3>{item.title}</h3>
                    <p>{item.copy}</p>
                  </motion.div>
                ))}
              </motion.div>
            </AnimatePresence>
          </div>
        </section>

        {/* ===== TEASER CARD ===== */}
        <section className="teaser">
          <div className="wrap">
            <div className="teaser__card reveal">
              <div className="teaser__copy">
                <span className="eyebrow eyebrow--violet">The console</span>
                <h2>This isn't a demo video.</h2>
                <p>
                  Press connect and start talking — for real. The console opens
                  a live microphone connection and streams a spoken reply back
                  in real time.
                </p>
                <Link to="/console" className="btn btn-ghost">
                  Launch the console
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12h14M13 6l6 6-6 6" />
                  </svg>
                </Link>
              </div>
              <div className="mock" aria-hidden="true">
                <span className="mock__status">
                  <i />
                  Live · 00:24
                </span>
                <div className="mock__ring">
                  <svg viewBox="0 0 24 24" fill="none" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2">
                    <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                    <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                    <line x1="12" y1="18" x2="12" y2="22" />
                  </svg>
                </div>
                <div className="mock__bars">
                  <span /><span /><span /><span /><span /><span /><span />
                </div>
                <p className="caption">Press connect and start talking</p>
              </div>
            </div>
          </div>
        </section>

        {/* ===== HOW IT WORKS ===== */}
        <section className="section how" id="how-it-works">
          <div className="wrap">
            <div className="section__head center reveal">
              <span className="eyebrow" style={{ marginLeft: "auto", marginRight: "auto" }}>
                The pipeline
              </span>
              <h2>From your voice to its voice, in three steps.</h2>
            </div>
            <div className="how__strip reveal">
              <div className="how__step">
                <svg className="how__icon" viewBox="0 0 24 24" fill="none" stroke="#6337de" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                  <line x1="12" y1="18" x2="12" y2="22" />
                </svg>
                <div className="how__num">01</div>
                <h3>You speak</h3>
                <p>The moment you connect, mic audio streams live over WebRTC — no recording, no upload step.</p>
              </div>
              <div className="how__step">
                <svg className="how__icon" viewBox="0 0 24 24" fill="none" stroke="#000000" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9.5 2A5.5 5.5 0 0 0 4 7.5c0 1.4.5 2.6 1.4 3.6L4 15h4.9c.7.3 1.4.5 2.1.5A5.5 5.5 0 0 0 9.5 2z" />
                  <path d="M15 12a4 4 0 1 0 0-8" />
                  <circle cx="18.5" cy="17.5" r="3.5" />
                </svg>
                <div className="how__num">02</div>
                <h3>The agent listens &amp; thinks</h3>
                <p>Speech is transcribed and answered as it arrives — the model starts forming a reply before you finish.</p>
              </div>
              <div className="how__step">
                <svg className="how__icon" viewBox="0 0 24 24" fill="none" stroke="#2fe6b8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M11 5L6 9H2v6h4l5 4V5z" />
                  <path d="M15.5 8.5a5 5 0 0 1 0 7M19 5.5a9 9 0 0 1 0 13" />
                </svg>
                <div className="how__num">03</div>
                <h3>It replies out loud</h3>
                <p>The response streams back as audio and plays automatically — no play button, no waiting for text.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ===== FEATURES ===== */}
        <section className="section" id="features">
          <div className="wrap">
            <div className="section__head reveal" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", gap: 32, maxWidth: "none" }}>
              <div>
                <span className="eyebrow">Platform</span>
                <h2>Built to sound like<br />your best agent.</h2>
              </div>
              <p style={{ maxWidth: 360, marginTop: 0 }}>
                Four pieces work together so callers never realize they're talking to software —
                or notice when they don't have to repeat themselves.
              </p>
            </div>
            <div className="features__grid reveal">
              {FEATURES.map((f) => (
                <div className="feature" key={f.title}>
                  <div className="feature__icon">{f.icon}</div>
                  <h3>{f.title}</h3>
                  <p>{f.copy}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ===== TESTIMONIALS ===== */}
        <section className="section testimonials" id="customers">
          <div className="wrap">
            <div className="section__head center reveal">
              <span className="eyebrow eyebrow--teal" style={{ marginLeft: "auto", marginRight: "auto" }}>
                Customers
              </span>
              <h2>Teams that picked up the call.</h2>
            </div>
            <div className="testimonials__grid">
              {TESTIMONIALS.map((t, i) => (
                <motion.div
                  className="testimonial-card reveal"
                  key={t.name}
                  initial={{ opacity: 0, y: 26 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: "-60px" }}
                  transition={{ duration: 0.6, delay: i * 0.1, ease: [0.19, 1, 0.22, 1] }}
                >
                  <div className="testimonial-card__stat">{t.stat}</div>
                  <p className="testimonial-card__quote">&ldquo;{t.quote}&rdquo;</p>
                  <div className="testimonial-card__person">
                    <img src={t.avatar} alt="" />
                    <div>
                      <div className="testimonial-card__name">{t.name}</div>
                      <div className="testimonial-card__role">{t.role}</div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* ===== FAQ ===== */}
        <section className="section faq" id="faq">
          <div className="wrap">
            <div className="section__head center reveal">
              <span className="eyebrow eyebrow--amber" style={{ marginLeft: "auto", marginRight: "auto" }}>
                FAQ
              </span>
              <h2>Questions, answered.</h2>
            </div>
            <div className="faq__list reveal">
              {FAQS.map((item, i) => {
                const isOpen = openFaq === i;
                return (
                  <div className={`faq-item${isOpen ? " is-open" : ""}`} key={item.q}>
                    <button
                      className="faq-item__trigger"
                      aria-expanded={isOpen}
                      onClick={() => setOpenFaq(isOpen ? -1 : i)}
                    >
                      <span>{item.q}</span>
                      <motion.span
                        className="faq-item__chevron"
                        animate={{ rotate: isOpen ? 135 : 0 }}
                        transition={{ duration: 0.3, ease: [0.19, 1, 0.22, 1] }}
                      >
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="12" y1="5" x2="12" y2="19" />
                          <line x1="5" y1="12" x2="19" y2="12" />
                        </svg>
                      </motion.span>
                    </button>
                    <AnimatePresence initial={false}>
                      {isOpen && (
                        <motion.div
                          className="faq-item__body"
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          transition={{ duration: 0.32, ease: [0.19, 1, 0.22, 1] }}
                        >
                          <p>{item.a}</p>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                );
              })}
            </div>
          </div>
        </section>

        {/* ===== FINAL CTA ===== */}
        <section className="cta-band">
          <div className="wrap cta-band__inner reveal">
            <div className="cta-band__glow" aria-hidden="true"></div>
            <h2>Never send a guest to voicemail again.</h2>
            <p>100 free minutes. No credit card. Live in your account in 12 minutes.</p>
            <div className="cta-band__actions">
              <Link to="/console" className="hero-btn-cta">
                <span className="hero-btn-cta-hover"></span>
                <span className="material-symbols-outlined" style={{ fontSize: "18px" }}>mic</span>
                START DEMO
              </Link>
              <button className="cta-band__ghost">BOOK A MEETING</button>
            </div>
          </div>
        </section>
      </main>
      <Footer variant="default" />
    </>
  );
}