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

    @parameterized.expand([(1,), (2,), (3,), (4,)])
    def test_config_files(self, grade):
        from unittest.mock import patch
        import inspect
        cur_file = inspect.stack(0)[0][1]
        testargs = [cur_file, 1]
        with patch('sys.argv', testargs):
            self.make_dummy_configs(grade)
            import neuroseries
            self.assertEqual(len(neuroseries.track_info['config']['list']), grade+2)
            self.assertEqual(neuroseries.track_info['config']['grade'], grade)
            self.remove_files()
