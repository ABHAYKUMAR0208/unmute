from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str

    unmute_pod_id: str
    unmute_voice: str | None = None

    # ── CRM (HubSpot) ────────────────────────────────────────────────
    hubspot_access_token: str | None = None
    hubspot_taxi_object_type: str | None = None
    hubspot_laundry_object_type: str | None = None
    hubspot_food_object_type: str | None = None
    hubspot_maintenance_object_type: str | None = None
    hubspot_payment_object_type: str | None = None
    hubspot_transcript_object_type: str | None = None
    hubspot_guest_object_type: str | None = None

    # ── CRM extraction (Ollama / Phi-3 Mini) ────────────────────────
    ollama_url: str = "http://localhost:11434/api/chat"

    # ── CRM worker (transcript file poller) ─────────────────────────
    crm_transcripts_dir: str = "transcripts"
    crm_outputs_dir: str = "crm_outputs"
    crm_poll_interval: int = 2
 
    # Fallback only — not the primary trigger anymore. A transcript is
    # normally processed as soon as its .done sentinel appears (written by
    # TranscriptWriter.mark_complete() on graceful shutdown). This timeout
    # only kicks in if a .jsonl sits with no .done file for this long,
    # covering the case where the agent process crashed before it could
    # write the sentinel. Should be comfortably longer than any real call.
    crm_stale_after_seconds: int = 300


settings = Settings()
