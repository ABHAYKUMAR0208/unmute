const LABELS = {
  idle: "Idle",
  connecting: "Connecting…",
  connected: "Live",
  "agent-speaking": "Agent speaking",
  error: "Connection error",
};

export default function StatusPill({ callState, agentSpeaking }) {
  const state =
    callState === "connected" && agentSpeaking ? "agent-speaking" : callState;
  return (
    <span className="status-pill" data-state={state} role="status" aria-live="polite">
      <span className="status-pill__dot" />
      {LABELS[state] ?? state}
    </span>
  );
}
