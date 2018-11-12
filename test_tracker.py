import unittest
import os
import json
from nose_parameterized import parameterized
import numpy as np
import pexpect as pex
from test_annex import prepare_sandbox, change_mod, make_random_text
# import pandas as pd
# from unittest.mock import patch
# import inspect

import neuroseries as nts

# noinspection PyUnresolvedReferences
from unittest.mock import patch
import inspect
cur_file = inspect.stack(0)[0][1]
test_args = [cur_file, 1]
with patch('sys.argv', test_args):
    # noinspection PyUnresolvedReferences
    import dataman as dtm


def create_remote_repo(name):
    import os
    os.mkdir(name)
    os.chdir(name)
    pex.run('git init')
    pex.run('git annex init')
    f = open('file1.txt', 'w')
    content = make_random_text(1000)
    f.write(content)
    f.close()
    pex.run('git annex add file1.txt')
    pex.run('git commit -m "commit file1.txt"')
    pex.run('git remote add laptop ../repo1')


class TrackerInitTestCase(unittest.TestCase):
    # noinspection PyShadowingNames
    def setUp(self):
        # noinspection PyGlobalUndefined
        global dtm
        from unittest.mock import patch
        import inspect
        cur_file = inspect.stack(0)[0][1]
        test_args = [cur_file, 1]
        with patch('sys.argv', test_args):
            # noinspection PyUnresolvedReferences
            import dataman as dtm
        from scipy.io import loadmat
        self.mat_data1 = loadmat(
            '/Users/fpbatta/src/batlab/neuroseries/resources/test_data/interval_set_data_1.mat')

        import os.path
        # noinspection PyBroadException
        try:
            os.remove('store.h5')
        except:
            pass

        self.a1 = self.mat_data1['a1'].ravel()
        self.b1 = self.mat_data1['b1'].ravel()
        self.int1 = nts.IntervalSet(self.a1, self.b1, expect_fix=True)

        self.a2 = self.mat_data1['a2'].ravel()
        self.b2 = self.mat_data1['b2'].ravel()
        self.int2 = nts.IntervalSet(self.a2, self.b2, expect_fix=True)

        self.tsd_t = self.mat_data1['t'].ravel()
        self.tsd_d = self.mat_data1['d'].ravel()
        self.tsd = nts.Tsd(self.tsd_t, self.tsd_d)

        self.start_dir = os.getcwd()
        prepare_sandbox()
        os.chdir('scratch/sandbox')

        os.mkdir('repo1')
        os.chdir('repo1')
        pex.run('git init')
        pex.run('git annex init')

    def tearDown(self):
        import sys
        del sys.modules[dtm.__name__]
        del sys.modules[dtm.data_manager.__name__]
        import os
        # noinspection PyBroadException
        try:
            self.store.close()
        except:
            pass

        # noinspection PyBroadException
        try:
            self.store2.close()
        except:
            pass

        # noinspection PyBroadException
        try:
            os.remove('store.h5')
        except:
            pass

        import os
        import shutil
        print(self.start_dir)
        os.chdir(self.start_dir)
        # noinspection PyBroadException
        try:
            change_mod('scratch/sandbox')
            shutil.rmtree('scratch/sandbox')
        except:
            pass

    @parameterized.expand([(dtm.FilesBackend,), (dtm.JsonBackend,), (dtm.AnnexJsonBackend,)])
    def testTrackerInfo(self, backend_class):
        import json
        backend = backend_class()

        import os
        # noinspection PyBroadException
        try:
            os.remove('store.h5')
        except:
            pass

        self.store = dtm.HDFStore('store.h5', backend=backend, mode='w')
        d = self.store.info
        self.assertEqual(set(d.keys()),
                         {'repo_info', 'date_created', 'hash', 'dependencies', 'file', 'variables', 'run'})
        self.assertEqual(d['variables'], {})
        self.assertEqual(d['dependencies'], [])
        self.assertEqual(d['run'], dtm.track_info)
        self.assertEqual(d['file'], 'store.h5')
        self.assertEqual(d['hash'], 'NULL')

        self.int1.store(self.store, 'int1')
        self.int2.store(self.store, 'int2')
        self.tsd.store(self.store, 'tsd')
        self.store.close()

        self.store = dtm.HDFStore('store.h5', backend=backend, mode='r')
        d = json.loads(dtm.series_to_str(self.store['file_info']))
        self.assertEqual(set(d['variables'].keys()), {'tsd', 'int2', 'int1'})

    @parameterized.expand([(dtm.FilesBackend,), (dtm.JsonBackend,), (dtm.AnnexJsonBackend,)])
    def testOpenCloseFile(self, backend_type):
        backend = backend_type()
        self.store = dtm.HDFStore('store.h5', backend=backend, mode='w')
        self.int1.store(self.store, 'int1')
        self.int2.store(self.store, 'int2')
        self.tsd.store(self.store, 'tsd')
        self.store.close()

        backend = dtm.FilesBackend()
        self.store2 = dtm.HDFStore('store.h5', backend=backend, mode='r')
        self.assertTrue(len(dtm.dependencies) > 0)
        self.assertEqual(dtm.dependencies[0]['file'], 'store.h5')
        d = self.store2.get_file_info()
        self.assertEqual(set(d['variables'].keys()), {'tsd', 'int2', 'int1'})
        self.store2.close()

    @parameterized.expand([('files',), ('json',), ('annex',)])
    def testStoreArray(self, backend_type):
        if backend_type == 'files':
            backend = dtm.FilesBackend()
        elif backend_type == 'json':
            backend = dtm.JsonBackend()
        else:
            backend = dtm.AnnexJsonBackend()

        if backend_type == 'annex':
            import os
            os.chdir('..')
            create_remote_repo('repo2')
            os.chdir('../repo1')
            backend.repo.add_remote('origin', '../repo2')
        self.store = dtm.HDFStore('store.h5', backend=backend, mode='w')
        arr = np.arange(100)
        self.store['arr'] = arr
        self.store.close()

        if backend_type == 'annex':
            backend.repo.push_annex('origin')
            backend.repo.drop('store.h5')
        if backend_type == 'files':
            backend = dtm.FilesBackend()
        elif backend_type == 'json':
            backend = dtm.JsonBackend()
        else:
            backend = dtm.AnnexJsonBackend()
        self.store2 = dtm.HDFStore('store.h5', backend=backend, mode='r')
        arr2 = self.store2['arr']
        np.testing.assert_array_almost_equal_nulp(arr, arr2)


class GenericFileStoreTestCase(unittest.TestCase):
    # noinspection PyUnresolvedReferences,PyShadowingNames
    def setUp(self):
        # noinspection PyGlobalUndefined
        global dtm
        from unittest.mock import patch
        import inspect
        cur_file = inspect.stack(0)[0][1]
        test_args = [cur_file, 1]
        with patch('sys.argv', test_args):
            import dataman as dtm

        self.start_dir = os.getcwd()
        prepare_sandbox()
        os.chdir('scratch/sandbox')

    def tearDown(self):
        import sys
        del sys.modules[dtm.__name__]
        del sys.modules[dtm.data_manager.__name__]

        import shutil
        print(self.start_dir)
        os.chdir(self.start_dir)
        # noinspection PyBroadException
        try:
            change_mod('scratch/sandbox')
            shutil.rmtree('scratch/sandbox')
        except:
            pass

    @parameterized.expand([('json',), ('annex',)])
    def test_write_read(self, backend_type):
        os.mkdir('repo1')
        os.chdir('repo1')
        if backend_type == 'json':
            backend = dtm.JsonBackend()
        else:
            os.chdir('..')
            create_remote_repo('repo2')
            os.chdir('../repo1')
            pex.run('git init')
            pex.run('git annex init')
            backend = dtm.AnnexJsonBackend()
            backend.repo.add_remote('origin', '../repo2')

        with open('file2.txt', 'w') as f:
            content = make_random_text(1000)
            f.write(content)

        self.store = dtm.store_file('file2.txt',  backend=backend, comment='file 2 for figure')

        self.assertTrue(os.path.exists('file2.json'))
        with open('file2.json', 'r') as f:
            info = json.loads(f.read())

        self.assertEqual(info['file'], 'file2.txt')
        if backend_type == 'annex':
            import git
            repo = git.Repo.init('.')
            self.assertEqual(repo.git.execute(['git', 'ls-files', 'file2.txt', '--error-unmatch']), 'file2.txt')
            self.assertEqual(repo.git.execute(['git', 'ls-files', 'file2.json', '--error-unmatch']), 'file2.json')
            backend.repo.push_annex('origin')
            backend.repo.drop('file2.txt')

        dtm.register_input('file2.txt', backend=backend)
        self.assertTrue(os.path.exists('file2.txt'))

        with open('file2.txt', 'r') as f:
            read_content = f.read()

        self.assertEqual(read_content, content)

        files_dependencies = [t['file'] for t in dtm.dependencies]
        self.assertIn('file2.txt', files_dependencies)

    @parameterized.expand([('json',), ('annex',)])
    def test_write_read_file_down_directory(self, backend_type):
        os.mkdir('repo1')
        os.chdir('repo1')
        if backend_type == 'json':
            backend = dtm.JsonBackend()
        else:
            os.chdir('..')
            create_remote_repo('repo2')
            os.chdir('../repo1')
            pex.run('git init')
            pex.run('git annex init')
            backend = dtm.AnnexJsonBackend()
            backend.repo.add_remote('origin', '../repo2')

        os.mkdir('child_dir')
        os.chdir('child_dir')
        with open('file2.txt', 'w') as f:
            content = make_random_text(1000)
            f.write(content)

        self.store = dtm.store_file('file2.txt',  backend=backend, comment='file 2 for figure')

        self.assertTrue(os.path.exists('file2.json'))
        with open('file2.json', 'r') as f:
            info = json.loads(f.read())

        self.assertEqual(info['file'], 'file2.txt')
        if backend_type == 'annex':
            import git
            os.chdir('..')
            repo = git.Repo.init('.')
            self.assertEqual(repo.git.execute(['git', 'ls-files', 'child_dir/file2.txt', '--error-unmatch']),
                             'child_dir/file2.txt')
            self.assertEqual(repo.git.execute(['git', 'ls-files', 'child_dir/file2.json', '--error-unmatch']),
                             'child_dir/file2.json')
            backend.repo.push_annex('origin')
            backend.repo.drop('child_dir/file2.txt')
            os.chdir('child_dir')

        dtm.register_input('file2.txt', backend=backend)
        self.assertTrue(os.path.exists('file2.txt'))

        with open('file2.txt', 'r') as f:
            read_content = f.read()

        self.assertEqual(read_content, content)

        files_dependencies = [t['file'] for t in dtm.dependencies]
        self.assertIn('file2.txt', files_dependencies)

if __name__ == '__main__':
    unittest.main()