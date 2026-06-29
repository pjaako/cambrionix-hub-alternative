from dataclasses import asdict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from hub_client import discover_hubs
from hub_backends import HubClient

app = FastAPI(title="Cambrionix Hub Monitor")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

hubs: list[HubClient] = discover_hubs()


class ModeRequest(BaseModel):
    mode: str


def _get_hub(hub_id: str) -> HubClient:
    for h in hubs:
        if h.hub_id == hub_id:
            return h
    raise HTTPException(status_code=404, detail=f"Hub {hub_id!r} not found")


def _hub_data(h: HubClient) -> dict:
    return {
        "hub_id": h.hub_id,
        "modes": h.supported_modes(),
        "ports": h.get_ports(),
    }


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"hubs": [_hub_data(h) for h in hubs]},
    )


@app.get("/api/hubs")
def api_hubs():
    return [
        {
            "hub_id": h.hub_id,
            "modes": h.supported_modes(),
            "ports": [asdict(p) for p in h.get_ports()],
        }
        for h in hubs
    ]


@app.post("/api/hubs/{hub_id}/ports/{port_id}/mode")
def api_set_mode(hub_id: str, port_id: int, body: ModeRequest):
    h = _get_hub(hub_id)
    valid = h.supported_modes()
    if body.mode not in valid:
        raise HTTPException(status_code=422, detail=f"mode must be one of {valid}")
    h.set_mode(port_id, body.mode)
    return {"mode": body.mode}
