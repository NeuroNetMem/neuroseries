import unittest
# from nose_parameterized import parameterized
# import numpy as np
# import pandas as pd
# from unittest.mock import patch
# import inspect

# import neuroseries as nts


class TrackerInitTestCase(unittest.TestCase):
    def setUp(self):
        global nts
        import neuroseries as nts
        from scipy.io import loadmat
        self.mat_data1 = loadmat(
            '/Users/fpbatta/src/batlab/neuroseries/resources/test_data/interval_set_data_1.mat')

        import os.path
        # noinspection PyBroadException
        try:
            os.remove('store.h5')
        except:
            pass
        # nts.track_info = nts.data_manager._get_init_info()
        # nts.dependencies = []

        self.a1 = self.mat_data1['a1'].ravel()
        self.b1 = self.mat_data1['b1'].ravel()
        self.int1 = nts.IntervalSet(self.a1, self.b1, expect_fix=True)

        self.a2 = self.mat_data1['a2'].ravel()
        self.b2 = self.mat_data1['b2'].ravel()
        self.int2 = nts.IntervalSet(self.a2, self.b2, expect_fix=True)

        self.tsd_t = self.mat_data1['t'].ravel()
        self.tsd_d = self.mat_data1['d'].ravel()
        self.tsd = nts.Tsd(self.tsd_t, self.tsd_d)

    def tearDown(self):
        import sys
        del sys.modules[nts.__name__]
        del sys.modules[nts.data_manager.__name__]
        import os
        # noinspection PyBroadException
        try:
            self.store.close()
        except:
            pass

        try:
            self.store2.close()
        except:
            pass

        try:
            os.remove('store.h5')
        except:
            pass


    def testTrackerInfo(self):
        import json
        backend = nts.FilesBackend()
        # nts.reset_dependencies()
        # self.assertEqual(nts.data_manager.dependencies, [])
        # self.assertEqual(nts.dependencies, [])
        import os
        try:
            os.remove('store.h5')
        except:
            pass

        self.store = nts.HDFStore('store.h5', backend=backend, mode='w')
        d = self.store.info
        # self.assertEqual(nts.dependencies, [])
        self.assertEqual(set(d.keys()),
                         {'repo_info', 'date_created', 'hash', 'dependencies', 'file', 'variables', 'run'})
        self.assertEqual(d['variables'], {})
        # self.assertEqual(nts.dependencies, [])
        self.assertEqual(d['dependencies'], [])
        self.assertEqual(d['run'], nts.track_info)
        self.assertEqual(d['file'], 'store.h5')
        self.assertEqual(d['hash'], 'NULL')

        self.int1.store(self.store, 'int1')
        self.int2.store(self.store, 'int2')
        self.tsd.store(self.store, 'tsd')
        self.store.close()

        self.store = nts.HDFStore('store.h5', backend=backend, mode='r')
        d = json.loads(nts.series_to_str(self.store['file_info']))
        self.assertEqual(set(d['variables'].keys()), {'tsd', 'int2', 'int1'})


    def testOpenCloseFile(self):
        import json
        backend = nts.FilesBackend()
        self.store = nts.HDFStore('store.h5', backend=backend, mode='w')
        self.int1.store(self.store, 'int1')
        self.int2.store(self.store, 'int2')
        self.tsd.store(self.store, 'tsd')
        self.store.close()

        self.store2 = nts.HDFStore('store.h5', backend=backend, mode='r')
        self.assertTrue(len(nts.dependencies) > 0)
        self.assertEqual(nts.dependencies[0]['file'], 'store.h5')
        d = json.loads(nts.series_to_str(self.store2['file_info']))
        self.assertEqual(set(d['variables'].keys()), {'tsd', 'int2', 'int1'})
        self.store2.close()
