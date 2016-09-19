import pandas as pd
import numpy as np
from warnings import warn


def _format_timestamps(t, time_units='usec'):
    if isinstance(t, (pd.Series, pd.DataFrame)):
        ts = t.index.values.astype(np.int64)
    else:
        ts = t.astype(np.int64)

    ts = ts.reshape((len(ts),))
    if time_units == 'usec':
        pass
    elif time_units == 'ms':
        ts *= 1000
    elif time_units == 's':
        ts *= 1000000
    else:
        raise ValueError('unrecognized time units type')
    if not (np.diff(ts) >= 0).all():
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


class Tsd(pd.DataFrame):
    def __init__(self, t, d, time_units='usec', **kwargs):
        t = _format_timestamps(t, time_units)
        super().__init__(index=t, data=d, **kwargs)

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
        return self.values

    def realign(self, t, align='closest'):
        method = _get_restrict_method(align)
        ix = _format_timestamps(t)

        rest_t = self.reindex(ix, method=method)
        return rest_t


class Ts(Tsd):
    def __init__(self, t, time_units='usec', **kwargs):
        super().__init__(t, None, time_units=time_units, columns=('time',), **kwargs)
