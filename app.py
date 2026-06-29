from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from controller import HubController

app = FastAPI(title="Cambrionix Hub Monitor")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

hub = HubController()


class ModeRequest(BaseModel):
    mode: str


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    hubs_data = hub.get_hubs()
    return templates.TemplateResponse(
        request=request, name="index.html", context={"hubs": hubs_data}
    )


@app.get("/api/hubs")
def api_hubs():
    return hub.get_hubs()


@app.post("/api/hubs/{hub_id}/ports/{port_id}/mode")
def api_set_mode(hub_id: str, port_id: int, body: ModeRequest):
    hubs_snapshot = hub.get_hubs()
    hub_entry = next((h for h in hubs_snapshot if h["hub_id"] == hub_id), None)
    if hub_entry is None:
        raise HTTPException(status_code=404, detail=f"Hub {hub_id!r} not found")
    valid = hub_entry["modes"]
    if body.mode not in valid:
        raise HTTPException(status_code=422, detail=f"mode must be one of {valid}")
    try:
        hub.set_mode(hub_id, port_id, body.mode)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Hub {hub_id!r} not found")
    return {"mode": body.mode}
