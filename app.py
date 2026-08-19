import logging
import os
import sys

from fastapi import FastAPI, Request, HTTPException

# Configure logging if debug is requested (works when imported by uvicorn)
if "--debug" in sys.argv or os.environ.get("CAMBRIONIX_DEBUG"):
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
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
    hubs_data = sorted(hub.get_hubs(), key=lambda h: h["hub_id"])
    return templates.TemplateResponse(
        request=request, name="index.html", context={"hubs": hubs_data}
    )


@app.get("/api/hubs")
def api_hubs():
    return sorted(hub.get_hubs(), key=lambda h: h["hub_id"])


@app.post("/api/hubs/discover", status_code=202)
def api_discover():
    hub.discover()
    return {"status": "accepted", "action": "discover"}


@app.post("/api/hubs/{hub_id}/ports/{port_id}/mode", status_code=202)
def api_set_mode(hub_id: str, port_id: int, body: ModeRequest):
    hubs_snapshot = hub.get_hubs()
    hub_entry = next((h for h in hubs_snapshot if h["hub_id"] == hub_id), None)
    if hub_entry is None:
        raise HTTPException(status_code=404, detail=f"Hub {hub_id!r} not found")
    valid = hub_entry["modes"]
    if body.mode not in valid:
        raise HTTPException(status_code=422, detail=f"mode must be one of {valid}")
    hub.set_mode(hub_id, port_id, body.mode)
    return {"status": "accepted", "hub_id": hub_id, "port_id": port_id, "mode": body.mode}


@app.post("/api/hubs/{hub_id}/ports/mode", status_code=202)
def api_set_hub_mode(hub_id: str, body: ModeRequest):
    hubs_snapshot = hub.get_hubs()
    hub_entry = next((h for h in hubs_snapshot if h["hub_id"] == hub_id), None)
    if hub_entry is None:
        raise HTTPException(status_code=404, detail=f"Hub {hub_id!r} not found")
    valid = hub_entry["modes"]
    if body.mode not in valid:
        raise HTTPException(status_code=422, detail=f"mode must be one of {valid}")
    hub.set_mode_all(hub_id, body.mode)
    return {"status": "accepted", "hub_id": hub_id, "mode": body.mode}


# Simulated faults for checking the error UI without waiting for hardware to
# fail. Registered only when CAMBRIONIX_DEV_TOOLS is set, so in a normal run the
# route is absent from the app and from /docs entirely - not merely refused.
# Deliberately a different variable from CAMBRIONIX_DEBUG: turning on debug
# logging must never open a mutation endpoint.
if os.environ.get("CAMBRIONIX_DEV_TOOLS"):

    class InjectErrorRequest(BaseModel):
        # Which hub, or every known hub when omitted.
        hub_id: str | None = None
        # Which port, or hub-wide when omitted.
        port_id: int | None = None
        # command   - simulate a refused set_mode (an event, expires on the TTL)
        # port_flag - simulate the firmware E flag (polled, persists)
        # health    - simulate hub health flags such as UV/OV/OT
        # poll      - simulate the hub failing to poll
        kind: str = "command"
        code: str | None = "422"
        message: str = "*E422: Refused: an error flag is set"
        flags: list[str] = ["UV"]
        mode: str = "on"
        clear: bool = False

    logging.getLogger(__name__).warning(
        "CAMBRIONIX_DEV_TOOLS is set - POST /api/debug/inject-error is exposed"
    )

    @app.post("/api/debug/inject-error", status_code=202)
    def api_inject_error(body: InjectErrorRequest):
        known = {h["hub_id"] for h in hub.get_hubs()}
        if body.hub_id is not None and body.hub_id not in known:
            raise HTTPException(status_code=404, detail=f"Hub {body.hub_id!r} not found")
        hub.inject_error(body.model_dump())
        return {"status": "accepted", **body.model_dump()}


if __name__ == "__main__":
    import uvicorn
    
    # Remove --debug from sys.argv so uvicorn doesn't choke on it
    if "--debug" in sys.argv:
        sys.argv.remove("--debug")
            
    uvicorn.run(app, host="0.0.0.0", port=8000)
