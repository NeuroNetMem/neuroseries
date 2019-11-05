import pandas as pd
import numpy as np


from .interval_set import IntervalSet

def tsd_by_trial(data, events, range):
    intervals = IntervalSet(events+range[0], events+range[1])
    data_by_trial = data.restrict(intervals, keep_labels=True)
    data_by_trial['event_time'] = events[data_by_trial['interval']].values
    data_by_trial['latency'] = data_by_trial.index.values - data_by_trial['event_time'].values
    return data_by_trial