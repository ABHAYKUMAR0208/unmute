import { useVoiceAgent } from "../hooks/useVoiceAgent";
import Nav from "../components/Nav";
import CallConsole from "../components/CallConsole";
import TranscriptPanel from "../components/TranscriptPanel";
import Footer from "../components/Footer";

export default function Console() {
  const {
    callState,
    errorMessage,
    seconds,
    micMuted,
    userLevel,
    agentLevel,
    agentSpeaking,
    transcript,
    connect,
    disconnect,
    toggleMic,
  } = useVoiceAgent();

  return (
    <>
      <Nav variant="console" />
      <main className="console-main">
        <CallConsole
          callState={callState}
          errorMessage={errorMessage}
          seconds={seconds}
          micMuted={micMuted}
          userLevel={userLevel}
          agentLevel={agentLevel}
          agentSpeaking={agentSpeaking}
          connect={connect}
          disconnect={disconnect}
          toggleMic={toggleMic}
        />
        <TranscriptPanel transcript={transcript} callState={callState} />
      </main>
      <Footer variant="light" />
    </>
  );
}
