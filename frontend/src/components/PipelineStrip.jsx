import { memo } from "react";

const STEPS = [
  {
    index: "01",
    title: "You speak",
    body: "Your mic audio streams to the agent over a live WebRTC connection the moment you connect — no recording, no upload step.",
  },
  {
    index: "02",
    title: "The agent listens & thinks",
    body: "Speech is transcribed and answered in real time, with your words appearing in the transcript as they're understood.",
  },
  {
    index: "03",
    title: "It replies out loud",
    body: "The response streams back as audio and plays automatically, so the conversation stays spoken end to end.",
  },
];

function PipelineStrip() {
  return (
    <div className="pipeline">
      {STEPS.map((step) => (
        <div className="pipeline-step" key={step.index}>
          <span className="pipeline-index">{step.index}</span>
          <h3>{step.title}</h3>
          <p>{step.body}</p>
        </div>
      ))}
    </div>
  );
}

export default memo(PipelineStrip);
