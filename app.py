from dataclasses import asdict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from hub_client import discover_hubs

app = FastAPI(title="Cambrionix Hub Monitor")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class ModeRequest(BaseModel):
    mode: str


def _close_all(hubs: list) -> None:
    for h in hubs:
        if hasattr(h, "close"):
            h.close()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    hubs = discover_hubs()
    try:
        hubs_data = [
            {"hub_id": h.hub_id, "modes": h.supported_modes(), "ports": h.get_ports()}
            for h in hubs
        ]
    finally:
        _close_all(hubs)
    return templates.TemplateResponse(
        request=request, name="index.html", context={"hubs": hubs_data}
    )


@app.get("/api/hubs")
def api_hubs():
    hubs = discover_hubs()
    result = []
    for h in hubs:
        try:
            result.append({
                "hub_id": h.hub_id,
                "modes": h.supported_modes(),
                "ports": [asdict(p) for p in h.get_ports()],
                "error": None,
            })
        except Exception as e:
            result.append({
                "hub_id": h.hub_id,
                "modes": [],
                "ports": [],
                "error": str(e),
            })
        finally:
            if hasattr(h, "close"):
                h.close()
    return result


@app.post("/api/hubs/{hub_id}/ports/{port_id}/mode")
def api_set_mode(hub_id: str, port_id: int, body: ModeRequest):
    hubs = discover_hubs()
    try:
        hub = next((h for h in hubs if h.hub_id == hub_id), None)
        if hub is None:
            raise HTTPException(status_code=404, detail=f"Hub {hub_id!r} not found")
        valid = hub.supported_modes()
        if body.mode not in valid:
            raise HTTPException(status_code=422, detail=f"mode must be one of {valid}")
        hub.set_mode(port_id, body.mode)
    finally:
        _close_all(hubs)
    return {"mode": body.mode}
