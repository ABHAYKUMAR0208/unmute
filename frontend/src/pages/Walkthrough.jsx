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

/* Scroll-driven walkthrough logic — mirrors walkthrough.html JS exactly */
function useWalkthroughScroll() {
  useEffect(() => {
    const isReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches;
    const isMobile = window.matchMedia("(max-width: 860px)").matches;
    if (isReducedMotion || isMobile) return;

    const markers = document.querySelectorAll(".walkthrough__marker");
    const dots = document.querySelectorAll(".wt-progress__dot");
    const stepEls = document.querySelectorAll(".wt-step");
    const fill = document.getElementById("wtFill");
    const stage = document.getElementById("wtStage");
    const callBtn = document.getElementById("wtCallBtn");
    const waveformEl = document.getElementById("wtWaveform");
    const pinned = document.querySelector(".walkthrough__pinned");
    const bars = waveformEl ? waveformEl.querySelectorAll("span") : [];

    const stepGlow = {
      1: "rgba(255,90,54,0.10)",
      2: "rgba(255,178,56,0.10)",
      3: "rgba(47,230,184,0.10)",
      4: "rgba(124,140,255,0.10)",
      5: "rgba(255,59,110,0.10)",
    };
    const btnState = {
      1: "idle",
      2: "connecting",
      3: "live",
      4: "live",
      5: "ending",
    };

    let currentStep = 0;
    let waveTimer = null;

    function animateWaveform() {
      if (waveTimer) clearInterval(waveTimer);
      waveTimer = setInterval(() => {
        bars.forEach((bar) => {
          bar.style.height = 20 + Math.round(Math.random() * 80) + "%";
        });
      }, 140);
    }

    function stopWaveform() {
      if (waveTimer) {
        clearInterval(waveTimer);
        waveTimer = null;
      }
      bars.forEach((bar) => (bar.style.height = "20%"));
    }

    function setStep(n) {
      if (n === currentStep) return;
      currentStep = n;

      if (pinned)
        pinned.style.setProperty(
          "--step-glow",
          stepGlow[n] || stepGlow[1]
        );
      if (stage) stage.setAttribute("data-step", n);
      if (callBtn) callBtn.setAttribute("data-state", btnState[n] || "idle");

      dots.forEach((dot) => {
        const s = parseInt(dot.dataset.step, 10);
        dot.classList.toggle("is-active", s === n);
      });
      stepEls.forEach((step) => {
        const s = parseInt(step.dataset.step, 10);
        step.classList.toggle("is-active", s === n);
      });

      if (fill) fill.style.height = (((n - 1) / 4) * 100).toFixed(1) + "%";

      if (n === 3) animateWaveform();
      else stopWaveform();
    }

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const idx = Array.from(markers).indexOf(entry.target);
            setStep(idx + 1);
          }
        });
      },
      { root: null, rootMargin: "-42% 0px -42% 0px", threshold: 0 }
    );

    markers.forEach((m) => observer.observe(m));

    dots.forEach((dot) => {
      dot.addEventListener("click", () => {
        const s = parseInt(dot.dataset.step, 10);
        const marker = document.querySelector(`.walkthrough__marker--${s}`);
        if (marker) marker.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });

    // init to step 1
    setStep(1);

    return () => {
      observer.disconnect();
      stopWaveform();
    };
  }, []);
}

export default function Walkthrough() {
  useReveal();
  useWalkthroughScroll();

  return (
    <>
      <Nav variant="default" />
      <main>
        {/* ===== COMPACT HERO ===== */}
        <section className="hero-compact" id="hero">
          <div className="hero-compact__glow" aria-hidden="true" />
          <div className="hero-compact__grid" aria-hidden="true" />
          <div className="wrap hero-compact__inner">
            <span className="eyebrow" style={{ justifyContent: "center" }}>
              The walkthrough
            </span>
            <h1>
              Watch exactly <em>how a call unfolds</em>.
            </h1>
            <p className="hero-compact__sub">
              Five moments, from the first click to hanging up — scroll through
              the whole conversation before you ever press connect yourself.
            </p>
            <div className="hero-compact__cta">
              <Link to="/console" className="btn btn-primary">
                Try it live
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                  <line x1="12" y1="18" x2="12" y2="22" />
                </svg>
              </Link>
              <Link to="/" className="btn-text">
                Back to overview
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </Link>
            </div>
          </div>
          <div className="hero-compact__scrollcue" aria-hidden="true">
            Scroll to begin
            <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6 9l6 6 6-6" />
            </svg>
          </div>
        </section>

        {/* ===== WALKTHROUGH ===== */}
        <section className="walkthrough" id="walkthrough" aria-label="Product walkthrough">
          <div className="walkthrough__outer">
            <div className="walkthrough__marker walkthrough__marker--1" aria-hidden="true" />
            <div className="walkthrough__marker walkthrough__marker--2" aria-hidden="true" />
            <div className="walkthrough__marker walkthrough__marker--3" aria-hidden="true" />
            <div className="walkthrough__marker walkthrough__marker--4" aria-hidden="true" />
            <div className="walkthrough__marker walkthrough__marker--5" aria-hidden="true" />

            <div className="walkthrough__pinned">
              <div className="walkthrough__inner">
                {/* Progress rail */}
                <div className="wt-progress" aria-hidden="true">
                  <div className="wt-progress__track">
                    <div className="wt-progress__line" />
                    <div className="wt-progress__fill" id="wtFill" />
                    {[1,2,3,4,5].map((n) => (
                      <div key={n} className={`wt-progress__dot${n === 1 ? " is-active" : ""}`} data-step={n}>{n}</div>
                    ))}
                  </div>
                </div>

                {/* Captions */}
                <div className="wt-captions">
                  {[
                    { n: 1, title: "Click connect", body: "One button. No sign-up, no setup. Just press connect and you're live.", icon: "mic" },
                    { n: 2, title: "Grant mic access", body: "Your browser asks for the mic — that's the only permission Unmute ever needs.", icon: "mic-off" },
                    { n: 3, title: "Talk — it listens live", body: "The moment you speak, the waveform reacts in real time — no delay, no queue.", icon: "mic" },
                    { n: 4, title: "Watch the transcript stream in", body: "Every word appears as it's spoken — yours and the agent's, side by side.", icon: "lines" },
                    { n: 5, title: "End it anytime", body: "One tap to hang up. Nothing lingers, nothing to clean up.", icon: "hang" },
                  ].map(({ n, title, body, icon }) => (
                    <div key={n} className={`wt-step${n === 1 ? " is-active" : ""}`} data-step={n}>
                      <span className="wt-step__number">Step {n}</span>
                      <h2 className="wt-step__headline">{title}</h2>
                      <p className="wt-step__body">{body}</p>
                      <span className="wt-step__visual" aria-hidden="true">
                        {icon === "lines" ? (
                          <svg viewBox="0 0 24 24" fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M4 6h16M4 12h10M4 18h13" />
                          </svg>
                        ) : icon === "hang" ? (
                          <svg viewBox="0 0 24 24" fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="2" y1="2" x2="22" y2="22" />
                            <path d="M10.7 15.3c-2-1-3.6-2.6-4.6-4.6l1.6-2.2a1.5 1.5 0 0 0 .2-1.6L6.4 3.7A1.5 1.5 0 0 0 5 3H3a1 1 0 0 0-1 1c0 10.5 8.5 19 19 19a1 1 0 0 0 1-1v-2a1.5 1.5 0 0 0-.7-1.4l-3.2-1.5a1.5 1.5 0 0 0-1.6.2z" />
                          </svg>
                        ) : (
                          <svg viewBox="0 0 24 24" fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                            <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                            <line x1="12" y1="18" x2="12" y2="22" />
                          </svg>
                        )}
                      </span>
                    </div>
                  ))}
                </div>

                {/* Stage mockup */}
                <div className="wt-stage" id="wtStage" data-step="1" aria-hidden="true">
                  {[1,2,3,4,5].map((n) => (
                    <div key={n} className={`wt-glow wt-glow--${n}`} />
                  ))}
                  <div className="wt-ring wt-ring--1" />
                  <div className="wt-ring wt-ring--2" />

                  <button className="wt-call-btn" id="wtCallBtn" data-state="idle" tabIndex={-1}>
                    <svg viewBox="0 0 24 24" fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6A19.79 19.79 0 012.12 4.18 2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z" />
                    </svg>
                  </button>

                  {/* Cursor (step 1) */}
                  <div className="wt-cursor">
                    <span className="wt-cursor__ripple" />
                    <svg viewBox="0 0 20 20">
                      <path d="M3 1L3 16 7 12 12 19 14 18 9 11 15 11 3 1Z" />
                    </svg>
                  </div>

                  {/* Permission popup (step 2) */}
                  <div className="wt-permission">
                    <div className="wt-permission__row">
                      <span className="wt-permission__icon">
                        <svg viewBox="0 0 24 24" fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
                          <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
                        </svg>
                      </span>
                      <span className="wt-permission__title">unmute.app wants to use your microphone</span>
                    </div>
                    <span className="wt-permission__body">Allow access so you can speak to the agent.</span>
                    <div className="wt-permission__actions">
                      <span className="wt-permission__btn wt-permission__btn--deny">Block</span>
                      <span className="wt-permission__btn wt-permission__btn--allow">Allow</span>
                    </div>
                  </div>

                  {/* Waveform bars (step 3) */}
                  <div className="wt-waveform" id="wtWaveform" aria-hidden="true">
                    {Array.from({ length: 8 }, (_, i) => <span key={i} />)}
                  </div>

                  {/* Transcript (step 4) */}
                  <div className="wt-transcript" aria-hidden="true">
                    <div className="wt-transcript__line wt-transcript__line--you"><b>You</b>Hey, what can you do?</div>
                    <div className="wt-transcript__line wt-transcript__line--agent"><b>Agent</b>I can help with questions, brainstorming, coding — just ask.</div>
                    <div className="wt-transcript__line wt-transcript__line--you"><b>You</b>Tell me about WebRTC.</div>
                    <div className="wt-transcript__line wt-transcript__line--agent"><b>Agent</b>WebRTC enables real-time peer-to-peer audio, in the browser<span className="wt-cursor-blink" /></div>
                  </div>

                  {/* Ended state (step 5) */}
                  <div className="wt-ended">
                    <span className="wt-ended__check">
                      <svg viewBox="0 0 24 24" fill="none" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20 6L9 17l-5-5" />
                      </svg>
                    </span>
                    <span className="wt-ended__label">Call ended · 00:00</span>
                  </div>

                  <div className="wt-sweep" aria-hidden="true" />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ===== CLOSING CTA ===== */}
        <section className="wt-cta">
          <div className="wrap">
            <div className="wt-cta__card reveal">
              <h2>That's the whole call.</h2>
              <p>
                No app to install, no account to create. The console is one page
                and one button away — try it with your own voice.
              </p>
              <Link to="/console" className="btn btn-primary">
                Try it live
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer variant="default" />
    </>
  );
}
