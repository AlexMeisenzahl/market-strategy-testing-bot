/**
 * Phase 9B: Real-Time Update Contract
 *
 * Single source of truth for dashboard liveness:
 * - Explicit polling intervals (default 3s for mission/system, 5s for panels)
 * - Per-panel "Last Updated" timestamps
 * - Stale indicators when data has not refreshed within threshold
 * - Global heartbeat synced to engine state
 *
 * The UI must never appear static while the engine is running.
 */

(function () {
  'use strict';

  const CONTRACT = {
    /** Polling: mission bar + system status (fast to show "is it running?") */
    POLL_SYSTEM_MS: 3000,
    /** Polling: overview panels (trades, strategies, overview metrics) */
    POLL_PANELS_MS: 5000,
    /** Data is considered stale after this many seconds */
    STALE_THRESHOLD_SEC: 30,
    /** Heartbeat is stale after this many seconds */
    HEARTBEAT_STALE_SEC: 60,
    /** Max chart points to keep UI responsive */
    CHART_MAX_POINTS: 200,
    /** Max table rows before pagination/virtualization */
    TABLE_PAGE_SIZE: 25,
    TABLE_MAX_ROWS: 100,
  };

  /** Per-panel last successful update time (ISO string or null) */
  const panelLastUpdated = {};

  /** Last engine heartbeat from server (ISO string or null) */
  let lastHeartbeat = null;

  /** Whether we have received at least one successful system response */
  let systemEverLoaded = false;

  function nowISO() {
    return new Date().toISOString();
  }

  function setPanelUpdated(panelId) {
    if (panelId) panelLastUpdated[panelId] = nowISO();
  }

  function getPanelUpdated(panelId) {
    return panelId ? panelLastUpdated[panelId] || null : null;
  }

  function setHeartbeat(isoString) {
    lastHeartbeat = isoString || null;
    if (isoString) systemEverLoaded = true;
  }

  function getHeartbeat() {
    return lastHeartbeat;
  }

  function getHeartbeatAgeSeconds() {
    if (!lastHeartbeat) return null;
    return Math.floor((Date.now() - new Date(lastHeartbeat).getTime()) / 1000);
  }

  function isHeartbeatStale() {
    const age = getHeartbeatAgeSeconds();
    return age != null && age > CONTRACT.HEARTBEAT_STALE_SEC;
  }

  function getStaleThresholdSec() {
    return CONTRACT.STALE_THRESHOLD_SEC;
  }

  function isPanelStale(panelId) {
    const ts = getPanelUpdated(panelId);
    if (!ts) return true;
    const ageSec = Math.floor((Date.now() - new Date(ts).getTime()) / 1000);
    return ageSec > CONTRACT.STALE_THRESHOLD_SEC;
  }

  function formatRelativeTime(isoString) {
    if (!isoString) return '—';
    const d = new Date(isoString);
    const ageSec = Math.floor((Date.now() - d.getTime()) / 1000);
    if (ageSec < 60) return ageSec + 's ago';
    if (ageSec < 3600) return Math.floor(ageSec / 60) + 'm ago';
    if (ageSec < 86400) return Math.floor(ageSec / 3600) + 'h ago';
    return Math.floor(ageSec / 86400) + 'd ago';
  }

  function formatTimeOnly(isoString) {
    if (!isoString) return '—';
    return new Date(isoString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  /** Update DOM: global heartbeat indicator and stale state */
  function updateHeartbeatUI() {
    const el = document.getElementById('dash-heartbeat');
    const staleEl = document.getElementById('dash-heartbeat-stale');
    const age = getHeartbeatAgeSeconds();
    if (el) {
      if (lastHeartbeat) {
        el.textContent = 'Heartbeat: ' + formatTimeOnly(lastHeartbeat) + ' (' + (age != null ? age + 's ago' : '') + ')';
        el.classList.remove('dash-stale');
        if (staleEl) staleEl.classList.add('hidden');
      } else {
        el.textContent = 'Heartbeat: —';
        if (staleEl) staleEl.classList.add('hidden');
      }
    }
    if (staleEl && age != null && age > CONTRACT.HEARTBEAT_STALE_SEC) {
      el && el.classList.add('dash-stale');
      staleEl.classList.remove('hidden');
    }
  }

  /** Mark a panel's "Last updated" element and stale state */
  function updatePanelTimestampUI(panelId, timestampElId, staleClassContainerId) {
    const ts = getPanelUpdated(panelId);
    const timestampEl = timestampElId ? document.getElementById(timestampElId) : null;
    const container = staleClassContainerId ? document.getElementById(staleClassContainerId) : null;
    if (timestampEl) {
      timestampEl.textContent = ts ? formatRelativeTime(ts) : '—';
      timestampEl.setAttribute('title', ts ? 'Last updated: ' + new Date(ts).toLocaleString() : '');
    }
    if (container) {
      if (isPanelStale(panelId)) container.classList.add('dash-panel-stale');
      else container.classList.remove('dash-panel-stale');
    }
  }

  /** Cap array for charts (avoid unbounded render) */
  function capChartData(dataArray, maxPoints) {
    const max = maxPoints != null ? maxPoints : CONTRACT.CHART_MAX_POINTS;
    if (!Array.isArray(dataArray) || dataArray.length <= max) return dataArray;
    return dataArray.slice(-max);
  }

  window.RealtimeContract = {
    CONTRACT,
    setPanelUpdated,
    getPanelUpdated,
    setHeartbeat,
    getHeartbeat,
    getHeartbeatAgeSeconds,
    isHeartbeatStale,
    isPanelStale,
    getStaleThresholdSec,
    formatRelativeTime,
    formatTimeOnly,
    updateHeartbeatUI,
    updatePanelTimestampUI,
    capChartData,
    systemEverLoaded: function () { return systemEverLoaded; },
  };

  setInterval(updateHeartbeatUI, 1000);
})();
