import { useVoiceAgent } from "../hooks/useVoiceAgent";
import Nav from "../components/Nav";
import CallConsole from "../components/CallConsole";
import MenuPanel from "../components/MenuPanel";
import TranscriptPanel from "../components/TranscriptPanel";
import Footer from "../components/Footer";
import "./Console.css";

export default function Console() {
  const {
    callState,
    errorMessage,
    seconds,
    micMuted,
    userLevel,
    agentLevel,
    agentSpeaking,
    userSpeaking,
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
          userSpeaking={userSpeaking}
          connect={connect}
          disconnect={disconnect}
          toggleMic={toggleMic}
        />
        <MenuPanel />
        <TranscriptPanel transcript={transcript} callState={callState} />
      </main>
      <Footer variant="light" />
    </>
  );
}