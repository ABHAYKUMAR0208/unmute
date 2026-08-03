"""
run_taxi_poller.py
===================
Entry point to run the HubSpot Taxi Poller standalone, as its own
long-running process/container — independent of the LiveKit agent-worker
and token-api services.

Usage:
  python -m app.run_taxi_poller

Or via Docker (see docker-compose.yml "taxi-worker" service):
  command: ["python", "-m", "app.run_taxi_poller"]
"""

import logging

from app.taxi.hubspot_taxi_poller import HubSpotTaxiPoller

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s — %(message)s",
    datefmt="%H:%M:%S",
)

if __name__ == "__main__":
    poller = HubSpotTaxiPoller()
    poller.run_forever()