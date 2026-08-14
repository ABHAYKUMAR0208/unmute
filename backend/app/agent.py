"""
LiveKit agent entrypoint: joins a room, forwards the caller's audio to
Unmute (running on RunPod), and plays Unmute's response audio back into
the room.

Run (inside the container):
    python -m app.agent start      # production
    python -m app.agent dev        # local dev with a LiveKit dev server
"""

from __future__ import annotations

import asyncio
import json
import logging

import numpy as np
from livekit import rtc
from livekit.agents import AutoSubscribe, JobContext, WorkerOptions, cli

from .config import settings
from .unmute_realtime_session import SAMPLE_RATE, UnmuteRealtimeSession
from .transcript_writer import TranscriptWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("unmute-agent")


async def entrypoint(ctx: JobContext):
    # --- Set up Unmute session object (not yet connected over the network) ---
    transcript_writer = TranscriptWriter(room_name=ctx.room.name)

    def publish_transcript(role: str, delta: str):
        payload = json.dumps({"role": role, "delta": delta}).encode("utf-8")
        asyncio.create_task(
            ctx.room.local_participant.publish_data(
                payload, reliable=True, topic="transcript"
            )
        )

    # NOTE: Billing moved to crm/worker.py + payments/billing_service.py.
    # It now runs AFTER the call ends, using the same LLM-extracted items
    # already pushed to HubSpot — so bill quantities always match CRM
    # exactly. Trade-off: the guest gets the payment link a few seconds
    # after hangup instead of live during the call. See billing_service.py
    # docstring for details. PaymentBridge (live, regex-based extraction)
    # is intentionally no longer wired in here to avoid double-billing.

    def on_assistant_delta(delta: str):
        logger.info("assistant text: %s", delta)
        publish_transcript("assistant", delta)
        transcript_writer.add_delta("assistant", delta)

    def on_user_delta(delta: str):
        logger.info("user said: %s", delta)
        publish_transcript("user", delta)
        transcript_writer.add_delta("user", delta)

    # --- Set up Unmute session object (not yet connected over the network) ---
    session = UnmuteRealtimeSession(
    pod_id=settings.unmute_pod_id,
    voice=settings.unmute_voice,
    instructions="""
You are Kelly, the voice hotel assistant for Grandview Hotel. This is a live phone/voice call. Keep replies short — 1 sentence when possible, 2 max. No lists, no markdown, speak naturally.
SCOPE
You only help with: taxi booking, laundry/dry cleaning pickup, food & beverage orders, maintenance requests.
Anything else, say exactly: "I'm here to assist with hotel services. How may I help you today?"
BEFORE EVERY REPLY: re-read the full conversation so far and determine state fresh each time. Never trust what you did last turn without re-checking — re-derive it from what was actually said.
STEP ORDER (do the FIRST step below that is not yet satisfied by the conversation so far; do only that one step)
1. Greeting not yet given → say exactly: "Welcome to Grandview Hotel! I'm Kelly, your hotel assistant. How may I assist you today?"
2. Room number not yet clearly stated by the guest → ask: "May I have your room number, please?"
3. Service type not yet stated → ask: "What service can I assist you with today?"
4. Service type known, but required fields for it are missing (see list below) → ask for the single next missing field only.
5. All fields collected, not yet confirmed → say once: "To confirm: Room [room number], you requested [summary]. Is that correct?"
6. Guest confirmed → say exactly: "Your request has been recorded. Thank you and goodbye." Then stop responding.
REQUIRED FIELDS BY SERVICE
- Taxi: destination, pickup time
- Laundry: items, pickup time
- Food: items, quantity, special instructions (ask "any special instructions?" — "no" counts as answered), delivery time
- Maintenance: issue description, urgency
RULES
- Ask ONE question per turn. Never combine two questions.
- If the guest already said something earlier in the call, do not ask for it again — reuse it.
- If a room number or detail sounds unclear or mistranscribed, briefly confirm it once ("Just to confirm, room 410?") instead of guessing.
- Never assume unstated details.
- Acknowledge briefly ("Sure.", "Got it.", "Certainly.") before each question after the greeting.
- If the guest corrects a detail already given, update it and go back to step 5 to reconfirm — do not restart from step 1.
- Do not repeat the room number or guest's details back except in the final confirmation step.
 """,
    on_text_delta=on_assistant_delta,
    on_user_transcript_delta=on_user_delta,
)
    
    # --- Forward each subscribed participant's mic audio into Unmute ---
    async def handle_track(track: rtc.Track):
        audio_stream = rtc.AudioStream(track, sample_rate=SAMPLE_RATE, num_channels=1)
        async for event in audio_stream:
            frame = event.frame
            pcm_i16 = np.frombuffer(frame.data, dtype=np.int16)
            pcm_f32 = pcm_i16.astype(np.float32) / 32768.0
            await session.push_pcm(pcm_f32)

    # IMPORTANT: register this listener BEFORE ctx.connect(). If registered
    # after, a fast-publishing browser participant can have its audio track
    # auto-subscribed and the event fired before we're listening for it,
    # silently dropping all incoming audio.
    @ctx.room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.TrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        if track.kind == rtc.TrackKind.KIND_AUDIO:
            logger.info("Subscribed to audio from %s", participant.identity)
            asyncio.create_task(handle_track(track))

    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
    logger.info("Agent joined room %s", ctx.room.name)

    # Defensive safety net for already-subscribed tracks at connect time.
    for participant in ctx.room.remote_participants.values():
        for publication in participant.track_publications.values():
            if (
                publication.subscribed
                and publication.track is not None
                and publication.track.kind == rtc.TrackKind.KIND_AUDIO
            ):
                logger.info(
                    "Found already-subscribed audio from %s", participant.identity
                )
                asyncio.create_task(handle_track(publication.track))

    # --- Set up the outbound track the agent will speak through ---
    source = rtc.AudioSource(SAMPLE_RATE, 1)
    track = rtc.LocalAudioTrack.create_audio_track("unmute-voice", source)
    await ctx.room.local_participant.publish_track(
        track, rtc.TrackPublishOptions(source=rtc.TrackSource.SOURCE_MICROPHONE)
    )

    # --- Connect to Unmute on RunPod ---
    await session.connect()

    # --- Task: drain Unmute's decoded audio into the LiveKit output track ---
    async def playback_loop():
        while True:
            pcm: np.ndarray = await session.audio_out_queue.get()
            pcm_i16 = (pcm * 32767.0).clip(-32768, 32767).astype(np.int16)
            frame = rtc.AudioFrame(
                data=pcm_i16.tobytes(),
                sample_rate=SAMPLE_RATE,
                num_channels=1,
                samples_per_channel=pcm_i16.shape[0],
            )
            await source.capture_frame(frame)

    playback_task = asyncio.create_task(playback_loop())

    async def cleanup():
        playback_task.cancel()
        transcript_writer.flush_pending()
        transcript_writer.mark_complete()
        await session.close()

    ctx.add_shutdown_callback(cleanup)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            ws_url=settings.livekit_url,
            api_key=settings.livekit_api_key,
            api_secret=settings.livekit_api_secret,
        )
    )