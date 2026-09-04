// 03-IA-ACTUALIZADOR-PROGRAMAS-WINDOWS - Frontend Logic

let currentTab = 'outdated';
let outdatedApps = [];
let installedApps = [];
let selectedAppIds = new Set();
let lastLogIndex = 0;
let pollTimer = null;
let isUpdatingOrScanning = false;

// Elementos DOM
const dom = {
  btnScan: document.getElementById('btn-scan'),
  btnUpgradeAll: document.getElementById('btn-upgrade-all'),
  btnUpgradeSelected: document.getElementById('btn-upgrade-selected'),
  selectedCount: document.getElementById('selected-count'),
  visibleCount: document.getElementById('visible-count'),
  selectAllCheckbox: document.getElementById('select-all-checkbox'),
  searchInput: document.getElementById('search-input'),
  clearSearch: document.getElementById('clear-search'),
  
  // Tabs
  tabOutdated: document.getElementById('tab-outdated'),
  tabInstalled: document.getElementById('tab-installed'),
  tabLogs: document.getElementById('tab-logs'),
  tabBadgeOutdated: document.getElementById('tab-badge-outdated'),
  tabBadgeInstalled: document.getElementById('tab-badge-installed'),
  
  // Vistas
  viewOutdated: document.getElementById('view-outdated'),
  viewInstalled: document.getElementById('view-installed'),
  viewLogs: document.getElementById('view-logs'),
  
  // Tablas
  outdatedTableBody: document.getElementById('outdated-table-body'),
  installedTableBody: document.getElementById('installed-table-body'),
  
  // KPIs
  statOutdated: document.getElementById('stat-outdated'),
  statInstalled: document.getElementById('stat-installed'),
  statStatusText: document.getElementById('stat-status-text'),
  statLastScan: document.getElementById('stat-last-scan'),
  
  // Progreso
  progressContainer: document.getElementById('progress-container'),
  progressText: document.getElementById('progress-text'),
  progressPercent: document.getElementById('progress-percent'),
  progressBarFill: document.getElementById('progress-bar-fill'),
  
  // Terminal
  terminalBody: document.getElementById('terminal-body'),
  autoscrollCheck: document.getElementById('autoscroll-check'),
  btnClearLogs: document.getElementById('btn-clear-logs'),
  
  toastContainer: document.getElementById('toast-container')
};

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  startPolling();
  refreshAllData();
});

function setupEventListeners() {
  // Pestañas
  dom.tabOutdated.addEventListener('click', () => switchTab('outdated'));
  dom.tabInstalled.addEventListener('click', () => switchTab('installed'));
  dom.tabLogs.addEventListener('click', () => switchTab('logs'));

  // Botón Escanear
  dom.btnScan.addEventListener('click', triggerScan);

  // Botón Actualizar Todo
  dom.btnUpgradeAll.addEventListener('click', triggerUpgradeAll);

  // Botón Actualizar Seleccionados
  dom.btnUpgradeSelected.addEventListener('click', triggerUpgradeSelected);

  // Búsqueda
  dom.searchInput.addEventListener('input', () => {
    dom.clearSearch.classList.toggle('hidden', !dom.searchInput.value);
    renderActiveTable();
  });

  dom.clearSearch.addEventListener('click', () => {
    dom.searchInput.value = '';
    dom.clearSearch.classList.add('hidden');
    renderActiveTable();
  });

  // Checkbox Seleccionar Todo
  dom.selectAllCheckbox.addEventListener('change', (e) => {
    const isChecked = e.target.checked;
    const filtered = getFilteredOutdated();
    filtered.forEach(app => {
      if (isChecked) {
        selectedAppIds.add(app.id);
      } else {
        selectedAppIds.delete(app.id);
      }
    });
    renderOutdatedTable();
    updateSelectionUI();
  });

  // Limpiar terminal
  dom.btnClearLogs.addEventListener('click', () => {
    dom.terminalBody.innerHTML = '<div class="log-entry log-info">[SISTEMA] Pantalla limpiada.</div>';
  });
}

function switchTab(tab) {
  currentTab = tab;
  dom.tabOutdated.classList.toggle('active', tab === 'outdated');
  dom.tabInstalled.classList.toggle('active', tab === 'installed');
  dom.tabLogs.classList.toggle('active', tab === 'logs');

  dom.viewOutdated.classList.toggle('hidden', tab !== 'outdated');
  dom.viewInstalled.classList.toggle('hidden', tab !== 'installed');
  dom.viewLogs.classList.toggle('hidden', tab !== 'logs');

  if (tab === 'installed' && installedApps.length === 0) {
    loadInstalledApps();
  }

  renderActiveTable();
}

function renderActiveTable() {
  if (currentTab === 'outdated') {
    renderOutdatedTable();
  } else if (currentTab === 'installed') {
    renderInstalledTable();
  }
}

// Carga de Datos y API
async function refreshAllData() {
  await Promise.all([
    checkStatus(),
    loadOutdatedApps(),
    loadInstalledApps()
  ]);
}

async function checkStatus() {
  try {
    const res = await fetch('/api/status');
    if (!res.ok) return;
    const status = await res.json();

    isUpdatingOrScanning = status.is_scanning || status.is_updating;

    // Actualizar KPIs
    dom.statOutdated.textContent = status.outdated_count;
    dom.tabBadgeOutdated.textContent = status.outdated_count;
    
    if (status.installed_count > 0) {
      dom.statInstalled.textContent = status.installed_count;
      dom.tabBadgeInstalled.textContent = status.installed_count;
    }

    dom.statStatusText.textContent = status.is_updating ? "Actualizando..." : (status.is_scanning ? "Escaneando..." : "Listo");
    dom.statStatusText.style.color = status.is_updating ? "#fbbf24" : (status.is_scanning ? "#38bdf8" : "#34d399");

    if (status.last_scan_time) {
      dom.statLastScan.textContent = `Última comprobación: ${status.last_scan_time}`;
    }

    // Botón Escanear animación
    const icon = dom.btnScan.querySelector('.icon-spin');
    if (icon) {
      icon.classList.toggle('spinning', status.is_scanning);
    }
    dom.btnScan.disabled = isUpdatingOrScanning;
    dom.btnUpgradeAll.disabled = status.is_updating || status.outdated_count === 0;

    // Barra de Progreso
    if (status.is_updating) {
      dom.progressContainer.classList.remove('hidden');
      dom.progressText.textContent = status.current_action;
      dom.progressPercent.textContent = `${status.progress_percent}%`;
      dom.progressBarFill.style.width = `${status.progress_percent}%`;
    } else {
      dom.progressContainer.classList.add('hidden');
    }

  } catch (err) {
    console.error("Error al obtener estado:", err);
  }
}

async function loadOutdatedApps() {
  try {
    const res = await fetch('/api/apps');
    if (!res.ok) return;
    const data = await res.json();
    outdatedApps = data;
    
    // Por defecto seleccionar todas las nuevas detectadas
    if (selectedAppIds.size === 0 && outdatedApps.length > 0) {
      outdatedApps.forEach(a => selectedAppIds.add(a.id));
    }
    
    dom.statOutdated.textContent = outdatedApps.length;
    dom.tabBadgeOutdated.textContent = outdatedApps.length;
    renderOutdatedTable();
    updateSelectionUI();
  } catch (err) {
    console.error("Error cargando apps pendientes:", err);
  }
}

async function loadInstalledApps() {
  try {
    const res = await fetch('/api/all-installed');
    if (!res.ok) return;
    const data = await res.json();
    if (data && data.length > 0) {
      installedApps = data;
      dom.statInstalled.textContent = installedApps.length;
      dom.tabBadgeInstalled.textContent = installedApps.length;
      renderInstalledTable();
    }
  } catch (err) {
    console.error("Error cargando todas las apps:", err);
  }
}

async function fetchLogs() {
  try {
    const res = await fetch(`/api/logs?since=${lastLogIndex}`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.logs && data.logs.length > 0) {
      data.logs.forEach(log => {
        const entry = document.createElement('div');
        entry.className = `log-entry log-${log.level || 'info'}`;
        entry.textContent = `[${log.time}] ${log.message}`;
        dom.terminalBody.appendChild(entry);
      });
      lastLogIndex = data.total;

      if (dom.autoscrollCheck.checked) {
        dom.terminalBody.scrollTop = dom.terminalBody.scrollHeight;
      }
    }
  } catch (err) {
    console.error("Error en logs:", err);
  }
}

// Búsqueda y Filtrado
function getFilteredOutdated() {
  const q = dom.searchInput.value.trim().toLowerCase();
  if (!q) return outdatedApps;
  return outdatedApps.filter(app => 
    (app.name && app.name.toLowerCase().includes(q)) ||
    (app.id && app.id.toLowerCase().includes(q))
  );
}

function getFilteredInstalled() {
  const q = dom.searchInput.value.trim().toLowerCase();
  if (!q) return installedApps;
  return installedApps.filter(app => 
    (app.name && app.name.toLowerCase().includes(q)) ||
    (app.id && app.id.toLowerCase().includes(q))
  );
}

// Renderizado de Tablas
function renderOutdatedTable() {
  const filtered = getFilteredOutdated();
  dom.visibleCount.textContent = filtered.length;

  if (filtered.length === 0) {
    if (outdatedApps.length === 0) {
      dom.outdatedTableBody.innerHTML = `
        <tr>
          <td colspan="7" class="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" style="margin: 0 auto 12px; display: block;">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
            <h3 style="color: #fff; margin-bottom: 6px;">¡Todo tu software está al día!</h3>
            <p style="color: #9ca3af;">No se encontraron actualizaciones pendientes en este momento.</p>
          </td>
        </tr>
      `;
    } else {
      dom.outdatedTableBody.innerHTML = `
        <tr>
          <td colspan="7" class="empty-state">
            <p>No se encontraron aplicaciones que coincidan con "<strong>${escapeHtml(dom.searchInput.value)}</strong>".</p>
          </td>
        </tr>
      `;
    }
    return;
  }

  let html = '';
  filtered.forEach((app, idx) => {
    const isChecked = selectedAppIds.has(app.id);
    const initial = app.name ? app.name.charAt(0).toUpperCase() : '?';

    html += `
      <tr data-id="${escapeHtml(app.id)}">
        <td>
          <label class="checkbox-container">
            <input type="checkbox" class="row-checkbox" data-id="${escapeHtml(app.id)}" ${isChecked ? 'checked' : ''}>
            <span class="checkmark"></span>
          </label>
        </td>
        <td>
          <div class="app-name-cell">
            <div class="app-avatar">${initial}</div>
            <span class="app-title-text">${escapeHtml(app.name)}</span>
          </div>
        </td>
        <td>
          <span class="app-id-tag">${escapeHtml(app.id)}</span>
        </td>
        <td>
          <span class="version-badge version-current">${escapeHtml(app.current_version || '--')}</span>
        </td>
        <td>
          <span class="version-badge version-new">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <line x1="12" y1="19" x2="12" y2="5"></line>
              <polyline points="5 12 12 5 19 12"></polyline>
            </svg>
            ${escapeHtml(app.available_version || 'Nueva')}
          </span>
        </td>
        <td>
          <span class="source-badge">${escapeHtml(app.source || 'winget')}</span>
        </td>
        <td class="text-right">
          <button class="btn-row-action btn-update-single" data-pkg-id="${escapeHtml(app.id)}" data-pkg-name="${escapeHtml(app.name)}">
            Actualizar
          </button>
        </td>
      </tr>
    `;
  });

  dom.outdatedTableBody.innerHTML = html;

  // Listeners a los checkboxes individuales
  dom.outdatedTableBody.querySelectorAll('.row-checkbox').forEach(cb => {
    cb.addEventListener('change', (e) => {
      const id = e.target.getAttribute('data-id');
      if (e.target.checked) {
        selectedAppIds.add(id);
      } else {
        selectedAppIds.delete(id);
      }
      updateSelectionUI();
    });
  });

  // Listeners a los botones individuales de actualización (sin inline onclick)
  dom.outdatedTableBody.querySelectorAll('.btn-update-single').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const pkgId = btn.getAttribute('data-pkg-id');
      const pkgName = btn.getAttribute('data-pkg-name');
      executeUpgradeSingle(pkgId, pkgName, btn);
    });
  });
}

function renderInstalledTable() {
  const filtered = getFilteredInstalled();

  if (filtered.length === 0) {
    dom.installedTableBody.innerHTML = `
      <tr>
        <td colspan="5" class="empty-state">
          <p>No se encontraron aplicaciones instaladas.</p>
        </td>
      </tr>
    `;
    return;
  }

  let html = '';
  filtered.forEach(app => {
    html += `
      <tr>
        <td>
          <div class="app-name-cell">
            <span class="app-title-text">${escapeHtml(app.name)}</span>
          </div>
        </td>
        <td><span class="app-id-tag">${escapeHtml(app.id)}</span></td>
        <td><span class="version-badge version-current">${escapeHtml(app.version || '--')}</span></td>
        <td><span class="version-badge">${escapeHtml(app.available || '-')}</span></td>
        <td><span class="source-badge">${escapeHtml(app.source || 'winget')}</span></td>
      </tr>
    `;
  });

  dom.installedTableBody.innerHTML = html;
}

function updateSelectionUI() {
  const count = selectedAppIds.size;
  dom.selectedCount.textContent = count;
  dom.btnUpgradeSelected.disabled = (count === 0) || isUpdatingOrScanning;

  const filtered = getFilteredOutdated();
  if (filtered.length === 0) {
    dom.selectAllCheckbox.checked = false;
    dom.selectAllCheckbox.indeterminate = false;
  } else {
    const visibleSelected = filtered.filter(a => selectedAppIds.has(a.id)).length;
    if (visibleSelected === filtered.length) {
      dom.selectAllCheckbox.checked = true;
      dom.selectAllCheckbox.indeterminate = false;
    } else if (visibleSelected > 0) {
      dom.selectAllCheckbox.checked = false;
      dom.selectAllCheckbox.indeterminate = true;
    } else {
      dom.selectAllCheckbox.checked = false;
      dom.selectAllCheckbox.indeterminate = false;
    }
  }
}

// Modal de Confirmación estilizado In-App
function showConfirmModal(title, message, onConfirm) {
  const modal = document.getElementById('confirm-modal');
  const modalTitle = document.getElementById('modal-title');
  const modalMsg = document.getElementById('modal-message');
  const btnCancel = document.getElementById('modal-btn-cancel');
  const btnConfirm = document.getElementById('modal-btn-confirm');

  modalTitle.textContent = title;
  modalMsg.textContent = message;
  modal.classList.remove('hidden');

  const cleanup = () => {
    modal.classList.add('hidden');
    btnConfirm.onclick = null;
    btnCancel.onclick = null;
  };

  btnCancel.onclick = cleanup;
  btnConfirm.onclick = () => {
    cleanup();
    if (typeof onConfirm === 'function') onConfirm();
  };
}

// Disparadores de Acciones
async function triggerScan() {
  try {
    showToast("Iniciando escaneo de actualizaciones...", "info");
    const res = await fetch('/api/scan', { method: 'POST' });
    const data = await res.json();
    if (res.ok) {
      checkStatus();
    } else {
      showToast(data.message, "warning");
    }
  } catch (err) {
    showToast("Error de conexión al escanear", "error");
  }
}

function triggerUpgradeAll() {
  showConfirmModal(
    "⚡ ¿Actualizar Todos los Programas?",
    `Se van a descargar e instalar en segundo plano las actualizaciones de los ${outdatedApps.length} programas pendientes.`,
    async () => {
      try {
        showToast("Iniciando actualización automática global...", "info");
        switchTab('logs');
        const res = await fetch('/api/upgrade-all', { method: 'POST' });
        const data = await res.json();
        if (!res.ok) {
          showToast(data.message, "warning");
        }
      } catch (err) {
        showToast("Error al iniciar actualización", "error");
      }
    }
  );
}

function triggerUpgradeSelected() {
  const ids = Array.from(selectedAppIds);
  if (ids.length === 0) {
    showToast("No has seleccionado ningún programa", "warning");
    return;
  }

  showConfirmModal(
    `¿Actualizar los ${ids.length} programas seleccionados?`,
    `Se actualizarán únicamente los ${ids.length} programas marcados con casilla.`,
    async () => {
      try {
        showToast(`Iniciando actualización de ${ids.length} programas...`, "info");
        switchTab('logs');
        const res = await fetch('/api/upgrade-selected', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ids: ids })
        });
        const data = await res.json();
        if (!res.ok) {
          showToast(data.message, "warning");
        }
      } catch (err) {
        showToast("Error al conectar con el servidor", "error");
      }
    }
  );
}

async function executeUpgradeSingle(id, name, buttonEl) {
  if (isUpdatingOrScanning) {
    showToast("Ya hay una tarea en ejecución. Espera a que finalice.", "warning");
    return;
  }

  if (buttonEl) {
    buttonEl.disabled = true;
    buttonEl.textContent = "Iniciando...";
  }

  showToast(`Actualizando "${name}"...`, "info");
  switchTab('logs');

  try {
    const res = await fetch('/api/upgrade-selected', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ids: [id] })
    });
    const data = await res.json();
    if (!res.ok) {
      showToast(data.message || "Error al actualizar", "warning");
      if (buttonEl) {
        buttonEl.disabled = false;
        buttonEl.textContent = "Actualizar";
      }
    }
  } catch (err) {
    showToast("Error de conexión al actualizar", "error");
    if (buttonEl) {
      buttonEl.disabled = false;
      buttonEl.textContent = "Actualizar";
    }
  }
}

// Polling de Estado y Logs
function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    await checkStatus();
    await fetchLogs();
    if (!isUpdatingOrScanning && outdatedApps.length === 0) {
      await loadOutdatedApps();
    }
  }, 1200);
}

// Toasts
function showToast(msg, type = "info") {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${escapeHtml(msg)}</span>`;
  dom.toastContainer.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
