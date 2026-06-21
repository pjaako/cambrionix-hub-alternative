from dataclasses import asdict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from hub_client import CambrionixClient

app = FastAPI(title="Cambrionix Hub Monitor")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

hub = CambrionixClient()


class ModeRequest(BaseModel):
    mode: str


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    ports = hub.get_ports()
    modes = hub.supported_modes()
    hub_id = hub.hub_id()
    return templates.TemplateResponse(
        request=request, name="index.html", context={"ports": ports, "modes": modes, "hub_id": hub_id}
    )


@app.get("/api/ports")
def api_ports():
    return [asdict(p) for p in hub.get_ports()]


@app.get("/api/modes")
def api_modes():
    return hub.supported_modes()


@app.post("/api/ports/{port_id}/mode")
def api_set_mode(port_id: int, body: ModeRequest):
    valid = hub.supported_modes()
    if body.mode not in valid:
        raise HTTPException(status_code=422, detail=f"mode must be one of {valid}")
    hub.set_mode(port_id, body.mode)
    return asdict(hub.get_port(port_id))
