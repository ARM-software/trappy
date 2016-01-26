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
"""
This class sublclasses :mod:`trappy.plotter.StaticPlot.StaticPlot` to
implement a bar plot.

"""
import numpy as np
from trappy.plotter.StaticPlot import StaticPlot

class BarPlot(StaticPlot):
    """A matplotlib static plotter which produces line plots"""

    def __init__(self, traces, templates=None, **kwargs):
        # Default keys, each can be overridden in kwargs

        super(BarPlot, self).__init__(
            traces=traces,
            templates=templates,
            **kwargs)

    def set_defaults(self):
        """Sets the default attrs"""
        super(BarPlot, self).set_defaults()
        self._attr["spacing"] = 0.2
        self._attr["stacked"] = False

    def plot_axis(self, axis, series_list, permute, concat, **kwargs):
        """Internal Method called to plot data (series_list) on a given axis"""
        stacked = self._attr["stacked"]
        #Figure out how many bars per group
        bars_in_group = 1 if stacked else len(series_list)

        #Get the width of a group
        group_width = 1.0 - self._attr["spacing"]
        bar_width = group_width / bars_in_group

        #Keep a list of the tops of bars to plot stacks
        #Start with a list of 0s to put the first bars at the bottom
        value_list = [c.result[p].values for (c, p) in series_list]
        end_of_previous = [0] * max(len(x) for x in value_list)

        for i, (constraint, pivot) in enumerate(series_list):
            result = constraint.result
            bar_anchor = np.arange(len(result[pivot].values))
            if not stacked:
                bar_anchor = bar_anchor + i * bar_width

            line_2d_list = axis.bar(
                bar_anchor,
                result[pivot].values,
                bottom=end_of_previous,
                width=bar_width,
                color=self._cmap.cmap(i),
                **kwargs["args_to_forward"]
            )

            if stacked:
                end_of_previous = [(x or 0) + (y or 0) for (x, y) in map(None, end_of_previous, result[pivot].values)]

            axis.set_title(self.make_title(constraint, pivot, permute, concat))

            self.add_to_legend(i, line_2d_list[0], constraint, pivot, concat)
