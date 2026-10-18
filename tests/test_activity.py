import unittest
from unittest.mock import patch
import activity


class ActivityTests(unittest.TestCase):
    def test_background_process_is_detected_without_a_window(self):
        result = activity.classify_activity('Nextcloud.NextcloudDesktop', [{'ProcessName':'nextcloud', 'Id':42}])
        self.assertEqual(result['status'], 'running')
        self.assertEqual(result['processes'], [{'name':'nextcloud.exe', 'pid':42}])

    def test_known_app_without_matching_process_is_not_guaranteed_closed(self):
        self.assertEqual(activity.classify_activity('VideoLAN.VLC', [])['status'], 'not_detected')

    def test_unknown_app_and_failed_snapshot_are_unverified(self):
        self.assertEqual(activity.classify_activity('Unmapped.App', [])['status'], 'unknown')
        self.assertEqual(activity.classify_activity('VideoLAN.VLC', None)['status'], 'unknown')

    def test_matching_is_exact_and_case_insensitive(self):
        self.assertEqual(activity.classify_activity('VideoLAN.VLC', [{'ProcessName':'VLC', 'Id':1}])['status'], 'running')
        self.assertEqual(activity.classify_activity('VideoLAN.VLC', [{'ProcessName':'myvlctool', 'Id':2}])['status'], 'not_detected')

    def test_task_manager_opens_only_the_windows_executable(self):
        with patch.object(activity.subprocess, 'Popen') as launch:
            activity.open_task_manager()
        command = launch.call_args.args[0]
        self.assertEqual(len(command), 1)
        self.assertTrue(command[0].lower().endswith('system32\\taskmgr.exe'))


if __name__ == '__main__':
    unittest.main()
