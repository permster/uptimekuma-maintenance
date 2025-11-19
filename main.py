from uptime_kuma_api import UptimeKumaApi
from fastapi import FastAPI
from os import getenv, environ

UPTIME_KUMA_URL = getenv('UPTIME_KUMA_URL')
UPTIME_KUMA_USERNAME = getenv('UPTIME_KUMA_USERNAME')
UPTIME_KUMA_PASSWORD = getenv('UPTIME_KUMA_PASSWORD')

required_vars = ["UPTIME_KUMA_URL", "UPTIME_KUMA_USERNAME", "UPTIME_KUMA_PASSWORD"]
for var in required_vars:
    if not var in environ:
        print(f"Missing required environment variable: {var}")
        exit(1)

app = FastAPI()

try:
    api = UptimeKumaApi(UPTIME_KUMA_URL)
except:
    print("Unable to connect to Uptime Kuma")
    exit(1)

try:
    api.login(UPTIME_KUMA_USERNAME, UPTIME_KUMA_PASSWORD)
except:
    print("Unable to login to Uptime Kuma, check your credentials.")
    exit(1)

@app.get('/')
def index():
    return {"usage": ["/maintenance", "/maintenance/{m_id}", "/maintenance/{m_id}/pause", "/maintenance/{m_id}/resume", "/info"]}

@app.get('/info')
def info():
    return api.info()

@app.get('/maintenance')
def maint_list():
    return api.get_maintenances()

@app.get('/maintenance/{m_id}')
def maint_get(m_id: int):
    try:
        return api.get_maintenance(m_id)
    except:
        return {"error": "maintenance not found"}

@app.get('/maintenance/{m_id}/pause')
def maint_pause(m_id: int):
    try:
        return api.pause_maintenance(m_id)
    except:
        return {"error": "maintenance not found"}

@app.get('/maintenance/{m_id}/resume')
def maint_resume(m_id: int):
    try:
        return api.resume_maintenance(m_id)
    except:
        return {"error": "maintenance not found"}
