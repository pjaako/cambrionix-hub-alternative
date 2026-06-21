let MODES = ['on', 'off'];

fetch('/api/modes').then(r => r.json()).then(m => { MODES = m; });

function formatTime(seconds) {
    if (seconds == null) return '—';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
}

function renderPort(p) {
    const modeOptions = MODES.map(m =>
        `<option value="${m}" ${m === p.mode ? 'selected' : ''}>${m}</option>`
    ).join('');

    const metrics = p.attached ? `
        <div class="metrics">
            <span class="metric"><span class="label">V</span> ${p.voltage_v != null ? p.voltage_v.toFixed(2) + ' V' : '—'}</span>
            <span class="metric"><span class="label">I</span> ${p.current_ma != null ? p.current_ma + ' mA' : '—'}</span>
            <span class="metric"><span class="label">T</span> ${formatTime(p.charging_seconds)}</span>
        </div>` : `<div class="metrics idle">No device attached</div>`;

    return `
        <div class="port-card ${p.attached ? 'attached' : 'idle'}">
            <div class="port-header">
                <span class="port-id">Port ${p.id}</span>
                <span class="mode-badge">${p.mode}</span>
            </div>
            ${metrics}
            <div class="mode-control">
                <select id="mode-${p.id}">${modeOptions}</select>
                <button onclick="setMode(${p.id})">Set</button>
            </div>
        </div>`;
}

function renderPorts(ports) {
    document.getElementById('ports').innerHTML = ports.map(renderPort).join('');
}

async function refresh() {
    try {
        const res = await fetch('/api/ports');
        if (!res.ok) throw new Error(res.statusText);
        renderPorts(await res.json());
    } catch (e) {
        document.getElementById('status').textContent = `Error: ${e.message}`;
    }
}

async function setMode(portId) {
    const mode = document.getElementById(`mode-${portId}`).value;
    try {
        await fetch(`/api/ports/${portId}/mode`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({mode}),
        });
        refresh();
    } catch (e) {
        document.getElementById('status').textContent = `Error: ${e.message}`;
    }
}

setInterval(refresh, 2000);
refresh();
