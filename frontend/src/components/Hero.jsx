import { memo } from "react";

function Hero() {
  return (
    <div className="hero">
      <span className="hero-eyebrow">Real-time voice agent</span>
      <h1>
        Talk to it. <em>It talks back.</em>
      </h1>
      <p>
        One button, one open microphone. Press connect and you&apos;re speaking
        with the agent live — no typing, no waiting for a reply to render.
      </p>
    </div>
  );
}

export default memo(Hero);
