import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import Nav from "../components/Nav";
import Footer from "../components/Footer";

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

  return (
    <>
      <Nav variant="default" />
      <main>
        {/* ===== HERO ===== */}
        <section className="hero" id="hero">
          <div className="hero__glow" aria-hidden="true" />
          <div className="hero__grid" aria-hidden="true" />
          <div className="wrap hero__inner">
            <span className="eyebrow">Real-time voice agent</span>
            <h1>
              Talk to it. <em>It talks back</em> — instantly.
            </h1>
            <p className="hero__sub">
              Unmute is a live spoken AI agent. No typing, no turn-taking, no
              waiting for a reply to finish generating. Just press connect and
              have a real conversation.
            </p>
            <div className="hero__cta">
              <Link to="/console" className="btn btn-primary">
                Try it live
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                  <line x1="12" y1="18" x2="12" y2="22" />
                </svg>
              </Link>
              <a href="#how-it-works" className="btn-text">
                See how it works
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </a>
            </div>
          </div>

          {/* Signal waveform */}
          <div className="signal wrap" aria-hidden="true">
            <svg viewBox="0 0 1180 132" preserveAspectRatio="none">
              <defs>
                <linearGradient id="signalGradient" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#ff5a36" stopOpacity="0" />
                  <stop offset="15%" stopColor="#ff5a36" />
                  <stop offset="50%" stopColor="#ffb08a" />
                  <stop offset="85%" stopColor="#7c8cff" />
                  <stop offset="100%" stopColor="#7c8cff" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path
                className="signal__path signal__path--ghost"
                d="M0,66 C 40,20 80,20 120,66 C 160,112 200,112 240,66 C 280,10 320,10 360,66 C 400,120 440,120 480,66 C 520,15 560,15 600,66 C 640,116 680,116 720,66 C 760,18 800,18 840,66 C 880,114 920,114 960,66 C 1000,20 1040,20 1080,66 C 1110,96 1140,96 1180,66"
              />
              <path
                className="signal__path"
                d="M0,66 C 40,20 80,20 120,66 C 160,112 200,112 240,66 C 280,10 320,10 360,66 C 400,120 440,120 480,66 C 520,15 560,15 600,66 C 640,116 680,116 720,66 C 760,18 800,18 840,66 C 880,114 920,114 960,66 C 1000,20 1040,20 1080,66 C 1110,96 1140,96 1180,66"
              />
            </svg>
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

        {/* ===== FEATURES ===== */}
        <section className="section" id="features">
          <div className="wrap">
            <div className="section__head reveal">
              <span className="eyebrow">Why Unmute</span>
              <h2>Built for real conversation, not chat.</h2>
              <p>Four things that make a voice agent actually feel like talking to someone.</p>
            </div>
            <div className="features__grid reveal">
              <article className="feature">
                <div className="feature__icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M8 4l-6 8 6 8M16 4l6 8-6 8" />
                  </svg>
                </div>
                <h3>Real-time, full duplex</h3>
                <p>Talk and listen at the same time, like an actual phone call — never turn-based, never a queue.</p>
              </article>
              <article className="feature">
                <div className="feature__icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 6h16M4 12h10M4 18h13" />
                  </svg>
                </div>
                <h3>Live transcript</h3>
                <p>See what's being said as it's said — both sides of the conversation, captioned in real time.</p>
              </article>
              <article className="feature">
                <div className="feature__icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z" />
                  </svg>
                </div>
                <h3>Low-latency pipeline</h3>
                <p>The reply starts streaming back almost immediately — no long pause while a response gets generated.</p>
              </article>
              <article className="feature">
                <div className="feature__icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="9" />
                    <path d="M3.6 9h16.8M3.6 15h16.8M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
                  </svg>
                </div>
                <h3>Open architecture</h3>
                <p>Built on WebRTC and LiveKit — self-hostable, inspectable infrastructure, not a closed black box.</p>
              </article>
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
                <svg className="how__icon" viewBox="0 0 24 24" fill="none" stroke="#ff5a36" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                  <line x1="12" y1="18" x2="12" y2="22" />
                </svg>
                <div className="how__num">01</div>
                <h3>You speak</h3>
                <p>The moment you connect, mic audio streams live over WebRTC — no recording, no upload step.</p>
              </div>
              <div className="how__step">
                <svg className="how__icon" viewBox="0 0 24 24" fill="none" stroke="#7c8cff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
      </main>
      <Footer variant="default" />
    </>
  );
}
