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
    crm_quiet_period: int = 10


settings = Settings()
