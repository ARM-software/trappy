from __future__ import division
import matplotlib.pyplot as plt
from trappy.plotter import AttrConf
from trappy.plotter.AbstractDataPlotter import AbstractDataPlotter
from trappy.plotter.XYPlot import XYPlot


class DualPlotNorm(AbstractDataPlotter):
    '''
    :param runs: The input data in the following format:

    -----------------------------------------
    | core |   freq   | power | total DMIPS |
    -----------------------------------------
    |   A7 |  800000  |  0.54 |      123456 |
    |  A15 |  1600000 |  1.54 |      987654 |
    -----------------------------------------

    :type runs: :mod:`pandas.DataFrame`

    :param workload: The name of the workload to be shown in the subtitle
    :type workload: str

    :param device: The name of the device to be shown in the subtitle
    :type device: str
    '''

    def __init__(self, runs, *args, **kwargs):
        self._attr = {}
        self.runs = runs
        self.set_defaults()
        self._check_data()
        for key in kwargs:
            if key in AttrConf.ARGS_TO_FORWARD:
                self._attr["args_to_forward"][key] = kwargs[key]
            else:
                self._attr[key] = kwargs[key]
        super(DualPlotNorm, self).__init__()

    def set_defaults(self):
        self._attr['title'] = ""
        self._attr['xlabel'] = ""
        self._attr['xunit'] = ""
        self._attr['ylabel'] = ""
        self._attr['yunit'] = ""
        self._attr['fig_size'] = (15, 10)
        self._attr["args_to_forward"] = {}
        self._attr["x_col"] = "x"
        self._attr["y_col"] = "y"
        self._attr["legend_col"] = ""
        self._attr["group_col"] = ""
        self._attr['separate_plots'] = False

    def view(self):
        """Displays the graphs"""

        x_col = self._attr["x_col"]
        y_col = self._attr["y_col"]
        legend_col = self._attr["legend_col"]
        group_col = self._attr["group_col"]

        # Calculate the mean and 95% confidence interval
        if group_col:
            avg = self.runs.groupby([legend_col, group_col]).mean()
            sem = self.runs.groupby([legend_col, group_col]).sem()
            sem[x_col] = (sem[x_col]*1.96)
            sem[y_col] = (sem[y_col]*1.96)
            df = avg.join(sem, rsuffix="_CI")
            df = df.reset_index()
            df = df[[legend_col, x_col, y_col, x_col+"_CI", y_col+"_CI"]]
        else:
            df = self.runs

        # Draw normal graph with error bars
        if not self._attr['separate_plots']:
            self._fig, self._ax = plt.subplots(1, 2)
            self._fig = [self._fig]
        else:
            self._ax = []
            self._fig = []
            for _ in (1, 2):
                fig, ax = plt.subplots(1, 1)
                self._ax.append(ax)
                self._fig.append(fig)

        XYPlot(df, ax=self._ax[0],
               x_col=x_col, y_col=y_col, legend_col=legend_col,
               xerr_col=x_col+"_CI" if group_col else "",
               yerr_col=y_col+"_CI" if group_col else "",
               xlabel=self._attr["xlabel"] + ((" (" + self._attr["xunit"] + ")") if self._attr["xunit"] else ""),
               ylabel=self._attr["ylabel"] + ((" (" + self._attr["yunit"] + ")") if self._attr["yunit"] else ""),).view()

        # Draw normalised graph
        df[x_col] = (df[x_col]/df[x_col].max())*100
        df[y_col] = (df[y_col]/df[y_col].max())*100
        XYPlot(df, ax=self._ax[1],
               x_col=x_col, y_col=y_col, legend_col=legend_col,
               xlabel=self._attr["xlabel"] + " (Normalized)",
               ylabel=self._attr["ylabel"] + " (Normalized)",).view()

        # Figure styling
        for fig in self._fig:
            fig.suptitle(self._attr['title'])
            fig.tight_layout()
            fig.subplots_adjust(top=0.9, wspace=0.2)
            fig.set_size_inches(self._attr['fig_size'])

    def savefig(self, name, *args, **kwargs):
        """Save the plot as a PNG file. This calls into
        :mod:`matplotlib.figure.savefig`
        """

        if self._fig is None:
            self.view()
        for suffix, fig in zip(["-errorbars", "-normalised"], self._fig):
            fig.savefig("{}{}.png".format(name, suffix), *args, **kwargs)
