import { memo } from "react";
import { Link } from "react-router-dom";

function GitVoiceIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="18" cy="18" r="3" />
      <circle cx="6" cy="6" r="3" />
      <path d="M13 6h3a2 2 0 0 1 2 2v7" />
      <line x1="6" y1="9" x2="6" y2="21" />
    </svg>
  );
}

/** variant="default" — full links. variant="light" — compact, no nav links. */
function Footer({ variant = "default" }) {
  return (
    <footer className={`site-footer${variant === "light" ? " site-footer--light" : ""}`}>
      <div className="wrap site-footer__inner">
        <Link to="/" className="brand" aria-label="Git Voice AI Agent home">
          <span className="brand__mark">
            <GitVoiceIcon />
          </span>
          Git Voice AI Agent
        </Link>

        {variant === "default" && (
          <ul className="site-footer__links">
            <li><Link to="/#features">Features</Link></li>
            <li><Link to="/walkthrough">Walkthrough</Link></li>
            <li><Link to="/solutions">Solutions</Link></li>
            <li><Link to="/console">Console</Link></li>
          </ul>
        )}

        <span className="site-footer__credit">Built with WebRTC &amp; LiveKit</span>
      </div>
    </footer>
  );
}

export default memo(Footer);
