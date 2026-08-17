let pendingPorts = new Map(); // "hubId-portId" -> desiredMode

// Derive the write-vocabulary mode (on/off/sync/biased) a status corresponds to,
// for comparing against the mode-toggle buttons.
function writeMode(status) {
    return (status === 'off' || status === 'sync' || status === 'biased') ? status : 'on';
}

// Reorder/relabel raw mode values for display: "biased" is hidden (not
// meaningful to end users), and the remaining values get intuitive names.
function displayModes(modes) {
    const hasSync = modes.includes('sync');
    const order = hasSync ? ['off', 'sync', 'on'] : ['off', 'on'];
    const labels = hasSync
        ? { off: 'off', sync: 'data', on: 'power' }
        : { off: 'off', on: 'data+power' };
    return order.filter(m => modes.includes(m)).map(m => ({ value: m, label: labels[m] }));
}

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
    const attached = p.attachment !== 'detached';
    const displayedMode = isPending ? pendingPorts.get(key) : writeMode(p.status);

    const s = isPending ? 'transition'
            : p.status === 'off' ? 'off'
            : attached           ? 'active'
            :                      'idle';
    const namePrefix = `port-mode-${hubId}-${p.id}`;

    const toggle = displayModes(modes).map(({ value: m, label }) => `
        <input type="radio" name="${namePrefix}" id="md-${hubId}-${p.id}-${m}"
               value="${m}" ${m === displayedMode ? 'checked' : ''}
               onchange="setMode('${hubId}', ${p.id}, '${m}')"
               ${isPending ? 'disabled' : ''}>
        <label for="md-${hubId}-${p.id}-${m}" class="opt-${m}">${label}</label>`
    ).join('');

    return `<div class="port-tile s-${s} ${isPending ? 'pending' : ''}">
      <div class="tile-head">
        <span class="tile-port">${String(p.id).padStart(2, '0')}</span>
        <span class="tile-status">${p.attachment} · ${p.status}</span>
      </div>
      <div class="tile-stats">
        <div>
          <div class="tile-stat-label">V</div>
          <div class="tile-stat-value">${attached && !isPending && p.voltage_mv != null ? (p.voltage_mv / 1000).toFixed(1) : '—'}</div>
        </div>
        <div>
          <div class="tile-stat-label">mA</div>
          <div class="tile-stat-value">${attached && !isPending && p.current_ma != null ? p.current_ma : '—'}</div>
        </div>
        <div>
          <div class="tile-stat-label">Wh</div>
          <div class="tile-stat-value">${attached && !isPending && p.energy_mwh != null ? (p.energy_mwh / 1000).toFixed(2) : '—'}</div>
        </div>
        <div>
          <div class="tile-stat-label">Time</div>
          <div class="tile-stat-value">${attached && !isPending ? fmt(p.charging_seconds) : '—'}</div>
        </div>
      </div>
      <div class="mode-toggle">${toggle}</div>
    </div>`;
}

function renderHub(hub) {
    const hubToggle = displayModes(hub.modes).map(({ value: m, label }) => `
        <button type="button" disabled onclick="event.stopPropagation(); setHubMode('${hub.hub_id}', '${m}'); relockHubToggle(this)">${label}</button>`
    ).join('');

    return `<details open class="hub-section" data-hub-id="${hub.hub_id}">
      <summary class="hub-header">
        <span class="hub-chevron">▼</span>
        <span class="hub-label">${hub.hub_id}</span>
        <div class="hub-mode-toggle-wrap">
          <div class="hub-mode-toggle">${hubToggle}</div>
          <button type="button" class="hub-lock-toggle" title="Unlock hub-wide controls" onclick="event.stopPropagation(); unlockHubToggle(this)">
            <svg class="icon-locked" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>
            <svg class="icon-unlocked" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 7.75-1.5"/></svg>
          </button>
        </div>
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
                    if (pendingPorts.has(key) && pendingPorts.get(key) === writeMode(p.status)) {
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

            // Keep sections in the order the backend returned them (alphabetical
            // by hub_id); appendChild moves an existing node rather than copying it.
            for (const hub of hubs) {
                container.appendChild(container.querySelector(`.hub-section[data-hub-id="${hub.hub_id}"]`));
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

function unlockHubToggle(unlockBtn) {
    const wrap = unlockBtn.closest('.hub-mode-toggle-wrap');
    wrap.classList.add('unlocked');
    wrap.querySelectorAll('.hub-mode-toggle button').forEach(b => b.disabled = false);
}

function relockHubToggle(clickedBtn) {
    const wrap = clickedBtn.closest('.hub-mode-toggle-wrap');
    wrap.classList.remove('unlocked');
    wrap.querySelectorAll('.hub-mode-toggle button').forEach(b => b.disabled = true);
}

async function setHubMode(hubId, mode) {
    try {
        const res = await fetch(`/api/hubs/${hubId}/ports/mode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode }),
        });
        if (!res.ok) throw new Error(await res.text());
        refresh();
    } catch (e) {
        document.getElementById('error').textContent = e.message;
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
