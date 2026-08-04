// Wraps a MediaStreamTrack in a Web Audio AnalyserNode and polls a rolling
// 0..1 amplitude level via requestAnimationFrame. Used to drive the console
// waveform and to detect "is this side of the call currently making sound".
export function createLevelMeter(mediaStreamTrack, onLevel) {
  const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  const source = audioCtx.createMediaStreamSource(
    new MediaStream([mediaStreamTrack])
  );
  const analyser = audioCtx.createAnalyser();
  analyser.fftSize = 256;
  analyser.smoothingTimeConstant = 0.75;
  source.connect(analyser);

  const data = new Uint8Array(analyser.frequencyBinCount);
  let rafId = null;
  let frame = 0;

  // Sample the analyser every frame for accuracy, but only push a React
  // state update every 3rd frame (~20fps) — plenty smooth for a level
  // meter while avoiding a full re-render at 60fps for the whole page.
  function tick() {
    analyser.getByteFrequencyData(data);
    let sum = 0;
    for (let i = 0; i < data.length; i++) sum += data[i];
    const level = Math.min(1, sum / data.length / 90);
    frame += 1;
    if (frame % 3 === 0) onLevel(level);
    rafId = requestAnimationFrame(tick);
  }
  tick();

  return function stop() {
    if (rafId) cancelAnimationFrame(rafId);
    try {
      source.disconnect();
      analyser.disconnect();
    } catch {
      /* already torn down */
    }
    audioCtx.close().catch(() => {});
  };
}
