const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync('web/app.js', 'utf8');
const start = source.indexOf('function schedulePoll()');
const end = source.indexOf('// Toasts', start);
let callback;
let loads = 0;
let status = {operation_id: 1, is_scanning: true, is_updating: false, outdated_count: 2};
const context = vm.createContext({
  pollTimer: null, lastOperationId: 0, outdatedApps: [{}, {}],
  currentPollInterval: 100, POLL_FAST: 100, POLL_IDLE: 1000,
  setTimeout(fn) { callback = fn; return 1; }, clearTimeout() {},
  async checkStatus() { return status; }, async fetchLogs() {},
  async loadOutdatedApps() { loads++; }
});
vm.runInContext(source.slice(start, end), context);
(async () => {
  context.schedulePoll();
  await callback();
  assert.equal(loads, 0, 'Do not consume the revision while scanning');
  assert.equal(context.lastOperationId, 0);
  status = {...status, is_scanning: false};
  await callback();
  assert.equal(loads, 1, 'Reload changed versions even when row count stays the same');
  assert.equal(context.lastOperationId, 1);
  await callback();
  assert.equal(loads, 1, 'Do not reload completed operations repeatedly');
  console.log('Polling: 3 comprobaciones correctas');
})().catch(error => { console.error(error); process.exitCode = 1; });
