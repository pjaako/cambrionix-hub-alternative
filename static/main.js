let modePending = false;

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
    const s = p.attached && p.mode === 'on' ? 'active'
            : p.attached                    ? 'standby'
            :                                 'idle';
    const powerW = p.attached && p.voltage_v != null && p.current_ma != null
        ? p.voltage_v * p.current_ma / 1000 : 0;
    const barPct = Math.min(powerW / 15 * 100, 100).toFixed(0);
    const namePrefix = `port-mode-${hubId}-${p.id}`;

    const toggle = modes.map(m => `
        <input type="radio" name="${namePrefix}" id="md-${hubId}-${p.id}-${m}"
               value="${m}" ${m === p.mode ? 'checked' : ''}
               onchange="setMode('${hubId}', ${p.id}, '${m}')">
        <label for="md-${hubId}-${p.id}-${m}" class="opt-${m}">${m}</label>`
    ).join('');

    return `<div class="row port-row s-${s}">
      <span class="col-port">${String(p.id).padStart(2, '0')}</span>
      <span class="col-led"><span class="led ${s !== 'idle' ? s : ''}"></span></span>
      <span class="col-v">${p.attached && p.voltage_v != null ? p.voltage_v.toFixed(1) : '—'}</span>
      <span class="col-i">${p.attached && p.current_ma != null ? p.current_ma : '—'}</span>
      <span class="col-pwr">${p.attached ? powerW.toFixed(1) : '—'}</span>
      <span class="col-time">${p.attached ? fmt(p.charging_seconds) : '—'}</span>
      <div class="col-bar">
        <div class="bar">
          <div class="bar-fill" style="width:${barPct}%"></div>
        </div>
      </div>
      <div class="col-mode"><div class="mode-toggle">${toggle}</div></div>
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
        <div class="row row-head">
          <span class="col-port">Port</span><span class="col-led"></span>
          <span class="col-v">V</span><span class="col-i">mA</span>
          <span class="col-pwr">W</span><span class="col-time">Time</span>
          <span class="col-bar"></span><span class="col-mode">Mode</span>
        </div>
        <div class="hub-ports-body">
          ${hub.ports.map(p => renderPort(p, hub.hub_id, hub.modes)).join('')}
        </div>
      </div>
    </details>`;
}

async function refresh() {
    if (modePending) return;
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
    modePending = true;
    try {
        await fetch(`/api/hubs/${hubId}/ports/${portId}/mode`, {
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
