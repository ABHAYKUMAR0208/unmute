import { motion } from "framer-motion";

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
      <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
      <line x1="12" y1="18" x2="12" y2="22" />
    </svg>
  );
}

function GlobeIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="2" y1="12" x2="22" y2="12" />
      <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
    </svg>
  );
}

function BoltIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <polyline points="12 6 12 12 16 14" />
    </svg>
  );
}

const FEATURES = [
  {
    icon: MicIcon,
    title: "Instant response",
    desc: "The agent picks up in real time, no hold music, no queue — guests talk and get answered.",
  },
  {
    icon: GlobeIcon,
    title: "Any language",
    desc: "Conversations flow naturally across languages, so every guest is understood on the first try.",
  },
  {
    icon: BoltIcon,
    title: "Smart escalation",
    desc: "Routine requests resolve automatically; anything that needs a human is handed off instantly.",
  },
  {
    icon: ClockIcon,
    title: "Always on",
    desc: "3 a.m. or 3 p.m., the front desk never sleeps — every call gets the same quality response.",
  },
];

function handleSpotlightMove(e) {
  const card = e.currentTarget;
  const bounds = card.getBoundingClientRect();
  card.style.setProperty("--spot-x", `${e.clientX - bounds.left}px`);
  card.style.setProperty("--spot-y", `${e.clientY - bounds.top}px`);
}

export default function HomeFeatures() {
  return (
    <section className="section features" id="features">
      <div className="wrap">
        <div className="section__head center reveal">
          <span className="eyebrow eyebrow--teal" style={{ marginLeft: "auto", marginRight: "auto" }}>
            Why it works
          </span>
          <h2>Built for how hotels actually run.</h2>
        </div>

        <motion.div
          className="features__grid features__grid--spotlight"
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-80px" }}
          variants={{
            hidden: {},
            show: { transition: { staggerChildren: 0.1 } },
          }}
        >
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <motion.div
              className="feature"
              key={title}
              onMouseMove={handleSpotlightMove}
              variants={{
                hidden: { opacity: 0, y: 24 },
                show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.19, 1, 0.22, 1] } },
              }}
              whileHover={{ y: -6 }}
            >
              <div className="feature__icon">
                <Icon />
              </div>
              <h3>{title}</h3>
              <p>{desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
