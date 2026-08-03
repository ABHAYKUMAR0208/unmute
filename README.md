# Unmute Voice Agent — Production Structure

```
unmute-prod/
├── docker-compose.yml
├── .env.example
├── data/                              # PayU's SQLite bills DB (volume)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                    # FastAPI: /token + mounts payments router (/health, /api/*, /pay, /payment/*)
│       ├── agent.py                   # LiveKit agent worker
│       ├── unmute_realtime_session.py # Bridge to Unmute on RunPod
│       ├── config.py                  # LiveKit/HubSpot/CRM settings (from .env)
│       ├── crm_router.py              # GET /api/crm, /api/crm/{id}
│       ├── crm/                       # transcript → HubSpot pipeline
│       │   ├── extractor.py
│       │   ├── validator.py
│       │   ├── hubspot_client.py
│       │   └── worker.py
│       ├── payments/                  # ← PayU billing/payment worker, merged in
│       │   ├── config.py              # PayuWorkerSettings (own dataclass, same .env)
│       │   ├── models.py
│       │   ├── bill_generator.py      # idempotent bill creation, SQLite
│       │   ├── payu_client.py         # hash generation/verification
│       │   ├── webhook_handler.py     # /payment/success + /payment/failure
│       │   ├── maintenance.py         # background stale-bill sweep
│       │   ├── router.py              # /api/create-bill, /api/refund, /pay/{order_id}, ...
│       │   └── service_catalog.py     # sample hotel menu (name → price)
│       └── taxi/                      # taxi booking worker (SMS/email already wired)
└── frontend/
    ├── Dockerfile                     # nginx serving the static page
    └── public/index.html
```

## Architecture

Five containers, one `docker-compose.yml`:

1. **`token-api`** (FastAPI) — mints LiveKit tokens on `/token`, **and**
   hosts the PayU billing/payment API + webhook callbacks (mounted from
   `app/payments`). Port `8081` on the host.
2. **`agent-worker`** — the LiveKit agent process. Bridges audio to
   Unmute running on RunPod.
3. **`crm-worker`** — watches finished-call transcripts, extracts the
   order, pushes it to HubSpot, and (once wired) creates the PayU bill.
4. **`taxi-worker`** — polls HubSpot for taxi requests, assigns a driver,
   sends SMS/email.
5. **`frontend`** (nginx) — serves the test page. Port `8080` on the host.

`token-api`, `agent-worker`, and `crm-worker` are built from the **same**
backend image; they just run different commands.

### PayU payments module (`app/payments/`)

This is the PayU billing worker, mounted directly into the FastAPI app
instead of running as its own standalone service. It keeps its own
settings class (`PayuWorkerSettings`, a plain dataclass reading from the
same root `.env`) so it doesn't need to touch the existing pydantic
`Settings` in `app/config.py`. Its SQLite bills DB lives at `data/payments.db`
(volume-mounted into both `token-api` and `crm-worker`, since both need
to read/write bills).

Key endpoints it adds:
- `POST /api/create-bill` — price + create a bill, returns a payment link
- `GET /pay/{order_id}` — guest-facing payment page (redirects to PayU)
- `POST /payment/success` / `/payment/failure` — PayU webhook callbacks
- `POST /api/refund`, `GET /api/payment-status/{txn_id}`
- `GET /health` — now reports PayU config status too (`payu_configured`, `issues`)

All `/api/*` payments routes require `X-API-Key: <PAYU_WORKER_API_KEY>`.
`/pay/*` and `/payment/*` are intentionally unauthenticated (guests and
PayU itself hit these).

**Not yet wired** (next step): `crm/worker.py` doesn't call
`BillGenerator.create_bill()` yet, and there's no price lookup or
SMS/email step for the payment link. See the "Order → Payment" TODO
below.

## 1. Configure

```bash
cp .env.example .env
```
Edit `.env` with your real LiveKit credentials and current RunPod pod ID.

**Important:** RunPod assigns a new pod ID every time you Stop/Start a
pod. If you restart your RunPod pod, update `UNMUTE_POD_ID` in `.env` and
run `docker compose up -d --build agent-worker` to pick up the change
(the token-api and frontend don't need rebuilding for this).

Also make sure Unmute itself (`start_all.sh`) is actually running on the
RunPod pod before testing — this project only bridges to it, it doesn't
run Unmute itself.

## 2. Run everything with one command

```bash
docker compose up --build
```

This builds all three images and starts them. First build will take a
few minutes (installing dependencies, possibly compiling `sphn` if no
prebuilt wheel matches your platform).

## 3. Test

Open **http://localhost:8080** in your browser, click **Connect & Talk**,
allow microphone access, and talk.

Watch the agent worker's logs in another terminal:
```bash
docker compose logs -f agent-worker
```
You should see `"registered worker"` at startup, then `"received job
request"` and `"Subscribed to audio from ..."` once you connect from the
browser — that second line confirms audio is actually flowing.

## 4. Stopping / restarting

```bash
docker compose down          # stop everything
docker compose up -d         # restart in the background
docker compose logs -f       # follow all logs
```

## Order → Payment wiring (not done yet)

The pieces below exist independently but aren't connected. This is the
next step:

1. `crm/extractor.py` gets a price for each item (either from
   `app/payments/service_catalog.py`'s menu, or your own source).
2. `crm/worker.py`, after `hubspot_client.push()`, calls
   `app.payments.BillGenerator.create_bill(...)` to get a `payment_link`.
3. Send that `payment_link` to the guest via SMS/email — reuse/generalize
   `taxi/taxi_worker.py`'s `send_confirmation_sms` / `send_confirmation_email`
   (MSG91 + SendGrid), which already work, just for taxi bookings only.
4. On `POST /payment/success`, update the HubSpot record's status to
   "paid" — `crm/hubspot_client.py` already has `build_payment_payload()`
   and `create_payment_schema()` stubbed for exactly this, unused so far.

## Fixed during this merge

- `docker-compose.yml` and `.gitignore` had **unresolved git merge-conflict
  markers** (`<<<<<<< HEAD` / `=======` / `>>>>>>>`) committed into them —
  both were broken files that would have failed to parse. Cleaned up.
- Two `/health` routes existed after mounting the payments router
  (FastAPI/Starlette matches routes in registration order, so the second
  one would have been silently unreachable). Kept the payments one since
  it reports more (`payu_configured`, config `issues`).
- `BASE_URL` in `.env` must now point at the merged app's actual address
  (`http://localhost:8081` locally) — not the PayU worker's old standalone
  port `9000`. This matters: it's baked into the payment page URL and the
  PayU webhook `surl`/`furl` callback URLs.
- `requirements.txt` merged with compatible version ranges
  (`fastapi>=0.115,<0.120`, `uvicorn[standard]>=0.30,<0.35`, plus PayU's
  `httpx` and `python-multipart`).

## Notes on going further to production

- **CORS**: `backend/app/main.py` currently allows all origins
  (`allow_origins=["*"]`). Lock this down to your real frontend's domain
  before deploying publicly.
- **HTTPS**: this setup uses plain HTTP for local/LAN testing. For a real
  public deployment, put the frontend and token-api behind a reverse
  proxy (nginx/Caddy/Traefik) with TLS certificates, and update
  `TOKEN_ENDPOINT` in `index.html` to the HTTPS URL.
- **Multiple concurrent calls**: this bridges to a single Unmute instance
  on RunPod. If you expect several simultaneous callers, revisit the STT
  `batch_size` setting on the RunPod side (see project history) and check
  GPU headroom accordingly — this repo's scaling limit is entirely on
  the RunPod/Unmute side, not in this bridge code.
- **Tool calling / function calling**: not yet implemented in this
  bridge or in Unmute's backend. This is a known next step, not present
  in this version.
