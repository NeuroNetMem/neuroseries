# noinspection PyPackageRequirements
from ipywidgets import interact
# noinspection PyPackageRequirements
from bokeh.models import Range1d
# noinspection PyPackageRequirements
from bokeh.io import push_notebook, show
# noinspection PyPackageRequirements
from bokeh.charts import TimeSeries
# noinspection PyPackageRequirements
from bokeh.plotting import figure
# noinspection PyPackageRequirements
from bokeh.models import ColumnDataSource, BoxAnnotation
# noinspection PyUnresolvedReferences,PyPackageRequirements
from bokeh.palettes import Spectral11

import pandas as pd
import numpy as np
import warnings


def FrameViewer(df, title="EEG", ylabel='voltage (mV)', xlabel='time (s)'):

    x_min = df.index[0]
    x_max = df.index[-1]
    default_interval = 1
    ts = TimeSeries(
        df, title=title,
        legend='top_left', ylabel=ylabel,
        xlabel=xlabel, x_range=Range1d(x_min, x_min+default_interval),
        plot_height=400)

    # noinspection PyShadowingNames
    def update_in(x_min=x_min, x_interval=default_interval):
        ts.x_range.start = x_min
        ts.x_range.end = x_min + x_interval
        push_notebook()

    show(ts, notebook_handle=True)
    interact(update_in, x_min=(x_min, x_max, 0.5), x_interval=(0.2, 5, 0.2))


# noinspection PyPep8Naming
def FrameViewerLong(df, title="EEG", ylabel='voltage (mV)', xlabel=None, downsample=10, units='s',
                    spread=0, annotations=None):

    from oio.open_ephys_io import ContinuousFile, load_continuous_tsd, is_sequence
    from .interval_set import IntervalSet
    # from .time_series import TsdFrame
    from .time_series import TimeUnits as tu

    if xlabel is None:
        xlabel = 'Time (' + units + ')'
    max_time = 30

    if is_sequence(df):
        if isinstance(df[0], str):
            df = [ContinuousFile(f) for f in df]
        x_min_df = df[0].start_time(units=units)
        x_max_df = df[0].end_time(units=units)
    else:
        x_min_df = df.start_time(units=units)
        x_max_df = df.end_time(units=units)

    if isinstance(df, pd.DataFrame):
        df = df.as_units(units)
        df1 = df[df.index < x_min_df + max_time]  # TODO use restrict
    else:
        df1 = load_continuous_tsd(df, t_min=tu.format_timestamps(x_min_df, units=units),
                                  t_max=tu.format_timestamps(x_min_df + max_time, units=units),
                                  downsample=downsample).as_units(units)

    default_interval = 1
    plot = figure(plot_height=400, plot_width=700, title=title,
                  tools="crosshair,pan,reset,save,box_zoom", x_axis_label=xlabel,
                  y_axis_label=ylabel)

    lines = []
    l = 0
    t = df1.index

    spread_vec = np.arange(len(df1.columns)) * spread
    for ix, x in enumerate(df1.columns):
        dd = {'t': t, x: df1[x] + spread_vec[ix]}
        source = ColumnDataSource(data=dd)
        lines.append(plot.line('t', x, source=source,
                               line_color=Spectral11[l % len(Spectral11)]))
        l += 1

    if annotations:
        for col, i_set in annotations.items():
            i_set = IntervalSet(x_min_df, x_min_df + max_time, time_units=units)
            i_set = i_set.as_units(units)

            for l in i_set.iterrows():
                box = BoxAnnotation(left=l[1]['start'], right=l[1]['end'], fill_alpha=0.1, fill_color=col)
                plot.add_layout(box)

    # noinspection PyShadowingNames
    def update_in(x_min=x_min_df, x_interval=default_interval):
        nonlocal df1

        if df1.index[0] > x_min or df1.index[-1] < x_min + x_interval:
            if isinstance(df, pd.DataFrame):
                df1 = df[((x_min - max_time/2) < df.index) & (df.index < (x_min + max_time/2))]
            else:
                df1 = load_continuous_tsd(df, t_min=tu.format_timestamps(x_min-max_time/2, units=units),
                                          t_max=tu.format_timestamps(x_min + max_time/2, units=units),
                                          downsample=downsample).as_units(units)
            t = df1.index
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                for ix, x in enumerate(df1.columns):
                    lines[ix].data_source.data['t'] = t
                    lines[ix].data_source.data[x] = df1[x] + spread_vec[ix]
            push_notebook()
        plot.x_range.start = x_min
        plot.x_range.end = x_min + x_interval
        push_notebook()

    show(plot, notebook_handle=True)
    interact(update_in, x_min=(x_min_df, x_max_df, 0.5), x_interval=(0.2, 5, 0.2))
