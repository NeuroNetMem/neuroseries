import unittest


class DataManagerStartupTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_info(self):
        from unittest.mock import patch
        import inspect

        cur_file = inspect.stack(0)[0][1]
        testargs = [cur_file, 1]
        with patch('sys.argv', testargs):
            import neuroseries
            print(neuroseries.track_info)
        self.assertEqual(neuroseries.track_info['entry_point'], cur_file)
