import { memo, useState } from "react";
import { Link, NavLink } from "react-router-dom";

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
      <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
      <line x1="12" y1="18" x2="12" y2="22" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
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

/**
 * Shared navigation header.
 * variant="default" — full site nav with links & "Try it live" CTA
 * variant="console" — brand + back-to-site only
 */
function Nav({ variant = "default" }) {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="nav">
      <div className="nav__inner">
        <Link to="/" className="brand" aria-label="Unmute home">
          <span className="brand__mark">
            <MicIcon />
          </span>
          Unmute
        </Link>

        {variant === "default" && (
          <nav className="nav__links" aria-label="Primary">
            <NavLink to="/" end className={({ isActive }) => isActive ? "is-active" : ""}>Home</NavLink>
            <NavLink to="/walkthrough" className={({ isActive }) => isActive ? "is-active" : ""}>Walkthrough</NavLink>
            <NavLink to="/solutions" className={({ isActive }) => isActive ? "is-active" : ""}>Solutions</NavLink>
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
            <MenuIcon />
          </button>
        </div>
      </div>

      <div className={`nav__mobile${mobileOpen ? " is-open" : ""}`} id="navMobile">
        {variant === "default" ? (
          <>
            <Link to="/" onClick={() => setMobileOpen(false)}>Home</Link>
            <Link to="/walkthrough" onClick={() => setMobileOpen(false)}>Walkthrough</Link>
            <Link to="/solutions" onClick={() => setMobileOpen(false)}>Solutions</Link>
            <Link to="/console" className="btn btn-primary btn-sm" onClick={() => setMobileOpen(false)}>
              Try it live
            </Link>
          </>
        ) : (
          <>
            <Link to="/" onClick={() => setMobileOpen(false)}>Home</Link>
            <Link to="/walkthrough" onClick={() => setMobileOpen(false)}>Walkthrough</Link>
            <Link to="/solutions" onClick={() => setMobileOpen(false)}>Solutions</Link>
          </>
        )}
      </div>
    </header>
  );
}

export default memo(Nav);
