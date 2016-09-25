import pandas as pd
import numpy as np
from warnings import warn
from .time_series import format_timestamps


class IntervalSet(pd.DataFrame):
    """
    a DataFrame representing a (irregular) set of time intervals in elapsed time, with relative operations
    """
    def __init__(self, start, end, time_units='usec', expect_fix=False, **kwargs):
        """
        makes a interval_set. if start and end and not aligned, meaning that len(start) == len(end),
        end[i] > start[i] and start[i+1] > end[i], or start and end are not sorted,
        will try to "fix" the data by eliminating some of the start and end data point
        :param start: array containing the beginning of each interval
        :param end: array containing the end of each interval
        :param expect_fix: if False, will give a warning when a fix is needed (default: False)
        """
        start = format_timestamps(np.array(start, dtype=np.int64).ravel(), time_units,
                                  give_warning=not expect_fix)
        end = format_timestamps(np.array(end, dtype=np.int64).ravel(), time_units,
                                give_warning=not expect_fix)


        to_fix = False
        msg = ''
        if not (np.diff(start) > 0).all():
            msg = "start is not sorted"
            to_fix = True
        if not (np.diff(end) > 0).all():
            msg = "end is not sorted"
            to_fix = True
        if len(start) != len(end):
            msg = "start and end not of the same length"
            to_fix = True
        else:
            # noinspection PyUnresolvedReferences
            if (start > end).any():
                msg = "some ends precede the relative start"
                to_fix = True
            # noinspection PyUnresolvedReferences
            if (end[:-1] > start[1:]).any():
                msg = "some start precede the previous end"
                to_fix = True

        if to_fix and not expect_fix:
            warn(msg, UserWarning)

        if to_fix:
            start.sort()
            end.sort()
            mm = np.hstack((start, end))
            mz = np.hstack((np.zeros_like(start), np.ones_like(end)))
            mx = mm.argsort()
            mm = mm[mx]
            mz = mz[mx]
            good_ix = np.nonzero(np.diff(mz) == 1)[0]
            start = mm[good_ix]
            end = mm[good_ix+1]

        # super().__init__({'start': start, 'end': end}, **kwargs)
        # self = self[['start', 'end']]
        super().__init__(data=np.vstack((start, end)).T, columns=('start', 'end'))

    def time_span(self):
        """
        Time span of the interval set
        :return:  an IntervalSet with a single interval encompassing the whole IntervalSet
        """
        s = self['start'][0]
        e = self['end'].iloc[-1]
        return IntervalSet(s, e)

    def tot_length(self, time_units='usec'):
        """
        Total elapsed time in the set
        :param time_units: the time units to return the result in ('usec' [default], 'ms', 's')
        :return: the total length
        """
        tot_l = (self['end'] - self['start']).astype(np.float64).sum()
        if time_units == 'usec':
            pass
        elif time_units == 'ms':
            tot_l /= 1.e3
        elif time_units == 's':
            tot_l /= 1.e6
        else:
            raise ValueError("Unrecognized time units")
        return tot_l

    def intersect(self, *a):
        """
        set intersection
        :param a: the IntervalSet to intersect self with, or a tuple of
        :return: the intersection IntervalSet
        """

        i_sets = [self]
        i_sets.extend(a)
        n_sets = len(i_sets)
        time1 = [i_set['start'] for i_set in i_sets]
        time2 = [i_set['end'] for i_set in i_sets]
        time1.extend(time2)
        time = np.hstack(time1)

        start_end = np.hstack((np.ones(len(time)/2, dtype=np.int32),
                              -1 * np.ones(len(time)/2, dtype=np.int32)))

        df = pd.DataFrame({'time': time, 'start_end': start_end})
        df.sort_values(by='time', inplace=True)
        df.reset_index(inplace=True, drop=True)
        df['cumsum'] = df['start_end'].cumsum()
        # noinspection PyTypeChecker
        ix = np.nonzero(df['cumsum'] == n_sets)[0]
        start = df['time'][ix]
        # noinspection PyTypeChecker
        end = df['time'][ix+1]

        return IntervalSet(start, end)

    def union(self, *a):
        """
        set union
        :param a:  the IntervalSet to intersect self with, or a tuple of
        :return: the union IntervalSet
        """
        i_sets = [self]
        i_sets.extend(a)
        time = np.hstack([i_set['start'] for i_set in i_sets] +
                         [i_set['end'] for i_set in i_sets])

        start_end = np.hstack((np.ones(len(time)/2, dtype=np.int32),
                              -1 * np.ones(len(time)/2, dtype=np.int32)))

        df = pd.DataFrame({'time': time, 'start_end': start_end})
        df.sort_values(by='time', inplace=True)
        df.reset_index(inplace=True, drop=True)
        df['cumsum'] = df['start_end'].cumsum()
        # noinspection PyTypeChecker
        ix_stop = np.nonzero(df['cumsum'] == 0)[0]
        ix_start = np.hstack((0, ix_stop[:-1]+1))
        start = df['time'][ix_start]
        stop = df['time'][ix_stop]

        return IntervalSet(start, stop)

    def set_diff(self, a):
        """
        set different
        :param a: the interval set to set-subtract from self
        :return: the difference IntervalSet
        """
        i_sets = (self, a)
        time = np.hstack([i_set['start'] for i_set in i_sets] +
                         [i_set['end'] for i_set in i_sets])
        start_end1 = np.hstack((np.ones(len(i_sets[0]), dtype=np.int32),
                                -1 * np.ones(len(i_sets[0]), dtype=np.int32)))
        start_end2 = np.hstack((-1 * np.ones(len(i_sets[1]), dtype=np.int32),
                                np.ones(len(i_sets[1]), dtype=np.int32)))
        start_end = np.hstack((start_end1, start_end2))
        df = pd.DataFrame({'time': time, 'start_end': start_end})
        df.sort_values(by='time', inplace=True)
        df.reset_index(inplace=True, drop=True)
        df['cumsum'] = df['start_end'].cumsum()
        # noinspection PyTypeChecker
        ix = np.nonzero(df['cumsum'] == 1)[0]
        start = df['time'][ix]
        # noinspection PyTypeChecker
        end = df['time'][ix+1]

        return IntervalSet(start, end)

    def in_interval(self, tsd):
        """
        finds out in which element of the interval set each point in a time series fits, NaNs for those
        that don't fit a interval
        :param tsd: the tsd to be binned
        :return: an array with the interval index labels for each time stamp (NaN) for timestamps not in
        IntervalSet.
        """
        bins = self.values.ravel()
        ix = np.array(pd.cut(tsd.index, bins, labels=np.arange(len(bins) - 1, dtype=np.int64)))
        ix[np.floor(ix / 2) * 2 != ix] = np.NaN
        ix = np.floor(ix/2)
        return ix
