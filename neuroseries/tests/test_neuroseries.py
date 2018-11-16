import unittest
from parameterized import parameterized
import numpy as np
import pandas as pd

import neuroseries as nts
import os

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
        self.assertIsInstance(ts, pd.Series, msg="ts doesn't return DataFrame")
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
        internally data are stored as us
        """
        a = np.random.randint(0, 1000, 100)
        a.sort()
        ts = nts.Ts(a/1000, time_units='ms')
        np.testing.assert_array_almost_equal_nulp(ts.index.values, a)
        ts = nts.Ts(a/1000000, time_units='s')
        # np.testing.assert_array_almost_equal_nulp(ts.index.values, a.astype(np.int64), nulp=100)
        self.assertTrue(np.all(ts.index.values >= a.astype(np.int64)-1))
        self.assertTrue(np.all(ts.index.values <= a.astype(np.int64)+1))
    @staticmethod
    def test_create_ts_time_units_double():
        """
        conversion of time units from floating point type
        """
        a = np.floor(np.random.rand(100) * 1000000)
        a.sort()
        ts = nts.Ts(a.copy(), time_units='ms')
        # noinspection PyTypeChecker
        np.testing.assert_array_almost_equal_nulp(ts.index.values/1000, a)

    @staticmethod
    def test_create_ts_from_non_sorted():
        """
        if ts are not sorted, a warning should be returned and the timestamps sorted for you
        """
        a = np.random.randint(0, 1000, 100)
        # with self.assertWarns(UserWarning):
        #     ts = nts.Ts(a)
        ts = nts.Ts(a)

        np.testing.assert_array_almost_equal_nulp(np.sort(a), ts.index.values)

    def test_create_ts_wrong_units(self):
        """
        if the units are unsupported it should raise ValueError
        """
        a = np.random.randint(0, 10000000, 100)
        a.sort()
        # noinspection PyUnusedLocal
        ts = 1
        with self.assertRaises(ValueError):
            ts = nts.Ts(a, time_units='min')
        self.assertTrue(ts)

    def test_times_data(self):
        """
        tests the times and data properties
        """
        a = np.random.randint(0, 10000000, 100)
        a.sort()
        b = np.random.randn(100)
        t = nts.Tsd(a, b)
        np.testing.assert_array_almost_equal_nulp(b, t.data())
        np.testing.assert_array_almost_equal_nulp(a, t.times())
        np.testing.assert_array_almost_equal_nulp(a/1000., t.times(units='ms'))
        np.testing.assert_array_almost_equal_nulp(a/1.0e6, t.times(units='s'))
        with self.assertRaises(ValueError):
            t.times(units='banana')


class TsRestrictTestCase(unittest.TestCase):
    def setUp(self):
        from scipy.io import loadmat
        self.mat_data1 = \
            loadmat(os.path.join(nts.get_test_data_dir(), 'restrict_ts_data_1.mat'))
        self.mat_data_left = \
            loadmat(os.path.join(nts.get_test_data_dir(), 'restrict_ts_data_2.mat'))
        self.mat_data_right = \
            loadmat(os.path.join(nts.get_test_data_dir(), 'restrict_ts_data_3.mat'))

    def tearDown(self):
        pass

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def test_realign(self, data_class):
        """
        first simple realign case
        """

        d_a = self.mat_data1['d_a']
        d_a = d_a.reshape((len(d_a),))
        t_a = data_class(self.mat_data1['t_a'].astype(np.int64), d_a)
        t_b = nts.Ts(self.mat_data1['t_b'].astype(np.int64))
        t_closest = t_a.realign(t_b, align='closest')
        dt = self.mat_data1['d_closest'].reshape((len(self.mat_data1['d_closest'],)))
        self.assertTrue((t_closest.values.ravel() != dt).sum() < 10)
        np.testing.assert_array_almost_equal_nulp(t_closest.values.ravel(), dt)

        t_next = t_a.realign(t_b, align='next')
        dt = self.mat_data1['d_next'].reshape((len(self.mat_data1['d_next'],)))
        np.testing.assert_array_almost_equal_nulp(t_next.values.ravel(), dt)

        t_prev = t_a.realign(t_b, align='prev')
        dt = self.mat_data1['d_prev'].reshape((len(self.mat_data1['d_prev'],)))
        np.testing.assert_array_almost_equal_nulp(t_prev.values.ravel(), dt)

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def test_realign_left(self, data_class):
        d_a = self.mat_data_left['d_a']
        d_a = d_a.reshape((len(d_a),))
        t_a = data_class(self.mat_data_left['t_a'].astype(np.int64), d_a)
        t_b = nts.Ts(self.mat_data_left['t_b'].astype(np.int64))
        t_closest = t_a.realign(t_b)
        dt = self.mat_data_left['d_closest'].ravel()
        self.assertTrue((t_closest.values.ravel() != dt).sum() < 10)
        np.testing.assert_array_almost_equal_nulp(t_closest.values.ravel(), dt)

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def test_realign_right(self, data_class):
        d_a = self.mat_data_right['d_a']
        d_a = d_a.reshape((len(d_a),))
        t_a = data_class(self.mat_data_right['t_a'].astype(np.int64), d_a)
        t_b = nts.Ts(self.mat_data_right['t_b'].astype(np.int64))
        t_closest = t_a.realign(t_b)
        dt = self.mat_data_right['d_closest'].ravel()
        self.assertTrue((t_closest.values.ravel() != dt).sum() < 10)
        np.testing.assert_array_almost_equal_nulp(t_closest.values.ravel(), dt)

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def test_realign_wrong_units(self, data_class):
        d_a = self.mat_data1['d_a']
        d_a = d_a.reshape((len(d_a),))
        t_a = data_class(self.mat_data1['t_a'].astype(np.int64), d_a)
        t_b = nts.Ts(self.mat_data1['t_b'].astype(np.int64))
        # noinspection PyUnusedLocal
        t_closest = 1
        with self.assertRaises(ValueError):
            t_closest = t_a.realign(t_b, align='banana')
        self.assertTrue(t_closest)


class IntervalSetOpsTestCase(unittest.TestCase):
    def setUp(self):
        from scipy.io import loadmat
        self.mat_data1 = loadmat(os.path.join(nts.get_test_data_dir(), 'interval_set_data_1.mat'))

        # note that data are n x 1 here, need to be converted to 1-D in constructor
        self.a1 = self.mat_data1['a1']
        self.b1 = self.mat_data1['b1']
        self.int1 = nts.IntervalSet(self.a1, self.b1, expect_fix=True)

        self.a2 = self.mat_data1['a2']
        self.b2 = self.mat_data1['b2']
        self.int2 = nts.IntervalSet(self.a2, self.b2, expect_fix=True)

    def tearDown(self):
        pass

    def test_create_interval_set(self):
        """
        create an interval set from start and end points "to be fixed"
        """
        a_i1 = self.mat_data1['a_i1'].ravel()
        b_i1 = self.mat_data1['b_i1'].ravel()
        np.testing.assert_array_almost_equal_nulp(a_i1, self.int1['start'])
        np.testing.assert_array_almost_equal_nulp(b_i1, self.int1['end'])

        a_i2 = self.mat_data1['a_i2'].ravel()
        b_i2 = self.mat_data1['b_i2'].ravel()
        np.testing.assert_array_almost_equal_nulp(a_i2, self.int2['start'])
        np.testing.assert_array_almost_equal_nulp(b_i2, self.int2['end'])

    def test_create_interval_set_from_scalars(self):
        int1 = nts.IntervalSet(100, 2100)
        self.assertIsInstance(int1, nts.IntervalSet)
        np.testing.assert_array_almost_equal_nulp(np.array((100,)), int1['start'])
        np.testing.assert_array_almost_equal_nulp(np.array((2100,)), int1['end'])

    def test_iterator(self):
        a_i1 = self.mat_data1['a_i1'].ravel().astype(np.int64)
        b_i1 = self.mat_data1['b_i1'].ravel().astype(np.int64)
        for i, int_i in self.int1.iterrows():
            self.assertEqual(a_i1[i], int_i['start'])
            self.assertEqual(b_i1[i], int_i['end'])

    def test_timespan_tot_length(self):
        """
        return the total length and the timespan of the interval set
        """
        a_i1 = self.mat_data1['a_i1'].ravel()
        b_i1 = self.mat_data1['b_i1'].ravel()
        time_span = self.int1.time_span()
        self.assertIsInstance(time_span, nts.IntervalSet)
        self.assertEqual(time_span['start'][0], a_i1[0])
        self.assertEqual(time_span['end'][0], b_i1[-1])
        tot_l = (b_i1 - a_i1).sum()
        self.assertAlmostEqual(self.int1.tot_length(), tot_l)

    def test_intersect(self):
        """
        intersection of the interval sets
        """
        a_intersect = self.mat_data1['a_intersect'].ravel()
        b_intersect = self.mat_data1['b_intersect'].ravel()
        int_intersect = self.int1.intersect(self.int2)
        self.assertIsInstance(int_intersect, nts.IntervalSet)

        np.testing.assert_array_almost_equal_nulp(int_intersect['start'], a_intersect)
        np.testing.assert_array_almost_equal_nulp(int_intersect['end'], b_intersect)

        int_intersect = self.int2.intersect(self.int1)

        np.testing.assert_array_almost_equal_nulp(int_intersect['start'], a_intersect)
        np.testing.assert_array_almost_equal_nulp(int_intersect['end'], b_intersect)

    def test_union(self):
        """
        union of the interval sets
        """
        a_union = self.mat_data1['a_union'].ravel()
        b_union = self.mat_data1['b_union'].ravel()
        int_union = self.int1.union(self.int2)
        self.assertIsInstance(int_union, nts.IntervalSet)

        np.testing.assert_array_almost_equal_nulp(int_union['start'], a_union)
        np.testing.assert_array_almost_equal_nulp(int_union['end'], b_union)

        int_union = self.int2.union(self.int1)

        np.testing.assert_array_almost_equal_nulp(int_union['start'], a_union)
        np.testing.assert_array_almost_equal_nulp(int_union['end'], b_union)

    def test_setdiff(self):
        """
        diffs of the interval sets
        """
        a_diff1 = self.mat_data1['a_diff1'].ravel()
        b_diff1 = self.mat_data1['b_diff1'].ravel()
        a_diff2 = self.mat_data1['a_diff2'].ravel()
        b_diff2 = self.mat_data1['b_diff2'].ravel()

        int_diff1 = self.int1.set_diff(self.int2)
        self.assertIsInstance(int_diff1, nts.IntervalSet)

        np.testing.assert_array_almost_equal_nulp(int_diff1['start'], a_diff1)
        np.testing.assert_array_almost_equal_nulp(int_diff1['end'], b_diff1)

        int_diff2 = self.int2.set_diff(self.int1)

        np.testing.assert_array_almost_equal_nulp(int_diff2['start'], a_diff2)
        np.testing.assert_array_almost_equal_nulp(int_diff2['end'], b_diff2)


class IntervalSetDropMergeTestCase(unittest.TestCase):
    def setUp(self):
        from scipy.io import loadmat
        self.mat_data1 = loadmat(os.path.join(nts.get_test_data_dir(),
            'interval_set_data_dropmerge1.mat'))

        # note that data are n x 1 here, need to be converted to 1-D in constructor
        self.a1 = self.mat_data1['a1'].ravel()
        self.b1 = self.mat_data1['b1'].ravel()
        self.int1 = nts.IntervalSet(self.a1, self.b1, expect_fix=True)

        self.a1_drop = self.mat_data1['a_i1_drop'].ravel()
        self.b1_drop = self.mat_data1['b_i1_drop'].ravel()
        self.int1_drop = nts.IntervalSet(self.a1_drop, self.b1_drop, expect_fix=True)

        self.a1_merge = self.mat_data1['a_i1_merge'].ravel()
        self.b1_merge = self.mat_data1['b_i1_merge'].ravel()
        self.int1_merge = nts.IntervalSet(self.a1_merge, self.b1_merge, expect_fix=True)

    def tearDown(self):
        pass

    def test_drop_short(self):
        i_drop = self.int1.drop_short_intervals(threshold=2.e3)
        self.assertIsInstance(i_drop, nts.IntervalSet)
        np.testing.assert_array_almost_equal_nulp(i_drop['start'], self.a1_drop)
        np.testing.assert_array_almost_equal_nulp(i_drop['end'], self.b1_drop)

    def test_merge_close(self):
        i_merge = self.int1.merge_close_intervals(threshold=3.e3)
        self.assertIsInstance(i_merge, nts.IntervalSet)
        np.testing.assert_array_almost_equal_nulp(i_merge['start'], self.a1_merge)
        np.testing.assert_array_almost_equal_nulp(i_merge['end'], self.b1_merge)


class TsdUnitsTestCase(unittest.TestCase):
    def setUp(self):
        from scipy.io import loadmat
        self.mat_data1 = loadmat(os.path.join(nts.get_test_data_dir(), 'interval_set_data_1.mat'))
        self.tsd_t = self.mat_data1['t'].ravel()
        self.tsd_d = self.mat_data1['d'].ravel()

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def test_as_dataframe(self, data_class):
        self.tsd = data_class(self.tsd_t, self.tsd_d)
        if data_class == nts.Tsd:
            df = self.tsd.as_series()
        else:
            df = self.tsd.as_dataframe()
        np.testing.assert_array_almost_equal_nulp(df.values, self.tsd.values)
        np.testing.assert_array_almost_equal_nulp(df.index.values, self.tsd.index.values)

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def test_units_context(self, data_class):
        self.tsd = data_class(self.tsd_t, self.tsd_d)
        with nts.TimeUnits('ms'):
            t = self.tsd.times()
            # noinspection PyTypeChecker
            np.testing.assert_array_almost_equal_nulp(self.tsd_t/1000., t)

    @staticmethod
    def test_times_units_ts():
        """
        tests the units calling of times
        """
        a = np.random.randint(0, 10000000, 100)
        a.sort()
        ts = nts.Ts(a)

        np.testing.assert_array_almost_equal_nulp(a, ts.times('us'))
        np.testing.assert_array_almost_equal_nulp(a/1000., ts.times('ms'))
        np.testing.assert_array_almost_equal_nulp(a/1.e6, ts.times('s'))

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def test_as_units_ts(self, data_class):
        """
        as_units returns tsd dataframe
        :return:
        """
        self.tsd = data_class(self.tsd_t, self.tsd_d)
        tsd_ms = self.tsd.as_units('ms')
        if data_class == nts.Tsd:
            self.assertIsInstance(tsd_ms, pd.Series)
        else:
            self.assertIsInstance(tsd_ms, pd.DataFrame)
        # noinspection PyTypeChecker
        np.testing.assert_array_almost_equal_nulp(self.tsd_t/1000., tsd_ms.index.values)

        tsd_s = self.tsd.as_units('s')
        # noinspection PyTypeChecker
        np.testing.assert_array_almost_equal_nulp(self.tsd_t/1.e6, tsd_s.index.values)


class TsdSupportTestCase(unittest.TestCase):
    def setUp(self):
        a1 = np.arange(1, 500000, 100)
        a2 = np.arange(800000, 2300000, 100)
        a3 = np.arange(5200000, 8900000, 100)
        self.t = np.hstack((a1, a2, a3))
        self.d = np.random.randn(*self.t.shape)

    def tearDown(self):
        pass

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def test_gaps(self, data_class):
        self.t1 = data_class(self.t, self.d)
        gaps = self.t1.gaps(500, method='absolute')
        st = gaps['start']
        en = gaps['end']
        np.testing.assert_array_almost_equal_nulp(st, np.array((499902, 2299901)))
        np.testing.assert_array_almost_equal_nulp(en, np.array((799999, 5199999)))

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def test_support(self, data_class):
        self.t1 = data_class(self.t, self.d)
        support = self.t1.support(min_gap=500, method='absolute')
        np.testing.assert_array_almost_equal_nulp(support['start'], np.array((0, 799999, 5199999)))
        np.testing.assert_array_almost_equal_nulp(support['end'], np.array((499902, 2299901, 8899901)))


class TsdIntervalSetRestrictTestCase(unittest.TestCase):
    def setUp(self):
        from scipy.io import loadmat
        self.mat_data1 = loadmat(os.path.join(nts.get_test_data_dir(),
            'interval_set_data_1.mat'))

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
        pass

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def testRestrict(self, data_class):
        """
        IntervalSet restrict of tsd
        """
        self.tsd = data_class(self.tsd_t, self.tsd_d)
        t_r1 = self.mat_data1['t_r1'].ravel()
        d_r1 = self.mat_data1['d_r1'].ravel()
        tsd_r1 = self.tsd.restrict(self.int1)
        self.assertIsInstance(tsd_r1, data_class)
        self.assertEqual(tsd_r1.index.name, "Time (us)")
        np.testing.assert_array_almost_equal_nulp(t_r1, tsd_r1.times())
        np.testing.assert_array_almost_equal_nulp(d_r1, tsd_r1.values.ravel())

        t_r2 = self.mat_data1['t_r2'].ravel()
        d_r2 = self.mat_data1['d_r2'].ravel()
        tsd_r2 = self.tsd.restrict(self.int2)
        np.testing.assert_array_almost_equal_nulp(t_r2, tsd_r2.times())
        np.testing.assert_array_almost_equal_nulp(d_r2, tsd_r2.values.ravel())

    @parameterized.expand([
        (nts.Tsd,),
        (nts.TsdFrame,)
    ])
    def testRange(self, data_class):
        self.tsd = data_class(self.tsd_t, self.tsd_d)
        range_interval = nts.IntervalSet(9.e8, 3.e9)

        int1_r = self.int1.intersect(range_interval)
        tsd_r = self.tsd.restrict(range_interval)
        tsd_r_r1 = self.tsd.restrict(int1_r)

        with nts.Range(range_interval):
            np.testing.assert_array_almost_equal_nulp(self.tsd.r.times(), tsd_r.times())
            np.testing.assert_array_almost_equal_nulp(self.int1.r['start'], int1_r['start'])
            np.testing.assert_array_almost_equal_nulp(self.int1.r['end'], int1_r['end'])

            np.testing.assert_array_almost_equal_nulp(self.tsd.r.restrict(self.int1.r).times(),
                                                      tsd_r_r1.times())

            # testing caching
            self.assertIsNotNone(self.tsd.r_cache)
            self.assertIsNotNone(self.int1.r_cache)
            np.testing.assert_array_almost_equal_nulp(self.tsd.r.times(), tsd_r.times())
            np.testing.assert_array_almost_equal_nulp(self.int1.r['start'], int1_r['start'])
            np.testing.assert_array_almost_equal_nulp(self.int1.r['end'], int1_r['end'])
            np.testing.assert_array_almost_equal_nulp(self.tsd.r.restrict(self.int1.r).times(),
                                                      tsd_r_r1.times())

        self.assertIsNone(self.tsd.r_cache)
        self.assertIsNone(self.int1.r_cache)

        with nts.Range(9.e8, 3.e9):
            np.testing.assert_array_almost_equal_nulp(self.tsd.r.times(), tsd_r.times())

if __name__ == '__main__':
    unittest.main()
