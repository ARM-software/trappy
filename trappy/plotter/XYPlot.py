import matplotlib.pyplot as plt
import pandas as pd
from trappy.plotter import AttrConf
from trappy.plotter.AbstractDataPlotter import AbstractDataPlotter
from trappy.plotter.ColorMap import ColorMap


class XYPlot(AbstractDataPlotter):
    def __init__(self, xinput, yinput=None, legend=None, xerr=None, yerr=None, ax=None, **kwargs):
        self.xdata = {}
        self.ydata = {}
        self._attr = {}
        self.set_defaults()
        self._ax = ax

        for key in kwargs:
            if key in AttrConf.ARGS_TO_FORWARD:
                self._attr["args_to_forward"][key] = kwargs[key]
            else:
                self._attr[key] = kwargs[key]

        # Data frame input
        if isinstance(xinput, pd.DataFrame):
            self.xdata, self.ydata, self.legend, self.xerr, self.yerr = self._fromDataFrame(xinput, legend)

        # Dict input
        elif isinstance(xinput, dict):
            if not _all_same_type(dict, xinput, yinput, xerr, yerr):
                raise TypeError("All inputs must be of the same type")
            self.xdata = xinput
            self.ydata = yinput
            self.xerr = xerr
            self.yerr = yerr
            self.legend = xinput.keys()

        # List input
        elif isinstance(xinput, list):
            if not _all_same_type(list, xinput, yinput, xerr, yerr):
                raise TypeError("All inputs must be of the same type")

            self.xdata, self.legend = self._fromList(xinput, legend)
            self.ydata, _ = self._fromList(yinput, legend)
            if yerr:
                self.yerr, _ = self._fromList(yerr, legend)
            if xerr:
                self.xerr, _ = self._fromList(xerr, legend)

        super(XYPlot, self).__init__()

    def _fromList(self, input, legend):
        output = {}

        # A list of lists - i.e multiple lines
        if isinstance(input[0], list):
            if legend:
                if len(legend) != len(input):
                    raise ValueError("You must specific the same number of line names as you do lines")
            else:
                legend = xrange(len(input))
            for i, name in enumerate(legend):
                output[name] = input[i]

        # Single list of values
        elif isinstance(input[0], int) or isinstance(input[0], float):
            legend = legend or ["0"]
            output[legend[0]] = input
        else:
            TypeError("Input must be a list of numeric values, or a list of such lists")

        return output, legend

    def _fromDataFrame(self, df, legend):
        xdata = {}
        ydata = {}
        xerr = {}
        yerr = {}

        if len(df.columns) < 2:
            raise ValueError("DataFrame must contain at least 2 columns")
        elif len(df.columns) == 2:
            legend = legend or ["0"]
            xdata[legend[0]] = df[df.columns[0]]
            ydata[legend[0]] = df[df.columns[1]]
        else:
            x_col = self._attr["x_col"]
            y_col = self._attr["y_col"]
            legend_col = self._attr["legend_col"]
            xerr_col = self._attr["xerr_col"]
            yerr_col = self._attr["yerr_col"]

            if legend_col:
                legend = df[legend_col].unique()
                for name in legend:
                    xdata[name] = df[df[legend_col] == name][x_col]
                    ydata[name] = df[df[legend_col] == name][y_col]
                    if xerr_col:
                        xerr[name] = df[df[legend_col] == name][xerr_col]
                    if yerr_col:
                        yerr[name] = df[df[legend_col] == name][yerr_col]
            else:
                legend = legend or ["0"]
                xdata[legend[0]] = df[x_col]
                ydata[legend[0]] = df[y_col]

        return xdata, ydata, legend, xerr, yerr

    def set_defaults(self):
        self._attr['title'] = ""
        self._attr['xlabel'] = ""
        self._attr['ylabel'] = ""
        self._attr["args_to_forward"] = {}
        self._attr['loc'] = 0
        self._attr['fig_size'] = (5, 5)
        self._attr["legend_col"] = ""
        self._attr["xerr_col"] = ""
        self._attr["yerr_col"] = ""
        self.yerr = None
        self.xerr = None
        self._fig = None

    def view(self, test=False):
        if not self._ax:
            self._fig, self._ax = plt.subplots(1, 1)

        cmap = ColorMap(len(self.legend))

        # Plot lines
        for i, name in enumerate(self.legend):
            self._ax.plot(self.xdata[name],
                          self.ydata[name],
                          'o-',
                          label=name,
                          color=cmap.cmap(i),
                          **self._attr["args_to_forward"])
            if self.yerr or self.xerr:
                self._ax.errorbar(self.xdata[name],
                                  self.ydata[name],
                                  yerr=self.yerr[name] if self.yerr else None,
                                  xerr=self.xerr[name] if self.xerr else None,
                                  fmt='o',
                                  color=cmap.cmap(i),
                                  **self._attr["args_to_forward"])

        # Setup graph style
        self._ax.set_xlabel(self._attr['xlabel'])
        self._ax.set_ylabel(self._attr['ylabel'])
        self._ax.grid()
        self._ax.legend(loc=self._attr['loc'])
        if self._attr['title']:
            self._ax.set_title(self._attr['title'])

        xmax = _find_max_2D(self.xdata)
        xmin = _find_min_2D(self.xdata)
        ymax = _find_max_2D(self.ydata)
        ymin = _find_min_2D(self.ydata)

        self._ax.set_xlim(right=xmax*1.05, left=xmin-0.05*xmax)
        self._ax.set_ylim(top=ymax*1.05, bottom=ymin-0.05*ymax)
        if self._fig:
            self._fig.set_size_inches(self._attr['fig_size'])

    def savefig(self, *args, **kwargs):
        """Save the plot as a PNG fill. This calls into
        :mod:`matplotlib.figure.savefig`
        """
        if not self._ax:
            self.view()
        if self._fig:
            self.savefig(*args, **kwargs)
        else:
            raise Exception("Cannot save figure when using external axes, please save from the figure they belong to.")


def _find_max_2D(data):
    return max(max(x) for x in data.itervalues() if list(x))


def _find_min_2D(data):
    return min(min(x) for x in data.itervalues() if list(x))


def _all_same_type(type, *args):
    for obj in args:
        if obj and not isinstance(obj, type):
            return False
    return True
