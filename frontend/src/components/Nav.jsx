import { memo, useRef, useState } from "react";
import { Link, NavLink } from "react-router-dom";
import { AnimatePresence, motion, useMotionValueEvent, useScroll } from "framer-motion";

function MenuIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

function CloseIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
      <line x1="6" y1="6" x2="18" y2="18" />
      <line x1="18" y1="6" x2="6" y2="18" />
    </svg>
  );
}

function ArrowRightIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

function BackIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 12H5M11 18l-6-6 6-6" />
    </svg>
  );
}

const NAV_LINKS = [
  { to: "/", label: "Home", end: true },
  { to: "/walkthrough", label: "Demo" },
  { to: "/features", label: "Features" },
  { to: "/solutions", label: "Solutions" },
  { to: "/about", label: "About" },
];

/**
 * Shared navigation header.
 * variant="default" — full site nav with links & "Try it live" CTA
 * variant="console" — brand + back-to-site only
 *
 * Scroll behaviour (framer-motion driven):
 *  - At the top of the page it floats as a rounded, inset pill.
 *  - Once scrolling starts it morphs into a flush, rectangular bar that
 *    reads as part of the page rather than a floating card.
 *  - Scrolling down hides it out of the way of content; scrolling back up
 *    (even slightly) brings it straight back.
 */
function Nav({ variant = "default" }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const [hidden, setHidden] = useState(false);
  const lastY = useRef(0);
  const { scrollY } = useScroll();

  useMotionValueEvent(scrollY, "change", (y) => {
    setScrolled(y > 28);

    const delta = y - lastY.current;
    if (y < 96) {
      setHidden(false);
    } else if (delta > 6) {
      setHidden(true);
      setMobileOpen(false);
    } else if (delta < -6) {
      setHidden(false);
    }
    lastY.current = y;
  });

  return (
    <motion.header
      className={`nav${scrolled ? " nav--scrolled" : ""}`}
      animate={{ y: hidden ? "-130%" : "0%" }}
      transition={{ type: "spring", stiffness: 380, damping: 38, mass: 0.7 }}
    >
      <motion.div
        className="nav__shell"
        animate={{
          borderRadius: scrolled ? 0 : 9999,
          marginTop: scrolled ? 0 : 20,
          boxShadow: scrolled
            ? "0 1px 0 rgba(0,0,0,0.06)"
            : "0 4px 24px rgba(0,0,0,0.06)",
        }}
        transition={{ type: "spring", stiffness: 300, damping: 32 }}
      >
        <div className="nav__inner">
          <Link to="/" className="brand" aria-label="Git SoftwareTech Voice AI Agent home">
            <span className="brand__mark">
              <img src="/images/logo-mark.png" alt="" />
            </span>
            Git Voice AI Agent
          </Link>

          {variant === "default" && (
            <nav className="nav__links" aria-label="Primary">
              {NAV_LINKS.map((link) => (
                <NavLink
                  key={link.to}
                  to={link.to}
                  end={link.end}
                  className={({ isActive }) => (isActive ? "is-active" : "")}
                >
                  {link.label}
                </NavLink>
              ))}
            </nav>
          )}

          <div className="nav__actions">
            {variant === "console" ? (
              <Link to="/" className="nav__back desktop-only">
                <BackIcon />
                Back to site
              </Link>
            ) : (
              <Link to="/console" className="btn btn-primary btn-sm desktop-only">
                Try it live
                <ArrowRightIcon />
              </Link>
            )}
            <button
              className="nav__toggle"
              aria-label={mobileOpen ? "Close menu" : "Open menu"}
              aria-expanded={mobileOpen}
              aria-controls="navMobile"
              onClick={() => setMobileOpen((v) => !v)}
            >
              {mobileOpen ? <CloseIcon /> : <MenuIcon />}
            </button>
          </div>
        </div>

        <AnimatePresence initial={false}>
          {mobileOpen && (
            <motion.div
              className="nav__mobile is-open"
              id="navMobile"
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.28, ease: [0.19, 1, 0.22, 1] }}
            >
              {NAV_LINKS.map((link) => (
                <Link key={link.to} to={link.to} onClick={() => setMobileOpen(false)}>
                  {link.label}
                </Link>
              ))}
              {variant === "default" && (
                <Link to="/console" className="btn btn-primary btn-sm" onClick={() => setMobileOpen(false)}>
                  Try it live
                </Link>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </motion.header>
  );
}

export default memo(Nav);