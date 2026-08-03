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
from .payments import PaymentBridge
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

    # --- Payment bridge: watches the live transcript and auto-creates a
    # priced bill + PayU payment link once an order looks closed. ---
    def on_payment_ready(payment_link: str, bill_text: str, room_number: str):
        logger.info("Payment link ready for room %s: %s", room_number, payment_link)
        payload = json.dumps({
            "type": "payment_ready",
            "room_number": room_number,
            "payment_link": payment_link,
            "bill_text": bill_text,
        }).encode("utf-8")
        asyncio.create_task(
            ctx.room.local_participant.publish_data(payload, reliable=True, topic="payment")
        )

    def on_payment_confirmed(order_id: str, amount: str, room_number: str):
        logger.info("Payment confirmed for order %s (room %s): Rs%s", order_id, room_number, amount)
        payload = json.dumps({
            "type": "payment_confirmed",
            "order_id": order_id,
            "amount": amount,
            "room_number": room_number,
        }).encode("utf-8")
        asyncio.create_task(
            ctx.room.local_participant.publish_data(payload, reliable=True, topic="payment")
        )

    payment_bridge = PaymentBridge(
        on_payment_ready=on_payment_ready,
        on_payment_confirmed=on_payment_confirmed,
    )

    def on_assistant_delta(delta: str):
        logger.info("assistant text: %s", delta)
        publish_transcript("assistant", delta)
        transcript_writer.add_delta("assistant", delta)
        payment_bridge.notify_turn("agent", delta)

    def on_user_delta(delta: str):
        logger.info("user said: %s", delta)
        publish_transcript("user", delta)
        transcript_writer.add_delta("user", delta)
        payment_bridge.notify_turn("user", delta)

    # --- Set up Unmute session object (not yet connected over the network) ---
    session = UnmuteRealtimeSession(
    pod_id=settings.unmute_pod_id,
    voice=settings.unmute_voice,
    instructions="""
You are Kelly, a professional hotel assistant for Grandview Hotel.

You only handle hotel service requests and must not talk about anything else.

Never repeat or echo back what the user just said, including their room number, name, or order details. Simply acknowledge with phrases like:
- "Got it"
- "Sure"

Then move to the next question.

Conversation Flow:
1. Always start with:
   "May I have your room number, please?"

2. After the guest provides the room number:
   Ask what service they need.

Supported Services Only:
- Taxi booking
- Laundry pickup and dry cleaning
- Food and beverage orders
- Maintenance requests for broken appliances or plumbing

Taxi Service Rules:
- Whenever the user asks for a taxi service, you must ALWAYS collect:
  - Room number
  - Pickup time
  - Destination
- If any of these details are missing, ask for the missing detail one at a time.
- Never proceed without collecting all three details.

Required Information Collection:

Taxi:
- Room number
- Destination
- Pickup time

Laundry:
- Items
- Pickup time

Food Orders:
- Items ordered
- Quantity of each item
- Special instructions (allergies/preferences)
- Preferred delivery time
  - If no delivery time is given, ask for it.

Maintenance:
- Issue description
- Urgency

Rules:
- If any detail is missing, ask a follow-up question.
- Ask only ONE question at a time.
- Never assume missing information.
- Keep responses short and clear.
- Do NOT repeat:
  - Room number
  - Guest name
  - Item names
  - Quantities
  - Any other provided details
- Store all details silently and continue.

Before Ending:
You MUST confirm once using:

"To confirm: Room [number], you requested [service/details] at [time] with [special instructions]. Is that correct?"

Only end after confirmation.

If user says something unrelated:
Respond with:
"I’m here to assist with hotel services. How may I help you today?"

End every conversation with:
"Thank you and goodbye."
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
        payment_bridge.stop()
        transcript_writer.flush_pending()
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
