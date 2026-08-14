import Nav from "../components/Nav";
import Footer from "../components/Footer";
import { Link } from "react-router-dom";

// Icons 
function RoomServiceIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 22h14M2 17h20M7 17a5 5 0 0 1 10 0M12 12V8M10 8h4" />
    </svg>
  );
}

function TaxiIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9L2 12.2V16c0 .6.4 1 1 1h2" />
      <circle cx="7" cy="17" r="2" />
      <circle cx="17" cy="17" r="2" />
    </svg>
  );
}

function LaundryIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="2" width="16" height="20" rx="2" ry="2" />
      <line x1="4" y1="7" x2="20" y2="7" />
      <circle cx="12" cy="14" r="3" />
      <path d="M12 14v.01" />
    </svg>
  );
}

function UserCheckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
      <circle cx="8.5" cy="7" r="4" />
      <polyline points="17 11 19 13 23 9" />
    </svg>
  );
}

function BroomIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2L12 10M8 10L16 10M10 10L10 22M14 10L14 22M6 22L18 22" />
      <circle cx="12" cy="5" r="3" />
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

function WrenchIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
    </svg>
  );
}

function RestaurantIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 2v7c0 1.1.9 2 2 2h4a2 2 0 0 0 2-2V2" />
      <path d="M7 2v20" />
      <path d="M21 15V2v0a5 5 0 0 0-5 5v6c0 1.1.9 2 2 2h3zm0 0v7" />
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

function SpaIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 7.477 2 13s4.477 10 10 10z" />
      <path d="M12 12L8 8" />
      <path d="M12 12l4-4" />
      <path d="M12 12v6" />
    </svg>
  );
}

function LogoutIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
      <polyline points="16 17 21 12 16 7" />
      <line x1="21" y1="12" x2="9" y2="12" />
    </svg>
  );
}

export default function Features() {
  return (
    <>
      <Nav />
      <main>
        {/* ===== HERO ===== */}
        <section className="hero">
          <div className="hero__glow" aria-hidden="true" />
          <div className="wrap hero__inner">
            <span className="eyebrow eyebrow--coral">Git Voice AI Agent Intelligence</span>
            <h1>
              Everything Your <em>Guests Need.</em>
            </h1>
            <p className="hero__sub" style={{ maxWidth: "600px", margin: "24px auto 0" }}>
              One intelligent voice assistant that handles every guest interaction seamlessly from check-in until checkout. No holds, no waiting.
            </p>
          </div>
        </section>

        {/* ===== BENTO GRID ===== */}
        <section className="bento-section">
          <div className="wrap">
            <div className="features-bento">
              {/* Room Service (Large) */}
              <div className="bento-card bento-card--large bento-card--image group">
                <img src="/images/room_service.jpg" alt="Room Service" className="bento-card__bg" />
                <div className="bento-card__overlay">
                  <div className="bento-card__head">
                    <div className="bento-icon">
                      <RoomServiceIcon />
                    </div>
                    <span className="bento-badge">2 MIN AVG</span>
                  </div>
                  <div className="bento-card__body">
                    <h3>Room Service</h3>
                    <p>Instant conversational ordering. "I'd like a club sandwich and a diet coke to room 402."</p>
                  </div>
                </div>
              </div>

              {/* Cab Booking */}
              <div className="bento-card bento-card--image group">
                <img src="/images/taxi.jpg" alt="Cab Booking" className="bento-card__bg" />
                <div className="bento-card__overlay">
                  <div className="bento-icon">
                    <TaxiIcon />
                  </div>
                  <div className="bento-card__body">
                    <h4>Cab Booking</h4>
                    <p>Scheduled or instant rides, coordinated seamlessly.</p>
                  </div>
                </div>
              </div>

              {/* Laundry */}
              <div className="bento-card bento-card--image group">
                <img src="/images/laundry.jpg" alt="Laundry" className="bento-card__bg" />
                <div className="bento-card__overlay">
                  <div className="bento-icon">
                    <LaundryIcon />
                  </div>
                  <div className="bento-card__body">
                    <h4>Laundry</h4>
                    <p>Automated pickup requests and status tracking.</p>
                  </div>
                </div>
              </div>

              {/* Check-in (Tall) */}
              <div className="bento-card bento-card--tall bento-card--image bento-card--gradient group">
                <img src="/images/checkin.jpg" alt="Check-in" className="bento-card__bg" />
                <div className="bento-card__overlay">
                  <div className="bento-icon bento-icon--primary">
                    <UserCheckIcon />
                  </div>
                  <div className="bento-card__body">
                    <h3>Check-in</h3>
                    <p>Bypass the front desk. Voice-guided identity verification and digital key issuance.</p>
                  </div>
                </div>
              </div>

              {/* Housekeeping */}
              <div className="bento-card bento-card--image group">
                <img src="/images/housekeeping.jpg" alt="Housekeeping" className="bento-card__bg" />
                <div className="bento-card__overlay">
                  <div className="bento-icon">
                    <BroomIcon />
                  </div>
                  <div className="bento-card__body">
                    <h4>Housekeeping</h4>
                    <p>Extra towels or full room makeup on command.</p>
                  </div>
                </div>
              </div>

              {/* Wake-up Calls */}
              <div className="bento-card bento-card--image group">
                <img src="/images/wakeup.jpg" alt="Wake-up Calls" className="bento-card__bg" />
                <div className="bento-card__overlay">
                  <div className="bento-card__head">
                    <div className="bento-icon bento-icon--secondary">
                      <ClockIcon />
                    </div>
                    <span className="bento-badge bento-badge--secondary">0% FAIL RATE</span>
                  </div>
                  <div className="bento-card__body">
                    <h4>Wake-up Calls</h4>
                    <p>Gentle, personalized morning greetings.</p>
                  </div>
                </div>
              </div>

              {/* Maintenance */}
              <div className="bento-card bento-card--image group">
                <img src="/images/maintenance.jpg" alt="Maintenance" className="bento-card__bg" />
                <div className="bento-card__overlay">
                  <div className="bento-icon bento-icon--error">
                    <WrenchIcon />
                  </div>
                  <div className="bento-card__body">
                    <h4>Maintenance</h4>
                    <p>Direct dispatch for immediate issue resolution.</p>
                  </div>
                </div>
              </div>

              {/* Restaurant Reservations (Wide) */}
              <div className="bento-card bento-card--wide bento-card--image group" style={{ flexDirection: "row", alignItems: "center" }}>
                <img src="/images/restaurant.jpg" alt="Restaurant Reservations" className="bento-card__bg" />
                <div className="bento-card__overlay" style={{ flexDirection: "row", alignItems: "center" }}>
                  <div className="bento-card__left">
                    <div className="bento-icon bento-icon--primary" style={{ marginBottom: "24px" }}>
                      <RestaurantIcon />
                    </div>
                    <h3>Restaurant Reservations</h3>
                    <p style={{ maxWidth: "340px" }}>Integrates with your POS to book tables, suggest wine pairings, and log dietary restrictions.</p>
                  </div>
                </div>
              </div>

              {/* Multi-language (Wide) */}
              <div className="bento-card bento-card--wide bento-card--image group">
                <img src="/images/language.jpg" alt="Native in 45+ Languages" className="bento-card__bg" />
                <div className="bento-card__overlay">
                  <div className="bento-card__head">
                    <div className="bento-icon">
                      <GlobeIcon />
                    </div>
                    <div className="lang-tags">
                      <span>EN</span><span>ES</span><span>FR</span><span className="faded">+42</span>
                    </div>
                  </div>
                  <div className="bento-card__body">
                    <h3>Native in 45+ Languages</h3>
                    <p style={{ maxWidth: "420px" }}>Real-time translation and native speaking capabilities ensure every guest feels entirely at home.</p>
                  </div>
                </div>
              </div>

              {/* Spa Services */}
              <div className="bento-card bento-card--image group">
                <img src="/images/spa.jpg" alt="Spa Services" className="bento-card__bg" />
                <div className="bento-card__overlay">
                  <div className="bento-icon">
                    <SpaIcon />
                  </div>
                  <div className="bento-card__body">
                    <h4>Spa Services</h4>
                    <p>Book treatments and view available schedules.</p>
                  </div>
                </div>
              </div>

              {/* Express Checkout */}
              <div className="bento-card bento-card--image group">
                <img src="/images/checkout.jpg" alt="Express Checkout" className="bento-card__bg" />
                <div className="bento-card__overlay">
                  <div className="bento-icon">
                    <LogoutIcon />
                  </div>
                  <div className="bento-card__body">
                    <h4>Express Checkout</h4>
                    <p>Review folios and process payments via voice.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
