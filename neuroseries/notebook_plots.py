# noinspection PyPackageRequirements
from ipywidgets import interact
# noinspection PyPackageRequirements
from bokeh.models import Range1d
# noinspection PyPackageRequirements
from bokeh.io import push_notebook, show
# noinspection PyPackageRequirements
from bokeh.charts import TimeSeries


def FrameViewer(df, title="EEG", ylabel='voltage (mV)', xlabel='time (s)'):

    x_min = df.index[0]
    x_max = df.index[-1]
    print(x_min, x_max)
    default_interval = 1
    ts = TimeSeries(
        df, title=title,
        legend='top_left', ylabel=ylabel,
        xlabel=xlabel, x_range=Range1d(x_min, x_min+default_interval),
        plot_height=400)

    def update_in(x_min=x_min, x_interval=default_interval):
        ts.x_range.start = x_min
        ts.x_range.end = x_min + x_interval
        push_notebook()

    show(ts, notebook_handle=True)
    interact(update_in, x_min=(x_min, x_max, 0.5), x_interval=(0.2, 5, 0.2))
