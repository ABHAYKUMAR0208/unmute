"""
TranscriptWriter — captures agent and user turns for one LiveKit room
session and saves them to disk.

Storage layout:

  transcripts/
    unprocessed/<room_name>.jsonl   <- one JSON object per completed turn,
                                        crash-safe. This is the ONLY place
                                        JSON transcripts get written to.
    unprocessed/<room_name>.done    <- written once, after the LiveKit job
                                        actually ends (see mark_complete()).
                                        Presence of this file is what tells
                                        the CRM worker a transcript is ready
                                        to process — not file-quiet timing.
                                        A downstream job is expected to pick
                                        these up and move them to processed/
                                        or failed/ once handled.
    processed/                      <- destination for a downstream
                                        consumer to move successfully
                                        processed transcripts into. Not
                                        written to by this class.
    failed/                         <- destination for a downstream
                                        consumer to move transcripts into
                                        that failed processing. Not written
                                        to by this class.
    txt/<room_name>.txt             <- human-readable plain text version,
                                        kept separate from the JSON pipeline.
"""

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("transcript-writer")

TRANSCRIPTS_DIR = Path("transcripts")
UNPROCESSED_DIR = TRANSCRIPTS_DIR / "unprocessed"
PROCESSED_DIR = TRANSCRIPTS_DIR / "processed"
FAILED_DIR = TRANSCRIPTS_DIR / "failed"
TXT_DIR = TRANSCRIPTS_DIR / "txt"


class TranscriptWriter:
    def __init__(self, room_name: str):
        self.room_name = room_name
        self.started_at = time.time()

        # Create the full folder structure up front (processed/ and failed/
        # aren't written to here, but should exist from the start so a
        # downstream mover job always has somewhere to put files).
        for d in (UNPROCESSED_DIR, PROCESSED_DIR, FAILED_DIR, TXT_DIR):
            d.mkdir(parents=True, exist_ok=True)

        self.jsonl_path = UNPROCESSED_DIR / f"{room_name}.jsonl"
        self.txt_path = TXT_DIR / f"{room_name}.txt"

        # Buffers the in-progress line for whichever role is currently
        # "speaking" in delta form, same grouping idea as the frontend panel.
        self._current_role: str | None = None
        self._current_text: str = ""

        with open(self.txt_path, "a", encoding="utf-8") as f:
            f.write(f"=== Session: {room_name} ===\n")

        logger.info(
            "TranscriptWriter ready — room=%s jsonl=%s txt=%s",
            room_name, self.jsonl_path, self.txt_path,
        )

    def add_delta(self, role: str, delta: str):
        """
        Call this on every text delta (assistant or user). Deltas from the
        same role accumulate into one turn; a role switch flushes the
        previous turn to disk before starting the new one.
        """
        if self._current_role is not None and self._current_role != role:
            self._flush_turn()

        self._current_role = role

        # Streamed deltas aren't guaranteed to carry their own separating
        # space (seen from both the LLM text stream and the STT transcript
        # stream) — insert one when neither side already has whitespace at
        # the join point, mirroring Unmute's own Chatbot.add_chat_message_delta.
        needs_space = (
            self._current_text
            and not self._current_text[-1].isspace()
            and delta
            and not delta[0].isspace()
        )
        if needs_space:
            delta = " " + delta

        self._current_text += delta

    def flush_pending(self):
        """Call on session shutdown to make sure the last turn isn't lost."""
        self._flush_turn()
 
    def mark_complete(self):
        """
        Call once, AFTER flush_pending(), when the LiveKit job has actually
        ended (i.e. from the agent's shutdown callback). Writes a small
        sentinel file next to the transcript so the CRM worker can detect
        "this call is truly over" directly, instead of guessing from file
        modification timing — see app/crm/worker.py for the consumer side.
 
        Order matters: this must be called after flush_pending(), so the
        sentinel never appears before the last turn is actually on disk.
        """
        done_path = UNPROCESSED_DIR / f"{self.room_name}.done"
        done_path.write_text(str(time.time()), encoding="utf-8")
        logger.info("Marked transcript complete -> %s", done_path)

    def _flush_turn(self):
        text = self._current_text.strip()
        if text:
            turn = {
                "room": self.room_name,
                "role": self._current_role,
                "text": text,
                "ts": time.time(),
            }
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(turn, ensure_ascii=False) + "\n")

            label = "AGENT" if self._current_role == "assistant" else "USER"
            with open(self.txt_path, "a", encoding="utf-8") as f:
                f.write(f"[{label}] {text}\n")

            logger.info("[TRANSCRIPT] %s: %s", label, text)

        self._current_role = None
        self._current_text = ""