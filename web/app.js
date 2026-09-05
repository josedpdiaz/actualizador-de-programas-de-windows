// 03-IA-ACTUALIZADOR-PROGRAMAS-WINDOWS - Frontend Logic

let currentTab = 'outdated';
let outdatedApps = [];
let installedApps = [];
let selectedAppIds = new Set();
let knownUpdatedIds = new Set();
let knownUninstalledIds = new Set();
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
    if (!res.ok) return null;
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

    // Procesar programas recién actualizados en tiempo real
    if (status.updated_ids && status.updated_ids.length > 0) {
      status.updated_ids.forEach(pkgId => {
        const lowerId = pkgId.toLowerCase();
        if (!knownUpdatedIds.has(lowerId)) {
          knownUpdatedIds.add(lowerId);
          animateAndRemoveUpdatedApp(pkgId);
        }
      });
    }

    // Procesar programas recién desinstalados en tiempo real
    if (status.uninstalled_ids && status.uninstalled_ids.length > 0) {
      status.uninstalled_ids.forEach(pkgId => {
        const lowerId = pkgId.toLowerCase();
        if (!knownUninstalledIds.has(lowerId)) {
          knownUninstalledIds.add(lowerId);
          animateAndRemoveUninstalledApp(pkgId);
        }
      });
    }

    // Procesar programas que requieran atención
    if (status.failed_ids && status.failed_ids.length > 0) {
      status.failed_ids.forEach(f => {
        const pkgId = f.id;
        const rows = dom.outdatedTableBody.querySelectorAll('tr[data-id]');
        for (const r of rows) {
          const id = r.getAttribute('data-id');
          if (id && id.toLowerCase() === pkgId.toLowerCase()) {
            const btn = r.querySelector('.btn-update-single');
            if (btn && !btn.classList.contains('badge-updated-warning')) {
              btn.className = 'btn-row-action btn-update-single badge-updated-warning';
              btn.innerHTML = `
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <span>Revisar</span>
              `;
              btn.disabled = false;
              btn.title = "El instalador reportó un aviso o incompatibilidad de versión. Consulta la pestaña Terminal en Vivo.";
            }
            break;
          }
        }
      });
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

    return status;
  } catch (err) {
    console.error("Error al obtener estado:", err);
    return null;
  }
}

function animateAndRemoveUpdatedApp(pkgId) {
  // Buscar fila en la tabla de actualizaciones pendientes
  const rows = dom.outdatedTableBody.querySelectorAll('tr[data-id]');
  let targetRow = null;
  for (const r of rows) {
    const id = r.getAttribute('data-id');
    if (id && id.toLowerCase() === pkgId.toLowerCase()) {
      targetRow = r;
      break;
    }
  }

  const appObj = outdatedApps.find(a => a.id.toLowerCase() === pkgId.toLowerCase());
  const appName = appObj ? appObj.name : pkgId;

  if (targetRow) {
    // 1. Mostrar estado de éxito inmediato en la fila
    const btn = targetRow.querySelector('.btn-update-single');
    if (btn) {
      btn.className = 'badge-updated-success';
      btn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <span>Actualizado</span>
      `;
      btn.disabled = true;
    }

    targetRow.classList.add('row-just-updated');
    showToast(`✓ "${appName}" se ha actualizado correctamente.`, "success");

    // 2. Deseleccionar
    selectedAppIds.delete(pkgId);

    // 3. Tras 1.5 segundos de confirmación visual, desvanecer y remover de pendientes
    setTimeout(() => {
      targetRow.classList.add('row-fading-out');
      setTimeout(() => {
        targetRow.remove();
        outdatedApps = outdatedApps.filter(a => a.id.toLowerCase() !== pkgId.toLowerCase());
        dom.statOutdated.textContent = outdatedApps.length;
        dom.tabBadgeOutdated.textContent = outdatedApps.length;
        dom.visibleCount.textContent = getFilteredOutdated().length;
        updateSelectionUI();

        if (outdatedApps.length === 0) {
          renderOutdatedTable();
        }
      }, 500);
    }, 1500);
  } else {
    // Si no está visible en el DOM actualmente (por filtro de búsqueda u otra pestaña)
    outdatedApps = outdatedApps.filter(a => a.id.toLowerCase() !== pkgId.toLowerCase());
    selectedAppIds.delete(pkgId);
    dom.statOutdated.textContent = outdatedApps.length;
    dom.tabBadgeOutdated.textContent = outdatedApps.length;
    updateSelectionUI();
  }
}

function animateAndRemoveUninstalledApp(pkgId) {
  const lowerId = pkgId.toLowerCase();
  
  // 1. Quitar de la tabla de actualizaciones pendientes si está allí
  const outdatedRows = dom.outdatedTableBody.querySelectorAll('tr[data-id]');
  for (const r of outdatedRows) {
    const id = r.getAttribute('data-id');
    if (id && id.toLowerCase() === lowerId) {
      r.classList.add('row-fading-out');
      setTimeout(() => {
        r.remove();
        outdatedApps = outdatedApps.filter(a => a.id.toLowerCase() !== lowerId);
        dom.statOutdated.textContent = outdatedApps.length;
        dom.tabBadgeOutdated.textContent = outdatedApps.length;
        dom.visibleCount.textContent = getFilteredOutdated().length;
        updateSelectionUI();
        if (outdatedApps.length === 0) renderOutdatedTable();
      }, 400);
      break;
    }
  }

  // 2. Quitar de la tabla de todos los instalados si está allí
  const installedRows = dom.installedTableBody.querySelectorAll('tr[data-installed-id]');
  for (const r of installedRows) {
    const id = r.getAttribute('data-installed-id');
    if (id && id.toLowerCase() === lowerId) {
      r.classList.add('row-fading-out');
      setTimeout(() => {
        r.remove();
        installedApps = installedApps.filter(a => a.id.toLowerCase() !== lowerId);
        dom.statInstalled.textContent = installedApps.length;
        dom.tabBadgeInstalled.textContent = installedApps.length;
        if (installedApps.length === 0) renderInstalledTable();
      }, 400);
      break;
    }
  }

  // Quitar de selección
  selectedAppIds.delete(pkgId);
  outdatedApps = outdatedApps.filter(a => a.id.toLowerCase() !== lowerId);
  installedApps = installedApps.filter(a => a.id.toLowerCase() !== lowerId);
  dom.statOutdated.textContent = outdatedApps.length;
  dom.tabBadgeOutdated.textContent = outdatedApps.length;
  dom.statInstalled.textContent = installedApps.length;
  dom.tabBadgeInstalled.textContent = installedApps.length;
  updateSelectionUI();

  showToast(`🗑️ "${pkgId}" se ha desinstalado oficialmente.`, "success");
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
          <div class="actions-cell">
            <button class="btn-row-action btn-update-single" data-pkg-id="${escapeHtml(app.id)}" data-pkg-name="${escapeHtml(app.name)}" title="Actualizar a la última versión">
              Actualizar
            </button>
            <button class="btn-row-uninstall btn-uninstall-single" data-pkg-id="${escapeHtml(app.id)}" data-pkg-name="${escapeHtml(app.name)}" title="Desinstalar este programa">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
              <span>Quitar</span>
            </button>
          </div>
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

  // Listeners a los botones individuales de actualización
  dom.outdatedTableBody.querySelectorAll('.btn-update-single').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const pkgId = btn.getAttribute('data-pkg-id');
      const pkgName = btn.getAttribute('data-pkg-name');
      executeUpgradeSingle(pkgId, pkgName, btn);
    });
  });

  // Listeners a los botones individuales de desinstalación
  dom.outdatedTableBody.querySelectorAll('.btn-uninstall-single').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const pkgId = btn.getAttribute('data-pkg-id');
      const pkgName = btn.getAttribute('data-pkg-name');
      executeUninstall(pkgId, pkgName);
    });
  });
}

function renderInstalledTable() {
  const filtered = getFilteredInstalled();

  if (filtered.length === 0) {
    dom.installedTableBody.innerHTML = `
      <tr>
        <td colspan="6" class="empty-state">
          <p>No se encontraron aplicaciones instaladas.</p>
        </td>
      </tr>
    `;
    return;
  }

  let html = '';
  filtered.forEach(app => {
    html += `
      <tr data-installed-id="${escapeHtml(app.id)}">
        <td>
          <div class="app-name-cell">
            <span class="app-title-text">${escapeHtml(app.name)}</span>
          </div>
        </td>
        <td><span class="app-id-tag">${escapeHtml(app.id)}</span></td>
        <td><span class="version-badge version-current">${escapeHtml(app.version || '--')}</span></td>
        <td><span class="version-badge">${escapeHtml(app.available || '-')}</span></td>
        <td><span class="source-badge">${escapeHtml(app.source || 'winget')}</span></td>
        <td class="text-right">
          <button class="btn-row-uninstall btn-uninstall-single" data-pkg-id="${escapeHtml(app.id)}" data-pkg-name="${escapeHtml(app.name)}" title="Desinstalar este programa oficialmente">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="3 6 5 6 21 6"></polyline>
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
            </svg>
            <span>Desinstalar</span>
          </button>
        </td>
      </tr>
    `;
  });

  dom.installedTableBody.innerHTML = html;

  // Listeners a los botones de desinstalación de la lista completa
  dom.installedTableBody.querySelectorAll('.btn-uninstall-single').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const pkgId = btn.getAttribute('data-pkg-id');
      const pkgName = btn.getAttribute('data-pkg-name');
      executeUninstall(pkgId, pkgName);
    });
  });
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
function showConfirmModal(title, message, onConfirm, confirmText = "Continuar y Actualizar", isDanger = false) {
  const modal = document.getElementById('confirm-modal');
  const modalTitle = document.getElementById('modal-title');
  const modalMsg = document.getElementById('modal-message');
  const btnCancel = document.getElementById('modal-btn-cancel');
  const btnConfirm = document.getElementById('modal-btn-confirm');
  const modalIconWrap = modal.querySelector('.modal-icon-wrap');

  modalTitle.textContent = title;
  modalMsg.textContent = message;
  btnConfirm.textContent = confirmText;

  if (isDanger) {
    btnConfirm.className = 'btn btn-danger';
    if (modalIconWrap) {
      modalIconWrap.style.background = 'rgba(239, 68, 68, 0.15)';
      modalIconWrap.style.color = '#ef4444';
    }
  } else {
    btnConfirm.className = 'btn btn-primary';
    if (modalIconWrap) {
      modalIconWrap.style.background = 'rgba(99, 102, 241, 0.15)';
      modalIconWrap.style.color = '#818cf8';
    }
  }

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

async function executeUninstall(pkgId, pkgName) {
  if (isUpdatingOrScanning) {
    showToast("Ya hay una tarea en curso. Por favor espera a que termine.", "warning");
    return;
  }

  const displayName = pkgName || pkgId;
  showConfirmModal(
    `🗑️ ¿Desinstalar ${displayName}?`,
    `Se ejecutará el desinstalador oficial de Windows para eliminar "${displayName}" (${pkgId}) por completo de tu equipo. Si Windows o el desinstalador abre una ventana de confirmación o permisos (UAC), acéptala para proceder.`,
    async () => {
      try {
        showToast(`Iniciando desinstalación oficial de "${displayName}"...`, "info");
        switchTab('logs');
        const res = await fetch('/api/uninstall', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: pkgId })
        });
        const data = await res.json();
        if (!res.ok) {
          showToast(data.message || "No se pudo iniciar la desinstalación", "warning");
        }
      } catch (err) {
        showToast("Error de conexión al solicitar desinstalación", "error");
      }
    },
    "Sí, Desinstalar",
    true // isDanger
  );
}

// Polling de Estado y Logs (adaptativo)
const POLL_FAST = 1200;   // ms cuando hay operación activa
const POLL_IDLE = 2500;   // ms cuando el sistema está en reposo
let currentPollInterval = POLL_IDLE;

function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  schedulePoll();
}

function schedulePoll() {
  if (pollTimer) clearTimeout(pollTimer);
  pollTimer = setTimeout(async () => {
    const status = await checkStatus();
    await fetchLogs();

    if (status && status.outdated_count !== outdatedApps.length) {
      if (!status.is_updating) {
        await loadOutdatedApps();
      }
    }

    // Ajustar velocidad según actividad
    const newInterval = (status && (status.is_scanning || status.is_updating)) ? POLL_FAST : POLL_IDLE;
    if (newInterval !== currentPollInterval) {
      currentPollInterval = newInterval;
    }
    schedulePoll();
  }, currentPollInterval);
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
