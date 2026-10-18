import copy
import http.client
import json
import threading
import unittest
from unittest.mock import patch

import app
from update_engine import CommandResult


class AppTests(unittest.TestCase):
    def setUp(self):
        self.original = copy.deepcopy(app.app_state)
        app.app_state.update(outdated_apps=[{'id': 'A.App'}, {'id': 'B.App'}],
                             installed_apps=[], update_blocked=False, logs=[], last_result=None)

    def tearDown(self):
        app.app_state.clear()
        app.app_state.update(self.original)

    def test_partial_failure_is_not_reported_as_all_successful(self):
        with patch.object(app, 'run_command', side_effect=[CommandResult(0), CommandResult(5)]):
            app.upgrade_selected_thread(['A.App', 'B.App'])
        result = app.app_state['last_result']
        self.assertEqual(result['counts']['success'], 1)
        self.assertEqual(result['counts']['failed'], 1)
        self.assertEqual(app.app_state['outdated_apps'], [{'id': 'B.App'}])
        self.assertEqual(app.app_state['logs'][-1]['level'], 'warning')

    def test_timeout_stops_queue_and_leaves_remaining_pending(self):
        with patch.object(app, 'run_command', return_value=CommandResult(-1, True)) as run:
            app.upgrade_selected_thread(['A.App', 'B.App'])
        self.assertEqual(run.call_count, 1)
        self.assertTrue(app.app_state['update_blocked'])
        self.assertEqual(app.app_state['last_result']['counts']['pending'], 1)
        self.assertEqual(app.app_state['updated_ids'], [])

    def test_restart_before_install_is_not_success(self):
        with patch.object(app, 'run_command', return_value=CommandResult(0x8A15010A)):
            app.upgrade_selected_thread(['A.App', 'B.App'])
        self.assertEqual(app.app_state['last_result']['counts']['success'], 0)
        self.assertEqual(app.app_state['last_result']['counts']['restart_before'], 1)

    def test_scan_failure_retains_previous_list(self):
        with patch.object(app, 'run_command', return_value=CommandResult(5)):
            app.scan_updates_thread()
        self.assertEqual(len(app.app_state['outdated_apps']), 2)
        self.assertFalse(app.app_state['is_scanning'])

    def test_preflight_failure_releases_gate_without_starting_work(self):
        def reject():
            raise ValueError('bloqueado')
        with patch.object(app.threading, 'Thread') as thread:
            with self.assertRaises(ValueError):
                app.start_operation(lambda: None, preflight=reject)
            thread.assert_not_called()
        self.assertTrue(app.operation_gate.acquire())
        app.operation_gate.release()

    def test_nested_scan_does_not_mark_reserved_operation_idle(self):
        app.app_state['is_scanning'] = True
        with patch.object(app, 'run_command', return_value=CommandResult(0)):
            app.scan_updates_thread()
        self.assertTrue(app.app_state['is_scanning'])

    def test_http_rejects_foreign_origin_invalid_payload_and_concurrent_operation(self):
        server = app.ReusableHTTPServer(('127.0.0.1', 0), app.AppRequestHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        previous_port = app.PORT
        app.PORT = server.server_port
        def request(body, origin=None):
            connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=3)
            headers = {'Content-Type': 'application/json'}
            if origin: headers['Origin'] = origin
            connection.request('POST', '/api/upgrade-selected', body, headers)
            response = connection.getresponse()
            result = response.status, json.loads(response.read())
            connection.close()
            return result
        try:
            self.assertEqual(request('{}', 'https://example.org')[0], 403)
            self.assertEqual(request('{bad')[0], 400)
            self.assertEqual(request('{"ids":"A.App"}')[0], 400)
            self.assertEqual(request('{"ids":["Other.App"]}')[0], 400)
            entered = threading.Event()
            release = threading.Event()
            def waiting_worker(ids):
                entered.set()
                release.wait(3)
            with patch.object(app, 'upgrade_selected_thread', side_effect=waiting_worker):
                self.assertEqual(request('{"ids":["A.App"]}')[0], 200)
                self.assertTrue(entered.wait(1))
                self.assertEqual(request('{"ids":["A.App"]}')[0], 409)
                release.set()
                for _ in range(100):
                    if not app.app_state['is_updating']: break
                    threading.Event().wait(.01)
        finally:
            app.PORT = previous_port
            server.shutdown()
            server.server_close()
            thread.join(2)


if __name__ == '__main__':
    unittest.main()
