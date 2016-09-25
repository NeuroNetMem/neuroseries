import pandas as pd
import numpy as np
from warnings import warn


def format_timestamps(t, time_units='usec', give_warning=True):
    t = t.astype(np.float64)
    if time_units == 'usec':
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


# noinspection PyAbstractClass
class Tsd(pd.DataFrame):
    def __init__(self, t, d=None, time_units='usec', **kwargs):
        if isinstance(t, pd.DataFrame):
            super().__init__(t, **kwargs)
        else:
            t = format_timestamps(t, time_units)
            super().__init__(index=t, data=d, **kwargs)
            self.index.name = "Time"

    def times(self, units='usec'):
        if units == 'usec':
            return self.index.values.astype(np.float64)
        elif units == 'ms':
            return self.index.values.astype(np.float64) / 1.0e3
        elif units == 's':
            return self.index.values.astype(np.float64) / 1.0e6
        else:
            raise ValueError('Unrecognized units')

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
        return Tsd(tsd_r, copy=True)


# noinspection PyAbstractClass
class Ts(Tsd):
    def __init__(self, t, time_units='usec', **kwargs):
        super().__init__(t, None, time_units=time_units, columns=('time',), **kwargs)
