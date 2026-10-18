const assert = require('node:assert/strict');
const ui = require('../web/activity-ui.js');
const apps = [
  {id:'VLC', activity:{status:'not_detected'}},
  {id:'Nextcloud', activity:{status:'running', processes:[{name:'nextcloud.exe',pid:42}]}},
  {id:'Other', activity:{status:'unknown'}}
];
assert.deepEqual([...ui.selection(apps, new Set(), false)], ['VLC']);
assert.deepEqual([...ui.selection(apps, new Set(['VLC','Nextcloud','Other']), true)], ['VLC']);
assert.deepEqual([...ui.selection(apps, new Set(), true)], [], 'Do not reselect intentionally unchecked rows');
assert.deepEqual(ui.candidates(apps).map(app => app.id), ['VLC']);
assert.match(ui.render(apps[1], text => String(text).replaceAll('<','&lt;')), /PID 42/);
assert.match(ui.render(apps[1], String), /Revisar en Administrador de tareas/);
assert.equal(ui.state({id:'Unknown'}), 'unknown');
console.log('Actividad de interfaz: 7 comprobaciones correctas');
