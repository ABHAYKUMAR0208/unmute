"""
Unmute <-> LiveKit bridge (Path A: single realtime WebSocket adapter).

Connects to an Unmute backend running on RunPod, speaking Unmute's
OpenAI-Realtime-*inspired* event schema over `/v1/realtime`.

Key protocol facts (confirmed from unmute/main_websocket.py and
unmute/openai_realtime_api_events.py in the Unmute repo):

- Endpoint:      wss://<POD_ID>-8000.proxy.runpod.net/v1/realtime
- Subprotocol:   the client MUST request subprotocol "realtime" during the
                  WebSocket handshake.
- Messages:      JSON text frames only.
- Audio in:      InputAudioBufferAppend.audio = base64(OGG-Opus stream bytes),
                  produced by an sphn.OpusStreamWriter so the framing matches
                  what the server's sphn.OpusStreamReader expects.
- Audio out:     ResponseAudioDelta.delta = base64(OGG-Opus stream bytes).
- Sample rate:   24000 Hz fixed.
- Turn-taking:   Handled server-side by VAD.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
from typing import Callable, Optional

import numpy as np
import sphn
import websockets

logger = logging.getLogger("unmute-bridge")

SAMPLE_RATE = 24000  # fixed by Unmute server, do not change
CHANNELS = 1


class UnmuteRealtimeSession:
    """
    Wraps one WebSocket connection to Unmute's /v1/realtime endpoint and
    exposes a simple push-audio-in / receive-audio-out interface.
    """

    def __init__(
        self,
        pod_id: str,
        voice: str | None = None,
        instructions: str | None = None,
        allow_recording: bool = False,
        on_text_delta: Optional[Callable[[str], None]] = None,
        on_user_transcript_delta: Optional[Callable[[str], None]] = None,
    ):
        self.url = f"wss://{pod_id}-8000.proxy.runpod.net/v1/realtime"
        self.voice = voice
        self.instructions = instructions
        self.allow_recording = allow_recording
        self.on_text_delta = on_text_delta
        self.on_user_transcript_delta = on_user_transcript_delta

        self._ws: websockets.WebSocketClientProtocol | None = None
        self._opus_writer = sphn.OpusStreamWriter(SAMPLE_RATE)
        self._opus_reader = sphn.OpusStreamReader(SAMPLE_RATE)

        self.audio_out_queue: asyncio.Queue[np.ndarray] = asyncio.Queue()

        self._recv_task: asyncio.Task | None = None
        self._closed = False

    async def connect(self):
        logger.info("Connecting to Unmute at %s", self.url)
        self._ws = await websockets.connect(
            self.url,
            subprotocols=["realtime"],
            max_size=None,
            ping_interval=20,
            ping_timeout=20,
        )

        session_update = {
            "type": "session.update",
            "session": {
                "instructions": (
                    {"type": "constant", "text": self.instructions}
                    if self.instructions
                    else None
                ),
                "voice": self.voice,
                "allow_recording": self.allow_recording,
            },
        }
        await self._ws.send(json.dumps(session_update))

        self._recv_task = asyncio.create_task(self._recv_loop())
        logger.info("Unmute session established")

    async def close(self):
        self._closed = True
        if self._recv_task:
            self._recv_task.cancel()
        if self._ws:
            await self._ws.close()

    async def push_pcm(self, pcm: np.ndarray):
        if self._ws is None:
            return

        opus_bytes: bytes = await asyncio.to_thread(
            self._opus_writer.append_pcm, pcm
        )
        if not opus_bytes:
            return

        msg = {
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(opus_bytes).decode("ascii"),
        }
        await self._ws.send(json.dumps(msg))

    async def _recv_loop(self):
        assert self._ws is not None
        try:
            async for raw in self._ws:
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("Non-JSON message from Unmute, ignoring")
                    continue

                await self._handle_event(event)
        except websockets.ConnectionClosed as e:
            if not self._closed:
                logger.warning("Unmute connection closed unexpectedly: %s", e)
        except asyncio.CancelledError:
            pass

    async def _handle_event(self, event: dict):
        etype = event.get("type")

        if etype == "response.audio.delta":
            opus_bytes = base64.b64decode(event["delta"])
            pcm: np.ndarray = await asyncio.to_thread(
                self._opus_reader.append_bytes, opus_bytes
            )
            if pcm.size:
                await self.audio_out_queue.put(pcm)

        elif etype == "response.audio.done":
            logger.debug("Response audio finished")

        elif etype == "response.text.delta":
            if self.on_text_delta:
                self.on_text_delta(event["delta"])

        elif etype == "conversation.item.input_audio_transcription.delta":
            if self.on_user_transcript_delta:
                self.on_user_transcript_delta(event["delta"])

        elif etype == "input_audio_buffer.speech_started":
            logger.debug("User started speaking (server VAD)")

        elif etype == "input_audio_buffer.speech_stopped":
            logger.debug("User stopped speaking (server VAD)")

        elif etype == "unmute.interrupted_by_vad":
            logger.debug("Response interrupted by VAD (user barge-in)")

        elif etype == "session.updated":
            logger.info("Session config acknowledged by Unmute")

        elif etype == "error":
            logger.error("Unmute error event: %s", event.get("error"))

        else:
            logger.debug("Unhandled event type: %s", etype)
