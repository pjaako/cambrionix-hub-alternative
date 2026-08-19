let pendingPorts = new Map(); // "hubId-portId" -> {mode, at, via}
const BRICK_CYCLE_MS = 3200; // must match the brick1/2/3 keyframe durations in index.html
// Backstop for a port that never reaches its requested mode and whose failure
// the backend never reports. Must stay below _COMMAND_ERROR_TTL in controller.py
// so a tile cannot return to normal while its explanation is still on screen.
const PENDING_TTL_MS = 10000;

// Firmware error text is arbitrary, unlike the enum values everything else
// interpolates, so it gets escaped before going into an attribute.
function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, c => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
}

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
    if (seconds == null) return '';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m`;
    if (m > 0) return `${m}m ${s}s`;
    return `${s}s`;
}

function renderPort(p, hubId, modes) {
    const key = `${hubId}-${p.id}`;
    const pending = pendingPorts.get(key);
    const isPending = !!pending;
    const attached = p.attachment !== 'detached';
    const displayedMode = isPending ? pending.mode : writeMode(p.status);
    // Which control started the change. The target mode alone cannot say:
    // sync -> charge and off -> on both land on "on", so whichever button was
    // pressed records itself and is the one that shows the transition.
    const pendingVia = isPending ? pending.via : null;
    // Both computed server-side (controller.py) so this and the Jinja template
    // cannot drift. faulted = this port is broken (red); blocked = its control
    // is dead, which a hub-wide fault also causes without reddening the tile.
    const blocked = !!p.blocked;
    const faulted = !!p.faulted;

    const s = isPending ? 'transition'
            : p.status === 'off' ? 'off'
            : attached           ? 'active'
            :                      'idle';

    const isOn = displayedMode !== 'off';
    const btnClass = pendingVia === 'power'
        ? 'pwr-btn is-pending'
        : `pwr-btn ${isOn ? 'is-on' : ''}`;
    const toggle = `
        <button type="button" class="${btnClass}" ${isPending || blocked ? 'disabled' : ''}
                aria-label="${isOn ? 'Turn charging off' : 'Turn charging on'}" aria-pressed="${isOn}"
                onclick="togglePort('${hubId}', ${p.id}, '${displayedMode}')">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v8"/><path d="M18.4 6.6a8 8 0 1 1-12.8 0"/></svg>
        </button>`;

    // Sync toggle: only where the hub actually supports the mode, and only on
    // a live attached port - an off port reports no attachment, and flipping a
    // detached one has nothing to act on.
    const canSync = modes.includes('sync') && attached && p.status !== 'off';
    const inSync = displayedMode === 'sync';
    const syncToggle = canSync ? `
        <button type="button" class="sync-btn ${inSync ? 'is-sync' : ''} ${pendingVia === 'sync' ? 'is-pending' : ''}" ${isPending || blocked ? 'disabled' : ''}
                aria-label="${inSync ? 'Switch to charging' : 'Switch to sync'}" aria-pressed="${inSync}"
                title="${inSync ? 'Sync mode - click to charge' : 'Charge mode - click to sync'}"
                onclick="toggleSync('${hubId}', ${p.id}, '${displayedMode}')">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="20" r="2.1" fill="currentColor" stroke="none"/>
            <path d="M12 18V6.6"/>
            <path d="M12 3.2 15 8.4H9z" fill="currentColor" stroke="none"/>
            <path d="M12 14.6 8.4 11"/>
            <circle cx="7.2" cy="9.8" r="2.1" fill="currentColor" stroke="none"/>
            <path d="M12 16.4 15.9 12.5"/>
            <rect x="14.6" y="9.6" width="4" height="4" rx="0.5" fill="currentColor" stroke="none"/>
          </svg>
        </button>` : '';

    const isOff = p.status === 'off';
    const attachIcon = isOff ? '' : `
        <svg class="icon-attach ${attached ? 'is-attached' : ''}" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-label="${attached ? 'Attached' : 'Detached'}"><title>${attached ? 'Attached' : 'Detached'}</title>
          <path d="M7 9H5v6h2"/>
          <path d="M17 9h2v6h-2"/>
          ${attached ? '<rect x="9" y="10" width="6" height="4" rx="1" fill="currentColor" stroke="none"/>' : ''}
        </svg>`;
    // Polling replaces this element every 2s, well inside the 3.2s brick
    // cycle, so a plain animation would restart at 0% each time and never
    // reach the "all three lit" state. Sync the phase to wall-clock time
    // instead, so a fresh element resumes mid-cycle rather than restarting.
    const battery = (isOff || !attached) ? '' : `
      <div class="tile-battery st-${p.status}" style="--phase: -${Date.now() % BRICK_CYCLE_MS}ms">
        <div class="battery-nub"></div>
        <div class="battery-body">
          <span class="brick brick-1"></span>
          <span class="brick brick-2"></span>
          <span class="brick brick-3"></span>
        </div>
      </div>`;

    // FAULT distinguishes a dead port (firmware `e`: will not detect or charge)
    // from a hub-wide condition, which reads ERROR.
    const badgeLabel = p.command_error && p.command_error.code
        ? 'E' + esc(p.command_error.code)
        : p.port_error ? 'FAULT' : 'ERROR';
    const errorBadge = faulted
        ? `<span class="tile-error" title="${esc(p.error_detail)}">${badgeLabel}</span>`
        : '';

    // Keep this markup in sync with the port-tile loop in templates/index.html.
    return `<div class="port-tile s-${s} ${attached ? '' : 'unattached'} ${isPending ? 'pending' : ''} ${faulted ? 'has-error' : ''}">
      ${battery}
      <div class="tile-body">
        <div class="tile-head">
          ${attachIcon}
          <span class="tile-port">${String(p.id).padStart(2, '0')}</span>
        </div>
        <div class="tile-stats">
          <div class="tile-stat-value">${attached && !isPending && p.voltage_mv != null ? p.voltage_mv + ' mV' : ''}</div>
          <div class="tile-stat-value">${attached && !isPending ? p.current_ma + ' mA' : ''}</div>
          <div class="tile-stat-value">${attached && !isPending ? p.energy_mwh + ' mWh' : ''}</div>
          <div class="tile-stat-value">${attached && !isPending ? fmt(p.charging_seconds) : ''}</div>
        </div>
        <div class="tile-foot">
          ${errorBadge}
          ${syncToggle}
          <span class="tile-status st-${p.status}">
            <span class="tile-status-label">${p.status}</span>
          </span>
          ${toggle}
        </div>
      </div>
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
        <span class="hub-error-detail"></span>
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
                // Release pending ports. Three independent escapes, because a
                // port that only cleared on reaching its target would stay
                // disabled forever the moment a command was refused.
                for (const p of hub.ports) {
                    const key = `${hub.hub_id}-${p.id}`;
                    const pending = pendingPorts.get(key);
                    if (!pending) continue;
                    if (pending.mode === writeMode(p.status)) {
                        pendingPorts.delete(key);          // reached its target
                    } else if (p.command_error || p.blocked) {
                        pendingPorts.delete(key);          // refused or blocked
                    } else if (Date.now() - pending.at > PENDING_TTL_MS) {
                        pendingPorts.delete(key);          // never reported either way
                    }
                }
                if (hub.command_error || hub.error) {
                    for (const p of hub.ports) pendingPorts.delete(`${hub.hub_id}-${p.id}`);
                }

                let section = container.querySelector(`.hub-section[data-hub-id="${hub.hub_id}"]`);
                if (!section) {
                    container.insertAdjacentHTML('beforeend', renderHub(hub));
                    section = container.querySelector(`.hub-section[data-hub-id="${hub.hub_id}"]`);
                } else {
                    // A failing hub keeps its tiles rendered from the last known
                    // ports the backend retained, rather than being blanked.
                    section.querySelector('.hub-ports-body').innerHTML =
                        hub.ports.map(p => renderPort(p, hub.hub_id, hub.modes)).join('');
                }
                updateHubChrome(section, hub);
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

function togglePort(hubId, portId, currentMode) {
    setMode(hubId, portId, currentMode === 'off' ? 'on' : 'off', 'power');
}

// Flips the data path only. The power button keeps owning on/off, so the two
// controls never fight over the same transition.
function toggleSync(hubId, portId, currentMode) {
    setMode(hubId, portId, currentMode === 'sync' ? 'on' : 'sync', 'sync');
}

async function setMode(hubId, portId, mode, via = 'power') {
    const key = `${hubId}-${portId}`;
    pendingPorts.set(key, { mode, at: Date.now(), via });
    
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

// Hub-level state lives on the header, which renderHub() only ever builds for
// a brand new section - existing sections have just their ports body replaced.
// Both paths call this so the header never goes stale.
function updateHubChrome(section, hub) {
    if (!section) return;
    section.classList.toggle('has-error', !!hub.blocked);
    section.classList.toggle('is-stale', !!hub.stale);
    // The detail ellipsises in a narrow header, so the full text has to stay
    // reachable on hover.
    const detail = section.querySelector('.hub-error-detail');
    detail.textContent = hub.error_detail || '';
    detail.title = hub.error_detail || '';
    section.querySelector('.hub-lock-toggle').disabled = !!hub.blocked;
    if (hub.blocked) {
        const wrap = section.querySelector('.hub-mode-toggle-wrap');
        wrap.classList.remove('unlocked');
        wrap.querySelectorAll('.hub-mode-toggle button').forEach(b => b.disabled = true);
    }
}

function unlockHubToggle(unlockBtn) {
    if (unlockBtn.closest('.hub-section').classList.contains('has-error')) return;
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
