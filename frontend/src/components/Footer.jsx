import { memo } from "react";
import { Link } from "react-router-dom";

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
      <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
      <line x1="12" y1="18" x2="12" y2="22" />
    </svg>
  );
}

/** variant="default" — full links. variant="light" — compact, no nav links. */
function Footer({ variant = "default" }) {
  return (
    <footer className={`site-footer${variant === "light" ? " site-footer--light" : ""}`}>
      <div className="wrap site-footer__inner">
        <Link to="/" className="brand" aria-label="Unmute home">
          <span className="brand__mark">
            <MicIcon />
          </span>
          Unmute
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
