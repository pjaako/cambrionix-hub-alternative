let MODES = ['on', 'off'];
let modePending = false;

fetch('/api/modes').then(r => r.json()).then(m => { MODES = m; });

function fmt(seconds) {
    if (seconds == null) return '—';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
}

function renderPort(p) {
    const s = p.attached && p.mode === 'on' ? 'active'
            : p.attached                    ? 'standby'
            :                                 'idle';

    const metrics = p.attached ? `
        <div class="metrics">
          <div class="metric-cell"><span class="metric-key">V</span>
            <span class="metric-val">${p.voltage_v != null ? p.voltage_v.toFixed(1) : '—'}</span></div>
          <div class="metric-cell"><span class="metric-key">I&nbsp;&nbsp;mA</span>
            <span class="metric-val">${p.current_ma != null ? p.current_ma : '—'}</span></div>
          <div class="metric-cell"><span class="metric-key">T</span>
            <span class="metric-val">${fmt(p.charging_seconds)}</span></div>
        </div>` : `<div class="no-device">no device</div>`;

    const toggle = MODES.map(m => `
        <input type="radio" name="port-mode-${p.id}" id="md-${p.id}-${m}"
               value="${m}" ${m === p.mode ? 'checked' : ''}
               onchange="setMode(${p.id}, '${m}')">
        <label for="md-${p.id}-${m}" class="opt-${m}">${m}</label>`
    ).join('');

    return `
        <div class="port-card s-${s}">
          <div class="card-body">
            <div class="card-head">
              <span class="port-label">Port ${String(p.id).padStart(2,'0')}</span>
              <span class="led ${s !== 'idle' ? s : ''}"></span>
            </div>
            ${metrics}
            <div class="mode-toggle">${toggle}</div>
          </div>
        </div>`;
}

async function refresh() {
    if (modePending) return;
    try {
        const res = await fetch('/api/ports');
        if (!res.ok) throw new Error(res.statusText);
        document.getElementById('ports').innerHTML =
            (await res.json()).map(renderPort).join('');
        document.getElementById('error').textContent = '';
    } catch (e) {
        document.getElementById('error').textContent = e.message;
    }
}

async function setMode(portId, mode) {
    modePending = true;
    try {
        await fetch(`/api/ports/${portId}/mode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode }),
        });
    } catch (e) {
        document.getElementById('error').textContent = e.message;
    } finally {
        modePending = false;
        refresh();
    }
}

setInterval(refresh, 2000);
refresh();
