import unittest
from nose_parameterized import parameterized
import numpy as np
from unittest.mock import patch
import inspect
import neuroseries as nts


cur_file = inspect.stack(0)[0][1]
test_args = [cur_file, 1]
print(cur_file)
with patch('sys.argv', test_args):
    import dataman as dtm


# noinspection PyBroadException
class HDFStoreTestCase(unittest.TestCase):
    def setUp(self):
        from scipy.io import loadmat
        self.mat_data1 = loadmat(
            '/Users/fpbatta/src/batlab/neuroseries/resources/test_data/interval_set_data_1.mat')

        import os
        try:
            os.remove('store.h5')
        except:
            pass
        backend = dtm.FilesBackend()
        self.store = dtm.HDFStore('store.h5', backend=backend, mode='w')

        self.a1 = self.mat_data1['a1'].ravel()
        self.b1 = self.mat_data1['b1'].ravel()
        self.int1 = nts.IntervalSet(self.a1, self.b1, expect_fix=True)

        self.a2 = self.mat_data1['a2'].ravel()
        self.b2 = self.mat_data1['b2'].ravel()
        self.int2 = nts.IntervalSet(self.a2, self.b2, expect_fix=True)

        self.tsd_t = self.mat_data1['t'].ravel()
        self.tsd_d = self.mat_data1['d'].ravel()

        self.store.close()

    def tearDown(self):
        import os
        try:
            self.store.close()
            os.remove('store.h5')
        except:
            pass

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def test_read_write(self, data_class):
        from scipy.io import loadmat
        self.mat_data1 = loadmat(
            '/Users/fpbatta/src/batlab/neuroseries/resources/test_data/interval_set_data_1.mat')

        self.tsd = data_class(self.tsd_t, self.tsd_d)

        self.store = dtm.HDFStore('store.h5', backend=dtm.FilesBackend(), mode='w')
        self.int1.store(self.store, 'int1')
        self.int2.store(self.store, 'int2')
        self.tsd.store(self.store, 'tsd')

        self.store.close()

        with dtm.HDFStore('store.h5', backend=dtm.FilesBackend()) as store:
            k = store.keys()
            self.assertIn('/int1', k)
            self.assertIn('/int2', k)
            self.assertIn('/tsd', k)
            all_vars = nts.extract_from(store)
            self.assertIn('int1', all_vars)
            self.assertIn('int2', all_vars)
            self.assertIn('tsd', all_vars)
            self.assertIsInstance(all_vars['int1'], nts.IntervalSet)
            self.assertIsInstance(all_vars['tsd'], data_class)
            np.testing.assert_array_almost_equal_nulp(self.int1['start'], all_vars['int1']['start'])
            np.testing.assert_array_almost_equal_nulp(self.int1['end'], all_vars['int1']['end'])
            np.testing.assert_array_almost_equal_nulp(self.int2['start'], all_vars['int2']['start'])
            np.testing.assert_array_almost_equal_nulp(self.int2['end'], all_vars['int2']['end'])
            np.testing.assert_array_almost_equal_nulp(self.tsd.index.values,
                                                      all_vars['tsd'].index.values)
            np.testing.assert_array_almost_equal_nulp(self.tsd.values,
                                                      all_vars['tsd'].values)

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def test_metadata(self, data_class):
        from scipy.io import loadmat
        self.mat_data1 = loadmat(
            '/Users/fpbatta/src/batlab/neuroseries/resources/test_data/interval_set_data_1.mat')

        self.tsd = data_class(self.tsd_t, self.tsd_d)

        self.store = dtm.HDFStore('store.h5', backend=dtm.FilesBackend(), mode='w')
        self.int1.store(self.store, 'int1')
        self.tsd.store(self.store, 'tsd')
        self.store.close()

        with dtm.HDFStore('store.h5', backend=dtm.FilesBackend()) as store:
            all_vars = nts.extract_from(store)
        self.assertEqual(all_vars['int1'].nts_class, 'IntervalSet')
        self.assertIsInstance(all_vars['int1'], nts.IntervalSet)


if __name__ == '__main__':
    unittest.main()