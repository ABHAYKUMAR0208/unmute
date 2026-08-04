import { memo, useEffect, useRef } from "react";

function TranscriptPanel({ transcript, callState }) {
  const bodyRef = useRef(null);
  const isLive = callState === "connected" || callState === "agent-speaking";

  useEffect(() => {
    if (bodyRef.current) {
      bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
    }
  }, [transcript]);

  return (
    <section className="transcript" aria-label="Conversation transcript">
      <div className="transcript__head">
        <h2>Transcript</h2>
        <span className={`transcript__live${isLive ? " is-live" : ""}`}>
          <i />
          LIVE
        </span>
      </div>
      <div className="transcript__body" ref={bodyRef}>
        {transcript.length === 0 ? (
          <p className="transcript__empty">
            Nothing said yet. Connect and start talking — what you and the agent
            say will appear here as it happens.
          </p>
        ) : (
          <div className="transcript__list">
            {transcript.map((line, idx) => (
              <div
                className={`line line--${line.role === "user" ? "you" : "agent"}`}
                key={line.id}
                style={{ animationDelay: `${idx * 0.05}s` }}
              >
                <span className="line__role">
                  {line.role === "user" ? "You" : "Agent"}
                </span>
                <span className="line__text">{line.text}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

export default memo(TranscriptPanel);
