import { memo } from "react";
import StatusPill from "./StatusPill";

function Header({ callState, agentSpeaking }) {
  return (
    <header className="site-header">
      <div className="wordmark">
        <span className="wordmark-dot" />
        unmute
      </div>
      <StatusPill callState={callState} agentSpeaking={agentSpeaking} />
    </header>
  );
}

export default memo(Header);
