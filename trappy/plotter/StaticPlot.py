#    Copyright 2016-2016 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Base matplotlib plotter module"""
from abc import abstractmethod, ABCMeta
import matplotlib.pyplot as plt
from trappy.plotter import AttrConf
from trappy.plotter.Constraint import ConstraintManager
from trappy.plotter.PlotLayout import PlotLayout
from trappy.plotter.AbstractDataPlotter import AbstractDataPlotter
from trappy.plotter.ColorMap import ColorMap

"""
This class uses :mod:`trappy.plotter.Constraint.Constraint` to
represent different permutations of input parameters. These
constraints are generated by creating an instance of
:mod:`trappy.plotter.Constraint.ConstraintManager`.

:param trace: The input data
:type trace: :mod:`trappy.trace.FTrace` or :mod:`pandas.DataFrame`, list or single

:param column: specifies the name of the column to
       be plotted.
:type column: (str, list(str))

:param templates: TRAPpy events

    .. note::

            This is not required if a :mod:`pandas.DataFrame` is
            used

:type templates: :mod:`trappy.base.Base`

:param filters: Filter the column to be plotted as per the
    specified criteria. For Example:
    ::

        filters =
                {
                    "pid": [ 3338 ],
                    "cpu": [0, 2, 4],
                }
:type filters: dict

:param per_line: Used to control the number of graphs
    in each graph subplot row
:type per_line: int

:param concat: Draw all the pivots on a single graph
:type concat: bool

:param fill: Fill the area under the plots
:type fill: bool

:param permute: Draw one plot for each of the traces specified
:type permute: bool

:param drawstyle: This argument is forwarded to the matplotlib
    corresponding :func:`matplotlib.pyplot.plot` call

    drawing style.

    .. note::

        step plots are not currently supported for filled
        graphs

:param xlim: A tuple representing the upper and lower xlimits
:type xlim: tuple

:param ylim: A tuple representing the upper and lower ylimits
:type ylim: tuple

:param title: A title describing all the generated plots
:type title: str

:param style: Created pre-styled graphs loaded from
    :mod:`trappy.plotter.AttrConf.MPL_STYLE`
:type style: bool

:param signals: A string of the type event_name:column
    to indicate the value that needs to be plotted

    .. note::

        - Only one of `signals` or both `templates` and
          `columns` should be specified
        - Signals format won't work for :mod:`pandas.DataFrame`
          input

:type signals: str

"""

class StaticPlot(AbstractDataPlotter):
    """Base class for matplotlib plotters"""

    __metaclass__ = ABCMeta

    def __init__(self, traces, templates=None, **kwargs):
        self._fig = None
        self._layout = None
        super(StaticPlot, self).__init__(traces=traces,
                                         templates=templates)

        self.set_defaults()

        for key in kwargs:
            if key in AttrConf.ARGS_TO_FORWARD:
                self._attr["args_to_forward"][key] = kwargs[key]
            else:
                self._attr[key] = kwargs[key]

        if "signals" in self._attr:
            self._describe_signals()

        self._check_data()

        if "column" not in self._attr:
            raise RuntimeError("Value Column not specified")

        zip_constraints = not self._attr["permute"]
        self.c_mgr = ConstraintManager(traces, self._attr["column"],
                                       self.templates, self._attr["pivot"],
                                       self._attr["filters"], zip_constraints)

    def savefig(self, *args, **kwargs):
        """Save the plot as a PNG fill. This calls into
        :mod:`matplotlib.figure.savefig`
        """

        if self._fig is None:
            self.view()
        self._fig.savefig(*args, **kwargs)

    @abstractmethod
    def set_defaults(self):
        """Sets the default attrs"""
        self._attr["width"] = AttrConf.WIDTH
        self._attr["length"] = AttrConf.LENGTH
        self._attr["per_line"] = AttrConf.PER_LINE
        self._attr["concat"] = AttrConf.CONCAT
        self._attr["fill"] = AttrConf.FILL
        self._attr["filters"] = {}
        self._attr["style"] = True
        self._attr["permute"] = False
        self._attr["pivot"] = AttrConf.PIVOT
        self._attr["xlim"] = AttrConf.XLIM
        self._attr["ylim"] = AttrConf.XLIM
        self._attr["title"] = AttrConf.TITLE
        self._attr["args_to_forward"] = {}
        self._attr["map_label"] = {}

    def view(self):
        """Displays the graph"""

        if self._attr["concat"]:
            if self._attr["style"]:
                with plt.rc_context(AttrConf.MPL_STYLE):
                    self._resolve_concat()
            else:
                self._resolve_concat()
        else:
            if self._attr["style"]:
                with plt.rc_context(AttrConf.MPL_STYLE):
                    self._resolve(self._attr["permute"])
            else:
                self._resolve(self._attr["permute"])

    def make_title(self, constraint, pivot, permute):
        title = ""
        if permute:
            title += constraint.get_data_name() + ":"

        if pivot == AttrConf.PIVOT_VAL:
            if type(self._attr["column"]) is list:
                title += ", ".join(self._attr["column"])
            else:
                title += self._attr["column"]
        else:
            title += "{0}: {1}".format(self._attr["pivot"],
                                       self._attr["map_label"].get(pivot, pivot))
        return title

    def _resolve(self, permute=False):
        """Determine what data to plot"""
        pivot_vals, len_pivots = self.c_mgr.generate_pivots(permute)
        pivot_vals = list(pivot_vals)

        # Create a 2D Layout
        self._layout = PlotLayout(
            self._attr["per_line"],
            len_pivots,
            width=self._attr["width"],
            length=self._attr["length"],
            title=self._attr['title'])

        self._fig = self._layout.get_fig()
        legend_str = []

        #Set up the legend and colormap
        #Determine what constraint to plot and the corresponding pivot value
        if permute:
            legend = [None] * self.c_mgr._max_len # pylint: disable=W0212
            self._cmap = ColorMap(self.c_mgr._max_len) # pylint: disable=W0212
            pivots = [y for _, y in pivot_vals]
            to_plot = [(c, p) for c in self.c_mgr for p in sorted(set(pivots))]
        else:
            legend = [None] * len(self.c_mgr)
            self._cmap = ColorMap(len(self.c_mgr))
            pivots = pivot_vals
            to_plot = [(c, p) for c in self.c_mgr for p in pivots if p in c.result]

        #Counts up the number of series plotted on each axis (for coloring etc)
        axis_series = dict((self._layout.get_axis(i), 0) for i in range(len(to_plot)))

        #Plot each series of data on the appropriate axis
        for i, (constraint, pivot) in enumerate(to_plot):
            result = constraint.result
            axis = self._layout.get_axis(i)
            series_index = axis_series[axis]
            axis_series[axis] += 1
            line_2d_list = self.plot(
                series_index,
                axis,
                result[pivot].index,
                result[pivot].values,
                args_to_forward=self._attr["args_to_forward"])

            legend[series_index] = line_2d_list[0]
            legend_str.append(str(constraint))

            axis.set_title(self.make_title(constraint, pivot, permute))

        for l_idx, legend_line in enumerate(legend):
            if not legend_line:
                del legend[l_idx]
                del legend_str[l_idx]
        self._fig.legend(legend, legend_str)
        self._layout.finish(len_pivots)

    def _resolve_concat(self):
        """Plot all lines on a single figure"""

        pivot_vals, len_pivots = self.c_mgr.generate_pivots()
        self._cmap = ColorMap(len_pivots)

        self._layout = PlotLayout(self._attr["per_line"], len(self.c_mgr),
                                  width=self._attr["width"],
                                  length=self._attr["length"],
                                  title=self._attr['title'])

        self._fig = self._layout.get_fig()
        legend = [None] * len_pivots
        legend_str = [""] * len_pivots
        plot_index = 0

        for constraint in self.c_mgr:
            result = constraint.result
            title = str(constraint)
            result = constraint.result
            pivot_index = 0
            for pivot in pivot_vals:

                if pivot in result:
                    axis = self._layout.get_axis(plot_index)
                    line_2d_list = self.plot(
                        pivot_index,
                        axis,
                        result[pivot].index,
                        result[pivot].values,
                        args_to_forward=self._attr["args_to_forward"])

                    if self._attr["xlim"] != None:
                        axis.set_xlim(self._attr["xlim"])
                    if self._attr["ylim"] != None:
                        axis.set_ylim(self._attr["ylim"])
                    legend[pivot_index] = line_2d_list[0]

                    if self._attr["fill"]:
                        drawstyle = line_2d_list[0].get_drawstyle()
                        if drawstyle.startswith("steps"):
                            # This has been fixed in upstream matplotlib
                            raise UserWarning("matplotlib does not support fill for step plots")

                        xdat, ydat = line_2d_list[0].get_data(orig=False)
                        axis.fill_between(
                            xdat,
                            axis.get_ylim()[0],
                            ydat,
                            facecolor=self._cmap.cmap(pivot_index),
                            alpha=AttrConf.ALPHA)

                    if pivot == AttrConf.PIVOT_VAL:
                        legend_str[pivot_index] = self._attr["column"]
                    else:
                        legend_str[pivot_index] = "{0}: {1}".format(self._attr["pivot"],
                                                                    self._attr["map_label"].get(pivot, pivot))
                else:
                    axis = self._layout.get_axis(plot_index)
                    axis.plot(
                        [],
                        [],
                        color=self._cmap.cmap(pivot_index),
                        **self._attr["args_to_forward"])
                pivot_index += 1
            plot_index += 1

        self._fig.legend(legend, legend_str)
        plot_index = 0
        for constraint in self.c_mgr:
            self._layout.get_axis(plot_index).set_title(str(constraint))
            plot_index += 1
        self._layout.finish(len(self.c_mgr))

    @abstractmethod
    def plot(self, axis, series_index, data_index, data_values, **kwargs):
        """Internal Method called to draw a series on an axis"""
        raise NotImplementedError("Method Not Implemented")
