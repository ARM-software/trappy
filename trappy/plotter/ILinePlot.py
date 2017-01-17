#    Copyright 2015-2017 ARM Limited
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

"""This module contains the class for plotting and customizing
Line/Linear Plots with :mod:`trappy.trace.BareTrace` or derived
classes.  This plot only works when run from an IPython notebook

"""

from collections import OrderedDict
import matplotlib.pyplot as plt
from trappy.plotter import AttrConf
from trappy.plotter import Utils
from trappy.plotter.Constraint import ConstraintManager
from trappy.plotter.ILinePlotGen import ILinePlotGen
from trappy.plotter.AbstractDataPlotter import AbstractDataPlotter
from trappy.plotter.ColorMap import ColorMap
from trappy.plotter import IPythonConf
from trappy.utils import handle_duplicate_index
import pandas as pd

if not IPythonConf.check_ipython():
    raise ImportError("Ipython Environment not Found")

class ILinePlot(AbstractDataPlotter):
    """
    Interactive Line Plotter

    Creates line plots for use in IPython notebooks that can be zoomed and
    scrolled interactively

    This class uses :mod:`trappy.plotter.Constraint.Constraint` to
    represent different permutations of input parameters. These
    constraints are generated by creating an instance of
    :mod:`trappy.plotter.Constraint.ConstraintManager`.

    :param traces: The input data
    :type traces: a list of :mod:`trappy.trace.FTrace`,
        :mod:`trappy.trace.SysTrace`, :mod:`trappy.trace.BareTrace`
        or :mod:`pandas.DataFrame` or a single instance of them.

    :param column: When plotting DataFrames, specifies the name of the column to
           be plotted. If plotting a single DataFrame, may be a list of columns
           to use. If plotting multiple DataFrames, must be a single column name
           or a list of respective column names such that ``columns[i]`` is
           plotted from ``traces[i]`` for each ``i``.
    :type column: (str, list(str))

    :param signals: When plotting traces (i.e. using ``Ftrace``, ``SysTrace`` et
        al. for ``traces``), a string of the type event_name:column to indicate
        the value that needs to be plotted.  You can add an additional parameter
        to specify the color of the line in rgb: "event_name:column:color".  The
        color is specified as a comma separated list of rgb values, from 0 to
        255 or from 0x0 to 0xff.  E.g. 0xff,0x0,0x0 is red and 100,40,32 is
        brown.

        .. note::

            - Only one of `signals` or both `templates` and
              `columns` should be specified
            - Signals format won't work for :mod:`pandas.DataFrame`
              input

    :type signals: str

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

    :param permute: Draw one plot for each of the traces specified
    :type permute: bool

    :param fill: Fill the area under the plots
    :type fill: bool

    :param fill_alpha: Opacity of filled area under the plots.
        Implies fill=True.
    :type fill_alpha: float

    :param xlim: A tuple representing the upper and lower xlimits
    :type xlim: tuple

    :param ylim: A tuple representing the upper and lower ylimits
    :type ylim: tuple

    :param drawstyle: Set the drawstyle to a matplotlib compatible
        drawing style.

        .. note::

            Only "steps-post" is supported as a valid value for
            the drawstyle. This creates a step plot.

    :type drawstyle: str

    :param sync_zoom: Synchronize the zoom of a group of plots.
        Zooming in one plot of a group (see below) will zoom in every
        plot of that group.  Defaults to False.
    :type sync_zoom: boolean

    :param group: Name given to the plots created by this ILinePlot
        instance.  This name is only used for synchronized zoom.  If
        you zoom on any plot in a group all plots will zoom at the
        same time.
    :type group: string
    """

    def __init__(self, traces, templates=None, **kwargs):
        # Default keys, each can be overridden in kwargs
        self._layout = None
        super(ILinePlot, self).__init__(traces=traces,
                                        templates=templates)

        self.set_defaults()

        for key in kwargs:
            self._attr[key] = kwargs[key]

        if "signals" in self._attr:
            self._describe_signals()

        self._check_data()

        if "column" not in self._attr:
            raise RuntimeError("Value Column not specified")

        if self._attr["drawstyle"] and self._attr["drawstyle"].startswith("steps"):
            self._attr["step_plot"] = True

        zip_constraints = not self._attr["permute"]

        window = self._attr["xlim"] if "xlim" in self._attr else None

        self.c_mgr = ConstraintManager(traces, self._attr["column"], self.templates,
                                       self._attr["pivot"],
                                       self._attr["filters"],
                                       window=window,
                                       zip_constraints=zip_constraints)


    def savefig(self, *args, **kwargs):
        raise NotImplementedError("Not Available for ILinePlot")

    def view(self, max_datapoints=75000, test=False):
        """Displays the graph

        :param max_datapoints: Maximum number of datapoints to plot.
        Dygraph can make the browser unresponsive if it tries to plot
        too many datapoints.  Chrome 50 chokes at around 75000 on an
        i7-4770 @ 3.4GHz, Firefox 47 can handle up to 200000 before
        becoming too slow in the same machine.  You can increase this
        number if you know what you're doing and are happy to wait for
        the plot to render.  :type max_datapoints: int

        :param test: For testing purposes.  Only set to true if run
        from the testsuite.
        :type test: boolean
        """

        # Defer installation of IPython components
        # to the .view call to avoid any errors at
        # when importing the module. This facilitates
        # the importing of the module from outside
        # an IPython notebook
        if not test:
            IPythonConf.iplot_install("ILinePlot")

        self._attr["max_datapoints"] = max_datapoints

        if self._attr["concat"]:
            self._plot_concat()
        else:
            self._plot(self._attr["permute"], test)

    def set_defaults(self):
        """Sets the default attrs"""
        self._attr["per_line"] = AttrConf.PER_LINE
        self._attr["concat"] = AttrConf.CONCAT
        self._attr["filters"] = {}
        self._attr["pivot"] = AttrConf.PIVOT
        self._attr["permute"] = False
        self._attr["drawstyle"] = None
        self._attr["step_plot"] = False
        self._attr["fill"] = AttrConf.FILL
        self._attr["scatter"] = AttrConf.PLOT_SCATTER
        self._attr["point_size"] = AttrConf.POINT_SIZE
        self._attr["map_label"] = {}
        self._attr["title"] = AttrConf.TITLE

    def _plot(self, permute, test):
        """Internal Method called to draw the plot"""
        pivot_vals, len_pivots = self.c_mgr.generate_pivots(permute)

        self._layout = ILinePlotGen(len_pivots, **self._attr)
        plot_index = 0
        for p_val in pivot_vals:
            data_dict = OrderedDict()
            for constraint in self.c_mgr:
                if permute:
                    trace_idx, pivot = p_val
                    if constraint.trace_index != trace_idx:
                        continue
                    legend = constraint._template.name + ":" + constraint.column
                else:
                    pivot = p_val
                    legend = str(constraint)

                result = constraint.result
                if pivot in result:
                    data_dict[legend] = result[pivot]

            if permute:
                title = self.traces[plot_index].name
            elif pivot != AttrConf.PIVOT_VAL:
                title = "{0}: {1}".format(self._attr["pivot"], self._attr["map_label"].get(pivot, pivot))
            else:
                title = ""

            if len(data_dict) > 1:
                data_frame = self._fix_indexes(data_dict)
            else:
                data_frame = pd.DataFrame(data_dict)

            self._layout.add_plot(plot_index, data_frame, title, test=test)
            plot_index += 1

        self._layout.finish()

    def _plot_concat(self):
        """Plot all lines on a single figure"""

        pivot_vals, _ = self.c_mgr.generate_pivots()
        plot_index = 0

        self._layout = ILinePlotGen(len(self.c_mgr), **self._attr)

        for constraint in self.c_mgr:
            result = constraint.result
            title = str(constraint)
            data_dict = OrderedDict()

            for pivot in pivot_vals:
                if pivot in result:
                    if pivot == AttrConf.PIVOT_VAL:
                        key = ",".join(self._attr["column"])
                    else:
                        key = "{0}: {1}".format(self._attr["pivot"], self._attr["map_label"].get(pivot, pivot))

                    data_dict[key] = result[pivot]

            if len(data_dict) > 1:
                data_frame = self._fix_indexes(data_dict)
            else:
                data_frame = pd.DataFrame(data_dict)

            self._layout.add_plot(plot_index, data_frame, title)
            plot_index += 1

        self._layout.finish()

    def _fix_indexes(self, data_dict):
        """
        In case of multiple traces with different indexes (i.e. x-axis values),
        create new ones with same indexes
        """
        # 1) Check if we are processing multiple traces
        if len(data_dict) <= 1:
            raise ValueError("Cannot fix indexes for single trace. "\
                             "Expecting multiple traces!")

        # 2) Merge the data frames to obtain common indexes
        df_columns = list(data_dict.keys())
        dedup_data = [handle_duplicate_index(s) for s in data_dict.values()]
        ret = pd.Series(dedup_data, index=df_columns)
        merged_df = pd.concat(ret.get_values(), axis=1)
        merged_df.columns = df_columns
        # 3) Fill NaN values depending on drawstyle
        if self._attr["drawstyle"] == "steps-post":
            merged_df = merged_df.ffill()
        elif self._attr["drawstyle"] == "steps-pre":
            merged_df = merged_df.bfill()
        elif self._attr["drawstyle"] == "steps-mid":
            merged_df = merged_df.ffill()
        else:
            # default
            merged_df = merged_df.interpolate()

        return merged_df
