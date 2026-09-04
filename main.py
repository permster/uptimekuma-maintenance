import logging
import threading
from os import environ, getenv

import pyotp
from fastapi import FastAPI
from uptime_kuma_api import UptimeKumaApi

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("uptimekuma-maintenance")

UPTIME_KUMA_URL = getenv('UPTIME_KUMA_URL')
UPTIME_KUMA_USERNAME = getenv('UPTIME_KUMA_USERNAME')
UPTIME_KUMA_PASSWORD = getenv('UPTIME_KUMA_PASSWORD')
UPTIME_KUMA_2FA_SECRET = getenv('UPTIME_KUMA_2FA_SECRET') or None

required_vars = ["UPTIME_KUMA_URL", "UPTIME_KUMA_USERNAME", "UPTIME_KUMA_PASSWORD"]
for var in required_vars:
    if var not in environ:
        print(f"Missing required environment variable: {var}")
        exit(1)

app = FastAPI()

# Guards reconnects so two concurrent requests can't both try to rebuild
# the client at the same time.
_api_lock = threading.Lock()
api: UptimeKumaApi = None


def _login(client: UptimeKumaApi) -> None:
    """Log in, then complete 2FA if a secret is configured. Raises on failure."""
    client.login(UPTIME_KUMA_USERNAME, UPTIME_KUMA_PASSWORD)

    if UPTIME_KUMA_2FA_SECRET:
        totp = pyotp.TOTP(UPTIME_KUMA_2FA_SECRET)
        client.login(UPTIME_KUMA_USERNAME, UPTIME_KUMA_PASSWORD, totp.now())


def _connect() -> UptimeKumaApi:
    """Build a brand-new client and log in - equivalent to what a container restart does."""
    client = UptimeKumaApi(UPTIME_KUMA_URL)
    _login(client)
    return client


try:
    api = _connect()
except Exception as e:
    print(f"Unable to connect/login to Uptime Kuma: {type(e).__name__}: {e}")
    exit(1)


def _reconnect() -> None:
    """Tear down and rebuild the websocket session to Uptime Kuma."""
    global api
    logger.warning("Reconnecting to Uptime Kuma...")
    try:
        if api is not None:
            api.disconnect()
    except Exception:
        pass  # connection was already dead, nothing to clean up
    api = _connect()
    logger.info("Reconnected to Uptime Kuma.")


def call_kuma(fn):
    """
    Run a call against the Uptime Kuma client.

    If it fails, the persistent websocket session may have gone stale
    (this is what actually happened: nothing in the code was wrong, the
    session had died and only a container restart fixed it). So on any
    failure we rebuild the connection once and retry automatically,
    instead of just reporting an error.

    If it still fails after that, we return the REAL exception instead
    of a hardcoded "maintenance not found" - that message was previously
    shown for every possible failure (auth expired, timeout, connection
    drop, or an actual missing maintenance), which made this kind of
    issue impossible to diagnose from the response alone.
    """
    try:
        return fn(), None
    except Exception as first_error:
        logger.warning(f"Kuma call failed: {type(first_error).__name__}: {first_error} - attempting reconnect")
        with _api_lock:
            try:
                _reconnect()
            except Exception as reconnect_error:
                logger.error(f"Reconnect failed: {type(reconnect_error).__name__}: {reconnect_error}")
                return None, (
                    f"{type(first_error).__name__}: {first_error} "
                    f"(reconnect also failed: {type(reconnect_error).__name__}: {reconnect_error})"
                )

        try:
            return fn(), None
        except Exception as second_error:
            logger.error(f"Kuma call failed again after reconnect: {type(second_error).__name__}: {second_error}")
            return None, f"{type(second_error).__name__}: {second_error}"


@app.get('/')
def index():
    return {"usage": ["/maintenance", "/maintenance/{m_id}", "/maintenance/{m_id}/pause", "/maintenance/{m_id}/resume", "/info"]}


@app.get('/info')
def info():
    result, error = call_kuma(lambda: api.info())
    if error:
        return {"error": error}
    return result


@app.get('/maintenance')
def maint_list():
    result, error = call_kuma(lambda: api.get_maintenances())
    if error:
        return {"error": error}
    return result


@app.get('/maintenance/{m_id}')
def maint_get(m_id: int):
    result, error = call_kuma(lambda: api.get_maintenance(m_id))
    if error:
        return {"error": error}
    return result


@app.get('/maintenance/{m_id}/pause')
def maint_pause(m_id: int):
    result, error = call_kuma(lambda: api.pause_maintenance(m_id))
    if error:
        return {"error": error}
    return result


@app.get('/maintenance/{m_id}/resume')
def maint_resume(m_id: int):
    result, error = call_kuma(lambda: api.resume_maintenance(m_id))
    if error:
        return {"error": error}
    return result
