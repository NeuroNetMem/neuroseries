import unittest

import numpy as np
import pandas as pd
import neuroseries as nts


class TsTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_ts(self):
        """
        calling convention
        ts = nts.Ts(a)
        ts is an instance of pd.DataFrame
        """
        a = np.random.randint(0, 10000000, 100)
        a.sort()
        ts = nts.Ts(a)
        self.assertIsInstance(ts, pd.DataFrame, msg="ts doesn't return DataFrame")
        self.assertIsInstance(ts.index.values, np.ndarray,
                      msg="ts doesn't return array values")
        self.assertIs(ts.index.dtype, np.dtype(np.int64), msg='index type is not int64')
        np.testing.assert_array_almost_equal_nulp(a, ts.index.values)

    def test_create_ts_from_double(self):
        """
        data get converted to ts and back fine
        """
        a = np.floor(np.random.rand(100)*1000000)
        a.sort()
        ts = nts.Ts(a)
        self.assertIs(ts.index.dtype, np.dtype(np.int64), msg='index type is not int64')
        np.testing.assert_array_almost_equal_nulp(a, ts.index.values)

    def test_create_ts_time_units(self):
        """
        internally data are stored as usec
        """
        a = np.random.randint(0, 1000, 100)
        a.sort()
        ts = nts.Ts(a, time_units='ms')
        np.testing.assert_array_almost_equal_nulp(ts.index.values, a*1000)
        ts = nts.Ts(a, time_units='s')
        np.testing.assert_array_almost_equal_nulp(ts.index.values, a.astype(np.int64) * 1000000)

    def test_create_ts_time_units_double(self):
        """
        conversion of time units from floating point type
        """
        a = np.floor(np.random.rand(100) * 1000000)
        a.sort()
        ts = nts.Ts(a, time_units='ms')
        np.testing.assert_array_almost_equal_nulp(ts.index.values, a * 1000)

    def test_create_ts_from_non_sorted(self):
        """
        if ts are not sorted, a warning should be returned and the timestamps sorted for you
        """
        a = np.random.randint(0, 1000, 100)
        # with self.assertWarns(UserWarning):
        #     ts = nts.Ts(a)
        ts = nts.Ts(a)

        np.testing.assert_array_almost_equal_nulp(np.sort(a), ts.index.values)


class TsRestrictTestCase(unittest.TestCase):
    def setUp(self):
        from scipy.io import loadmat
        self.mat_data1 = \
            loadmat('/Users/fpbatta/src/batlab/neuroseries/resources/test_data/restrict_ts_data_1.mat')
        self.mat_data_left = \
            loadmat('/Users/fpbatta/src/batlab/neuroseries/resources/test_data/restrict_ts_data_2.mat')
        self.mat_data_right = \
            loadmat('/Users/fpbatta/src/batlab/neuroseries/resources/test_data/restrict_ts_data_3.mat')

    def tearDown(self):
        pass

    def test_realign(self):
        """
        first simple realign case
        """

        d_a = self.mat_data1['d_a']
        d_a = d_a.reshape((len(d_a),))
        t_a = nts.Tsd(self.mat_data1['t_a'].astype(np.int64), d_a, columns=('data',))
        t_b = nts.Ts(self.mat_data1['t_b'].astype(np.int64))
        t_closest = t_a.realign(t_b, align='closest')
        # tt = self.mat_data1['t_closest'].astype(np.int64)
        # tt = tt.reshape((len(tt),))
        dt = self.mat_data1['d_closest'].reshape((len(self.mat_data1['d_closest'],)))
        self.assertTrue((t_closest['data'].values != dt).sum() < 10)
        np.testing.assert_array_almost_equal_nulp(t_closest['data'], dt)

        t_next = t_a.realign(t_b, align='next')
        # tt = self.mat_data1['t_next'].astype(np.int64)
        # tt = tt.reshape((len(tt),))
        dt = self.mat_data1['d_next'].reshape((len(self.mat_data1['d_next'],)))
        np.testing.assert_array_almost_equal_nulp(t_next['data'], dt)

        t_prev = t_a.realign(t_b, align='prev')
        # tt = self.mat_data1['t_prev'].astype(np.int64)
        # tt = tt.reshape((len(tt),))
        dt = self.mat_data1['d_prev'].reshape((len(self.mat_data1['d_prev'],)))
        np.testing.assert_array_almost_equal_nulp(t_prev['data'], dt)

    def test_realign_left(self):
        d_a = self.mat_data_left['d_a']
        d_a = d_a.reshape((len(d_a),))
        t_a = nts.Tsd(self.mat_data_left['t_a'].astype(np.int64), d_a, columns=('data',))
        t_b = nts.Ts(self.mat_data_left['t_b'].astype(np.int64))
        t_closest = t_a.realign(t_b)
        # tt = self.mat_data1['t_closest'].astype(np.int64)
        # tt = tt.reshape((len(tt),))

        # np.testing.assert_array_almost_equal_nulp(t_closest.index.values, tt)
        dt = self.mat_data1['d_closest'].reshape((len(self.mat_data1['d_closest'], )))
        self.assertTrue((t_closest['data'].values != dt).sum() < 10)
        np.testing.assert_array_almost_equal_nulp(t_closest['data'], dt)

    def test_realign_right(self):
        d_a = self.mat_data_right['d_a']
        d_a = d_a.reshape((len(d_a),))
        t_a = nts.Tsd(self.mat_data_right['t_a'].astype(np.int64), d_a, columns=('data',))
        t_b = nts.Ts(self.mat_data_right['t_b'].astype(np.int64))
        t_closest = t_a.realign(t_b)
        dt = self.mat_data1['d_closest'].reshape((len(self.mat_data1['d_closest'], )))
        self.assertTrue((t_closest['data'].values != dt).sum() < 10)
        np.testing.assert_array_almost_equal_nulp(t_closest['data'], dt)
