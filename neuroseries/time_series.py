import pandas as pd
import numpy as np
from warnings import warn
from pandas.core.internals import SingleBlockManager, BlockManager
from pandas.core.base import AccessorProperty, PandasObject


class BaseMethod(PandasObject):
    def __init__(self, data):
        self._data = data

    @staticmethod
    def func(*args, **kwargs):
        raise NotImplementedError('shuold have a function')

    def __call__(self, *args, **kwargs):
        if len(args) == 0:
            fc = self.func(self._data, **kwargs)
        else:
            fc = self.func(self._data, *args, **kwargs)
        return fc
    __doc__ = func.__doc__
    __call__.__doc__ = func.__doc__


def as_method(func):
    name = func.__name__.capitalize() + 'Method'
    cls = type(name, (BaseMethod,), {'func': staticmethod(func),
                                     '__doc__': func.__doc__})
    ap = AccessorProperty(cls, cls)
    return ap


class Range:
    interval = None
    cached_objects = []

    def __init__(self, a, b=None, time_units=None):
        if b:
            start = TimeUnits.format_timestamps(np.array((a,), dtype=np.int64).ravel(), time_units)
            end = TimeUnits.format_timestamps(np.array((b,), dtype=np.int64).ravel(), time_units)
            from neuroseries.interval_set import IntervalSet
            Range.interval = IntervalSet(start, end)
        else:
            Range.interval = a

    def __enter__(self):
        return Range.interval

    def __exit__(self, exc_type, exc_val, exc_tb):
        Range.interval = None
        for i in Range.cached_objects:
            i.invalidate_restrict_cache()
        self.cached_objects = []


class TimeUnits:
    default_time_units = 'us'

    def __init__(self, units):
        TimeUnits.default_time_units = units

    def __enter__(self):
        return self.default_time_units

    def __exit__(self, exc_type, exc_val, exc_tb):
        TimeUnits.default_time_units = 'us'

    @staticmethod
    def format_timestamps(t, units=None, give_warning=True):

        if not units:
            units = TimeUnits.default_time_units

        t = t.astype(np.float64)
        if units == 'us':
            pass
        elif units == 'ms':
            t *= 1000
        elif units == 's':
            t *= 1000000
        else:
            raise ValueError('unrecognized time units type')

        if isinstance(t, BlockManager):
            t = pd.DataFrame(t, copy=True)

        if isinstance(t, (pd.Series, pd.DataFrame)):
            ts = t.index.values.astype(np.int64)
            ts = ts.round()
        else:
            t = t.round()
            ts = t.astype(np.int64)

        ts = ts.reshape((len(ts),))

        if not (np.diff(ts) >= 0).all():
            if give_warning:
                warn('timestamps are not sorted', UserWarning)
            ts.sort()
        return ts

    @staticmethod
    def return_timestamps(t, units=None):

        if not units:
            units = TimeUnits.default_time_units
        if units == 'us':
            return t
        elif units == 'ms':
            return t / 1000.
        elif units == 's':
            return t / 1.0e6
        else:
            raise ValueError('Unrecognized units')


def _get_restrict_method(align):
    if align in ('closest', 'nearest'):
        method = 'nearest'
    elif align in ('next', 'bfill', 'backfill'):
        method = 'bfill'
    elif align in ('prev', 'ffill', 'pad'):
        method = 'pad'
    else:
        raise ValueError('Unrecognized restrict align method')
    return method


class Tsd(pd.Series):
    def __init__(self, t, d=None, time_units=None, **kwargs):
        if isinstance(t, (pd.Series, SingleBlockManager)):
            super().__init__(t, **kwargs)
        else:
            t = TimeUnits.format_timestamps(t, time_units)
            super().__init__(index=t, data=d, **kwargs)
        self.index.name = "Time (us)"
        self.r_cache = None

    def times(self, units=None):
        return TimeUnits.return_timestamps(self.index.values.astype(np.float64), units)

    def as_series(self):
        """
        :return: copy of the data in a DataFrame (strip Tsd class label)
        """
        return pd.Series(self, copy=True)

    def as_units(self, units=None):
        """
        returns a Series with time expressed in the desired unit
        :param units: us, ms, or s
        :return: Series with adjusted times
        """
        ss = self.as_series()
        t = self.index.values
        t = TimeUnits.return_timestamps(t, units)
        ss.index = t
        units_str = units
        if not units_str:
            units_str = 'us'
        ss.index.name = "Time (" + units_str + ")"
        return ss

    def data(self):
        return self.values

    def realign(self, t, align='closest'):
        method = _get_restrict_method(align)
        ix = TimeUnits.format_timestamps(t.index.values)

        rest_t = self.reindex(ix, method=method)
        return rest_t

    def restrict(self, iset, keep_labels=False):
        ix = iset.in_interval(self)
        tsd_r = pd.DataFrame(self, copy=True)
        col = tsd_r.columns[0]
        tsd_r['interval'] = ix
        ix = ~np.isnan(ix)
        tsd_r = tsd_r[ix]
        if not keep_labels:
            s = tsd_r.iloc[:, col]
            return Tsd(s)
        return TsdFrame(tsd_r, copy=True)

    @property
    def r(self):
        if Range.interval is None:
            raise ValueError('no range interval set')
        if self.r_cache is None:
            self.r_cache = self.restrict(Range.interval)
            Range.cached_objects.append(self)

        return self.r_cache

    def invalidate_restrict_cache(self):
        self.r_cache = None

    @property
    def _constructor(self):
        return Tsd


# noinspection PyAbstractClass
class TsdFrame(pd.DataFrame):
    def __init__(self, t, d=None, time_units=None, **kwargs):
        if isinstance(t, (pd.DataFrame, SingleBlockManager, BlockManager)):
            super().__init__(t, **kwargs)
        else:
            t = TimeUnits.format_timestamps(t, time_units)
            super().__init__(index=t, data=d, **kwargs)
        self.index.name = "Time (us)"
        self.r_cache = None

    def times(self, units=None):
        return TimeUnits.return_timestamps(self.index.values.astype(np.float64), units)

    def as_dataframe(self):
        """
        :return: copy of the data in a DataFrame (strip Tsd class label)
        """
        return pd.DataFrame(self, copy=True)

    def as_units(self, units=None):
        """
        returns a DataFrame with time expressed in the desired unit
        :param units: us (s), ms, or s
        :return: DataFrame with adjusted times
        """
        df = self.as_dataframe()
        t = self.index.values
        t = TimeUnits.return_timestamps(t, units)
        df.set_index(t, inplace=True)
        units_str = units
        if not units_str:
            units_str = 'us'
        df.index.name = "Time (" + units_str + ")"
        return df

    def data(self):
        if len(self.columns) == 1:
            return self.values.ravel()
        return self.values

    def realign(self, t, align='closest'):
        method = _get_restrict_method(align)
        ix = TimeUnits.format_timestamps(t)

        rest_t = self.reindex(ix, method=method, columns=self.columns.values)
        return rest_t

    def restrict(self, iset, keep_labels=False):
        ix = iset.in_interval(self)
        tsd_r = pd.DataFrame(self, copy=True)
        tsd_r['interval'] = ix
        ix = ~np.isnan(ix)
        tsd_r = tsd_r[ix]
        if not keep_labels:
            del tsd_r['interval']
        return TsdFrame(tsd_r, copy=True)

    @property
    def _constructor(self):
        return TsdFrame

    @property
    def _constructor_sliced(self):
        return Tsd

    @property
    def r(self):
        if Range.interval is None:
            raise ValueError('no range interval set')
        if self.r_cache is None:
            self.r_cache = self.restrict(Range.interval)
            Range.cached_objects.append(self)

        return self.r_cache

    def invalidate_restrict_cache(self):
        self.r_cache = None


# noinspection PyAbstractClass
class Ts(Tsd):
    def __init__(self, t, time_units=None, **kwargs):
        super().__init__(t, None, time_units=time_units, **kwargs)


def gaps(data, min_gap, method='absolute'):
    """
    finds gaps in a tsd
    :param data: a Tsd/TsdFrame
    :param min_gap: the minimum gap that will be considered
    :param method: 'absolute': min gap is expressed in time (us), 'median',
    min_gap expressed in units of the median inter-sample event
    :return: an IntervalSet containing the gaps in the TSd
    """
    dt = np.diff(data.times(units='us'))

    if method == 'absolute':
        pass
    elif method == 'median':
        md = np.median(dt)
        min_gap *= md
    else:
        raise ValueError('unrecognized method')

    ix = np.where(dt > min_gap)
    t = data.times()
    st = t[ix] + 1
    en = t[(np.array(ix) + 1)] - 1
    from neuroseries.interval_set import IntervalSet
    return IntervalSet(st, en)


# noinspection PyTypeChecker
Tsd.gaps = as_method(gaps)
TsdFrame.gaps = as_method(gaps)

def support(data, min_gap, method='absolute'):
    """
    find the smallest (to a min_gap resolution) IntervalSet containing all the times in the Tsd
    :param data: a Tsd/TsdFrame
    :param min_gap: the minimum gap that will be considered
    :param method: 'absolute': min gap is expressed in time (us), 'median',
    min_gap expressed in units of the median inter-sample event
    :return: an IntervalSet
    """

    here_gaps = gaps(data, min_gap, method=method)
    t = data.times('us')
    from neuroseries.interval_set import IntervalSet
    span = IntervalSet(t[0] - 1, t[-1] + 1)
    support_here = span.set_diff(here_gaps)
    return support_here


# noinspection PyTypeChecker
Tsd.support = as_method(support)
TsdFrame.support = as_method(support)