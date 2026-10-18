import sys
import threading
import time
import unittest

import update_engine as engine


class EngineTests(unittest.TestCase):
    def test_real_process_streams_and_returns_exit_code(self):
        lines = []
        result = engine.run_command([sys.executable, '-c', "print('avance', flush=True)"], lines.append, timeout=3)
        self.assertEqual(result.code, 0)
        self.assertFalse(result.timed_out)
        self.assertEqual(lines, ['avance'])

    def test_silent_process_cannot_block_timeout(self):
        start = time.monotonic()
        result = engine.run_command([sys.executable, '-c', 'import time; time.sleep(20)'], lambda line: None, timeout=.2)
        self.assertTrue(result.timed_out)
        self.assertLess(time.monotonic() - start, 4)

    def test_elapsed_feedback_continues_after_process_closes_output(self):
        ticks = []
        result = engine.run_command([sys.executable, '-c', 'import os,time; os.close(1); os.close(2); time.sleep(1.3)'],
                                    lambda line: None, timeout=3, on_tick=ticks.append)
        self.assertEqual(result.code, 0)
        self.assertGreaterEqual(len(ticks), 2)

    def test_command_is_exact_noninteractive_and_does_not_force_unknown(self):
        command = engine.upgrade_command('Vendor.App')
        self.assertIn('--exact', command)
        self.assertIn('--disable-interactivity', command)
        self.assertNotIn('--include-unknown', command)
        self.assertNotIn('--force', command)

    def test_command_searches_only_the_catalog_that_identified_the_app(self):
        command = engine.upgrade_command('VideoLAN.VLC', source='winget')
        self.assertEqual(command[command.index('--source') + 1], 'winget')
        store = engine.upgrade_command('Store.App', source='msstore')
        self.assertEqual(store[store.index('--source') + 1], 'msstore')
        with self.assertRaises(ValueError):
            engine.upgrade_command('Vendor.App', source='')

    def test_ids_must_be_strings_from_displayed_catalog(self):
        self.assertEqual(engine.validate_ids(['A.App', 'A.App'], ['A.App']), ['A.App'])
        for value in ['A.App', [1], ['Other.App'], ['--all'], []]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                engine.validate_ids(value, ['A.App'])

    def test_only_one_operation_can_be_reserved(self):
        gate = engine.OperationGate()
        barrier = threading.Barrier(8)
        winners = []
        def reserve():
            barrier.wait()
            winners.append(gate.acquire())
        threads = [threading.Thread(target=reserve) for _ in range(8)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(winners.count(True), 1)
        gate.release()
        self.assertTrue(gate.acquire())

    def test_unsigned_windows_exit_codes_are_classified(self):
        self.assertEqual(engine.result_kind(-1978335189), 'no_update')
        self.assertEqual(engine.result_kind(3010), 'restart')
        self.assertEqual(engine.result_kind(5), 'failed')


if __name__ == '__main__':
    unittest.main()
