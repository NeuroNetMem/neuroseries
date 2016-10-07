import pandas as pd
import numpy as np
from warnings import warn


def format_timestamps(t, time_units=None, give_warning=True):

    if not time_units:
        time_units = 'us'

    t = t.astype(np.float64)
    if time_units == 'us':
        pass
    elif time_units == 'ms':
        t *= 1000
    elif time_units == 's':
        t *= 1000000
    else:
        raise ValueError('unrecognized time units type')
    t = t.round()
    if isinstance(t, (pd.Series, pd.DataFrame)):
        ts = t.index.values.astype(np.int64)
    else:
        ts = t.astype(np.int64)

    ts = ts.reshape((len(ts),))

    if not (np.diff(ts) >= 0).all():
        if give_warning:
            warn('timestamps are not sorted', UserWarning)
        ts.sort()
    return ts


def return_timestamps(t, units=None):

    if not units:
        units = 'us'  # TODO fix with global unit setting mechanism
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
        if isinstance(t, pd.Series):
            super().__init__(t, **kwargs)
        else:
            t = format_timestamps(t, time_units)
            super().__init__(index=t, data=d, **kwargs)
        self.index.name = "Time (us)"

    def times(self, units=None):
        return return_timestamps(self.index.values.astype(np.float64), units)

    def as_series(self):
        """
        :return: copy of the data in a DataFrame (strip Tsd class label)
        """
        return pd.Series(self, copy=True)

    def as_units(self, units=None):
        """
        returns a DataFrame with time expressed in the desired unit
        :param units: us (s), ms, or s
        :return: DataFrame with adjusted times
        """
        ss = self.as_series()
        t = self.index.values
        t = return_timestamps(t, units)
        ss.set_index(t, inplace=True)
        return ss

    def data(self):
        return self.values

    def realign(self, t, align='closest'):
        method = _get_restrict_method(align)
        ix = format_timestamps(t)

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
            s = tsd_r.iloc[:,col]
            return Tsd(s)
        return TsdFrame(tsd_r, copy=True)


# noinspection PyAbstractClass
class TsdFrame(pd.DataFrame):
    def __init__(self, t, d=None, time_units=None, **kwargs):
        if isinstance(t, pd.DataFrame):
            super().__init__(t, **kwargs)
        else:
            t = format_timestamps(t, time_units)
            super().__init__(index=t, data=d, **kwargs)
        self.index.name = "Time (us)"

    def times(self, units=None):
        return return_timestamps(self.index.values.astype(np.float64), units)

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
        t = return_timestamps(t, units)
        df.set_index(t, inplace=True)
        return df

    def data(self):
        if len(self.columns) == 1:
            return self.values.ravel()
        return self.values

    def realign(self, t, align='closest'):
        method = _get_restrict_method(align)
        ix = format_timestamps(t)

        rest_t = self.reindex(ix, method=method)
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
        return Tsd


# noinspection PyAbstractClass
class Ts(Tsd):
    def __init__(self, t, time_units=None, **kwargs):
        super().__init__(t, None, time_units=time_units, **kwargs)
