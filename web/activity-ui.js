const ActivityUI = (() => {
  function state(app) { return app.activity?.status || 'unknown'; }
  function candidates(apps) { return apps.filter(app => state(app) === 'not_detected'); }
  function selection(apps, selected, initialized) {
    if (!initialized) return new Set(candidates(apps).map(app => app.id));
    return new Set(apps.filter(app => state(app) === 'not_detected' && selected.has(app.id)).map(app => app.id));
  }
  function render(app, escape) {
    const activity = app.activity || {};
    const status = state(app);
    const label = {running:'En ejecución', not_detected:'Sin actividad detectada', unknown:'Sin comprobar'}[status] || 'Sin comprobar';
    const processes = (activity.processes || []).slice(0, 4).map(process => `${process.name} · PID ${process.pid}`).join(', ');
    const explanation = status === 'unknown' ? 'No se puede asociar con certeza esta aplicación a sus procesos.' : 'Comprobación por nombre de proceso; no garantiza que no haya trabajo pendiente.';
    return `<div class="activity-info"><span class="activity-badge activity-${escape(status)}" title="${escape(explanation)}">${label}</span>
      ${processes ? `<small class="activity-processes">${escape(processes)}</small>` : ''}
      ${activity.checked_at ? `<small class="activity-checked">Consulta: ${escape(activity.checked_at)}</small>` : ''}
      ${status === 'running' ? `<button class="btn-row-action btn-review-activity" data-pkg-id="${escape(app.id)}">Revisar en Administrador de tareas</button>` : ''}</div>`;
  }
  return {state, candidates, selection, render};
})();
if (typeof module !== 'undefined') module.exports = ActivityUI;
