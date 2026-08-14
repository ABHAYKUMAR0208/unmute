import VoiceCore from "./VoiceCore";

function pad(n) {
  return String(n).padStart(2, "0");
}

function formatDuration(s) {
  return `${pad(Math.floor(s / 60))}:${pad(s % 60)}`;
}

function PhoneIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6 19.8 19.8 0 0 1-3-8.7A2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.3 1.8.6 2.7a2 2 0 0 1-.4 2.1L8 9.9a16 16 0 0 0 6 6l1.4-1.4a2 2 0 0 1 2.1-.4c.9.3 1.8.5 2.7.6a2 2 0 0 1 1.8 2.2z" />
    </svg>
  );
}

function HangupIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.7 15.3c-2-1-3.6-2.6-4.6-4.6l1.6-2.2a1.5 1.5 0 0 0 .2-1.6L6.4 3.7A1.5 1.5 0 0 0 5 3H3a1 1 0 0 0-1 1c0 10.5 8.5 19 19 19a1 1 0 0 0 1-1v-2a1.5 1.5 0 0 0-.7-1.4l-3.2-1.5a1.5 1.5 0 0 0-1.6.2z" />
      <line x1="2" y1="2" x2="22" y2="22" />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" />
      <line x1="12" y1="8" x2="12" y2="13" />
      <line x1="12" y1="16.5" x2="12" y2="16.51" />
    </svg>
  );
}

function MicOnIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 2a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
      <path d="M19 10v1a7 7 0 0 1-14 0v-1" />
      <line x1="12" y1="18" x2="12" y2="22" />
    </svg>
  );
}

function MicOffIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="2" y1="2" x2="22" y2="22" />
      <path d="M9 9v3a3 3 0 0 0 4.6 2.5M15 9.4V5a3 3 0 0 0-5.9-.7" />
      <path d="M19 10v1a7 7 0 0 1-.4 2.3M5 10v1a7 7 0 0 0 10.6 6" />
      <line x1="12" y1="18" x2="12" y2="22" />
    </svg>
  );
}

export default function CallConsole({
  callState,
  errorMessage,
  seconds,
  micMuted,
  userLevel,
  agentLevel,
  agentSpeaking,
  userSpeaking,
  connect,
  disconnect,
  toggleMic,
}) {
  const isLive = callState === "connected" || callState === "agent-speaking";
  const isIdle = callState === "idle";
  const isConnecting = callState === "connecting";
  const isError = callState === "error";

  const uiState = isError
    ? "error"
    : isConnecting
    ? "connecting"
    : agentSpeaking
    ? "agent-speaking"
    : userSpeaking
    ? "user-speaking"
    : isLive
    ? "connected"
    : "idle";

  const activeLevel = agentSpeaking ? agentLevel : userSpeaking ? userLevel : 0;

  function handleCallClick() {
    if (isLive) {
      disconnect();
    } else {
      connect();
    }
  }

  const buttonAriaLabel = isLive
    ? "End call"
    : isError
    ? "Retry connection"
    : "Connect call";

  return (
    <>
      {/* Ambient glow — colour shifts with call state */}
      <div className="console-main__glow" aria-hidden="true" data-state={uiState} />

      {/* Status pill */}
      <div className="status-pill" data-state={uiState} role="status" aria-live="polite">
        <span className="status-pill__dot" />
        <span>
          {{
            idle: "Idle",
            connecting: "Connecting…",
            connected: "Live",
            "agent-speaking": "Agent speaking",
            "user-speaking": "You're speaking",
            error: "Connection error",
          }[uiState] ?? uiState}
        </span>
      </div>

      {/* Call console */}
      <section className="call-console" aria-label="Call console">
        <VoiceCore state={uiState} isLive={isLive} micMuted={micMuted} level={activeLevel} />

        <div className={`call-timer${isLive ? " is-live" : ""}`}>
          {formatDuration(seconds)}
        </div>

        <div className="call-controls">
          <button
            className="mute-toggle"
            data-muted={micMuted ? "true" : "false"}
            onClick={toggleMic}
            disabled={!isLive}
            aria-pressed={micMuted}
            aria-label={micMuted ? "Unmute microphone" : "Mute microphone"}
          >
            {micMuted ? <MicOffIcon /> : <MicOnIcon />}
            {micMuted ? "Unmute" : "Mute"}
          </button>

          <button
            className="call-button"
            data-state={uiState}
            onClick={handleCallClick}
            disabled={isConnecting}
            aria-label={buttonAriaLabel}
          >
            {isError ? <ErrorIcon /> : isLive ? <HangupIcon /> : <PhoneIcon />}
          </button>
        </div>

        {isIdle && (
          <p className="call-help">
            Your browser will ask for microphone access when you connect.
          </p>
        )}

        {isError && errorMessage && (
          <p className="call-error">
            <ErrorIcon />
            <span>{errorMessage}</span>
          </p>
        )}
      </section>
    </>
  );
}