import pandas as pd
import numpy as np


from .interval_set import IntervalSet

def tsd_by_trial(data, events, window):
    """

    Args:
        data: the data to be cut
        events: the events
        window: the interval around the events for cutting. Tuple (start, stop)

    Returns:
        the cut data as DataFrame
    """
    intervals = IntervalSet(events + window[0], events + window[1])
    data_by_trial = data.restrict(intervals, keep_labels=True)
    data_by_trial['event_time'] = events[data_by_trial['interval']].values
    data_by_trial['latency'] = data_by_trial.index.values - data_by_trial['event_time'].values
    return data_by_trial