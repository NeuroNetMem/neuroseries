import unittest
from nose_parameterized import parameterized


class DataManagerStartupTestCase(unittest.TestCase):
    filenames = ['~/.neuroseries/config_alt.yml', '~/.neuroseries/config.yml', 'neuroseries.yml', 'neuroseries.yml']
    ns_dir = "~/.neuroseries"

    def setUp(self):
        pass

    def tearDown(self):
        self.remove_files()

    def remove_files(self):
        import os
        for f in self.filenames:
            try:
                os.remove(os.path.expanduser(f))
            except FileNotFoundError:
                pass
        try:
            del os.environ['NEUROSERIES_CONFIG']
        except KeyError:
            pass

    def make_dummy_configs(self, grade):
        file_contents = ("""
list:
- uno
- due
- tre
grade: {}
        """.format(grade),
                         """
list:
- uno
- due
- tre
- quattro
grade: {}
        """.format(grade),
                         """
list:
- uno
- due
- tre
- quattro
- cinque
grade: {}
        """.format(grade),
                         """
list:
- uno
- due
- tre
- quattro
- cinque
- sei
grade: {}
        """.format(grade))

        import os

        os.environ['NEUROSERIES_CONFIG'] = self.filenames[0]

        try:
            os.mkdir(os.path.expanduser(self.ns_dir))
        except OSError:
            pass

        fds = [open(os.path.expanduser(fname), 'w') for fname in self.filenames[:grade]]

        for (fd, content) in zip(fds[:grade], file_contents):
            fd.write(content)

    def test_create_info(self):
        from unittest.mock import patch
        import inspect
        cur_file = inspect.stack(0)[0][1]
        testargs = [cur_file, 1]
        with patch('sys.argv', testargs):
            import neuroseries
            print(neuroseries.track_info['config'])
        self.assertEqual(neuroseries.track_info['entry_point'], cur_file)

    def test_venv(self):
        from unittest.mock import patch
        import inspect
        cur_file = inspect.stack(0)[0][1]
        testargs = [cur_file, 1]
        with patch('sys.argv', testargs):
            import neuroseries
            self.assertTrue('pandas' in neuroseries.track_info['venv'])

    @parameterized.expand([(1,), (2,), (3,), (4,)])
    def test_config_files(self, grade):
        from unittest.mock import patch
        import inspect
        cur_file = inspect.stack(0)[0][1]
        testargs = [cur_file, 1]
        with patch('sys.argv', testargs):
            self.make_dummy_configs(grade)
            import neuroseries
            neuroseries.track_info = neuroseries.data_manager._get_init_info()
            self.assertEqual(len(neuroseries.track_info['config']['list']), grade+2)
            self.assertEqual(neuroseries.track_info['config']['grade'], grade)
            self.remove_files()


class UtilsTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

# def str_to_series(a_string):
#     ba = bytearray(a_string, encoding='utf-8')
#     ss = pd.Series(ba)
#     return ss
#
# def series_to_series(ss):
#     bb = bytearray(ss.values.tolist())
#     bs = bytes(bb)
#     a_string = bs.decode()
#     return a_string
    def test_convert_dict(self):
        from unittest.mock import patch
        import inspect
        cur_file = inspect.stack(0)[0][1]
        testargs = [cur_file, 1]
        with patch('sys.argv', testargs):
            import neuroseries as nts

            d = {'a': 5, 'b': [1, 2, 3], 'c':
                {'a1': 'aaa', 'c': 54}}

            import json
            import pandas as pd
            s1 = json.dumps(d)
            ss = nts.str_to_series(s1)
            s2 = nts.series_to_str(ss)
            self.assertEqual(s1, s2)

            d2 = json.loads(s2)
            self.assertEqual(d, d2)




