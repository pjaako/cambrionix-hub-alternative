let pendingPorts = new Map(); // "hubId-portId" -> desiredMode

function fmt(seconds) {
    if (seconds == null) return '—';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
}

function renderPort(p, hubId, modes) {
    const key = `${hubId}-${p.id}`;
    const isPending = pendingPorts.has(key);
    const displayedMode = isPending ? pendingPorts.get(key) : p.mode;

    const s = isPending ? 'transition' : (p.attached && p.mode === 'on' ? 'active'
            : p.attached                    ? 'standby'
            :                                 'idle');
    const powerW = p.attached && p.voltage_v != null && p.current_ma != null
        ? p.voltage_v * p.current_ma / 1000 : 0;
    const namePrefix = `port-mode-${hubId}-${p.id}`;

    const toggle = modes.map(m => `
        <input type="radio" name="${namePrefix}" id="md-${hubId}-${p.id}-${m}"
               value="${m}" ${m === displayedMode ? 'checked' : ''}
               onchange="setMode('${hubId}', ${p.id}, '${m}')"
               ${isPending ? 'disabled' : ''}>
        <label for="md-${hubId}-${p.id}-${m}" class="opt-${m}">${m}</label>`
    ).join('');

    return `<div class="port-tile s-${s} ${isPending ? 'pending' : ''}">
      <div class="tile-head">
        <span class="led ${s !== 'idle' ? s : ''}"></span>
        <span class="tile-port">${String(p.id).padStart(2, '0')}</span>
        <span class="tile-status">${s}</span>
      </div>
      <div class="tile-stats">
        <div>
          <div class="tile-stat-label">V</div>
          <div class="tile-stat-value">${p.attached && !isPending && p.voltage_v != null ? p.voltage_v.toFixed(1) : '—'}</div>
        </div>
        <div>
          <div class="tile-stat-label">mA</div>
          <div class="tile-stat-value">${p.attached && !isPending && p.current_ma != null ? p.current_ma : '—'}</div>
        </div>
        <div>
          <div class="tile-stat-label">W</div>
          <div class="tile-stat-value">${p.attached && !isPending ? powerW.toFixed(1) : '—'}</div>
        </div>
        <div>
          <div class="tile-stat-label">Time</div>
          <div class="tile-stat-value">${p.attached && !isPending ? fmt(p.charging_seconds) : '—'}</div>
        </div>
      </div>
      <div class="mode-toggle">${toggle}</div>
    </div>`;
}

function renderHub(hub) {
    return `<details open class="hub-section" data-hub-id="${hub.hub_id}">
      <summary class="hub-header">
        <span class="hub-chevron">▼</span>
        <span class="hub-label">${hub.hub_id}</span>
        <span class="hub-meta">${hub.ports.length} ports · ${hub.modes.join(' / ')}</span>
      </summary>
      <div class="hub-ports">
        <div class="hub-ports-body">
          ${hub.ports.map(p => renderPort(p, hub.hub_id, hub.modes)).join('')}
        </div>
      </div>
    </details>`;
}

async function refresh() {
    try {
        const res = await fetch('/api/hubs');
        if (!res.ok) throw new Error(res.statusText);
        const hubs = await res.json();
        const container = document.getElementById('hubs-container');

        if (hubs.length === 0) {
            container.innerHTML = '<p class="no-hubs">No hubs detected. Check that the hub is connected and powered on.</p>';
        } else {
            container.querySelector('.no-hubs')?.remove();

            // update or create each hub section
            for (const hub of hubs) {
                // Clear pending ports that have reached their target state
                for (const p of hub.ports) {
                    const key = `${hub.hub_id}-${p.id}`;
                    if (pendingPorts.has(key) && pendingPorts.get(key) === p.mode) {
                        pendingPorts.delete(key);
                    }
                }

                let section = container.querySelector(`.hub-section[data-hub-id="${hub.hub_id}"]`);
                if (!section) {
                    container.insertAdjacentHTML('beforeend', renderHub(hub));
                } else {
                    section.querySelector('.hub-ports-body').innerHTML = hub.error
                        ? `<div class="hub-error">${hub.error}</div>`
                        : hub.ports.map(p => renderPort(p, hub.hub_id, hub.modes)).join('');
                }
            }

            // remove sections for hubs that disappeared
            const seen = new Set(hubs.map(h => h.hub_id));
            container.querySelectorAll('.hub-section').forEach(s => {
                if (!seen.has(s.dataset.hubId)) s.remove();
            });
        }

        document.getElementById('error').textContent = '';
    } catch (e) {
        document.getElementById('error').textContent = e.message;
    }
}

async function setMode(hubId, portId, mode) {
    const key = `${hubId}-${portId}`;
    pendingPorts.set(key, mode);
    
    // Immediate local UI refresh to show transition state
    const container = document.getElementById('hubs-container');
    const section = container.querySelector(`.hub-section[data-hub-id="${hubId}"]`);
    if (section) {
        refresh();
    }
    
    try {
        const res = await fetch(`/api/hubs/${hubId}/ports/${portId}/mode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode }),
        });
        if (!res.ok) throw new Error(await res.text());
    } catch (e) {
        document.getElementById('error').textContent = e.message;
        pendingPorts.delete(key);
        refresh();
    }
}

async function manualRefresh() {
    const btn = document.querySelector('.btn-refresh');
    btn.classList.add('loading');
    btn.textContent = 'Scanning...';
    try {
        const res = await fetch('/api/hubs/discover', { method: 'POST' });
        if (!res.ok) throw new Error(await res.text());
        // Wait a bit for discovery to complete before refreshing UI
        await new Promise(r => setTimeout(r, 1000));
        await refresh();
    } catch (e) {
        document.getElementById('error').textContent = e.message;
    } finally {
        btn.classList.remove('loading');
        btn.textContent = 'Refresh Hubs';
    }
}

setInterval(refresh, 2000);
refresh();
