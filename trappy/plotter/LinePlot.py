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
"""This module contains the class for plotting and
customizing Line Plots with a pandas dataframe input
"""

from trappy.plotter import AttrConf
from trappy.plotter.StaticPlot import StaticPlot

class LinePlot(StaticPlot):
    """A matplotlib static plotter which produces line plots"""

    def __init__(self, traces, templates=None, **kwargs):
        # Default keys, each can be overridden in kwargs

        super(LinePlot, self).__init__(
            traces=traces,
            templates=templates,
            **kwargs)

        self._check_add_scatter()

    def set_defaults(self):
        """Sets the default attrs"""
        super(LinePlot, self).set_defaults()
        self._attr["scatter"] = AttrConf.PLOT_SCATTER
        self._attr["fill"] = AttrConf.FILL

    def _check_add_scatter(self):
        """Check if a scatter plot is needed
        and augment the forwarded args accordingly"""

        if self._attr["scatter"]:
            self._attr["args_to_forward"]["linestyle"] = ""
            self._attr["args_to_forward"]["marker"] = "o"
            if "point_size" in self._attr:
                self._attr["args_to_forward"]["markersize"] = \
                    self._attr["point_size"]

    def fill_line(self, axis, line_2d, cmap_index):
        drawstyle = line_2d.get_drawstyle()
        if drawstyle.startswith("steps"):
            # This has been fixed in upstream matplotlib
            raise UserWarning("matplotlib does not support fill for step plots")

        xdat, ydat = line_2d.get_data(orig=False)
        axis.fill_between(
            xdat,
            axis.get_ylim()[0],
            ydat,
            facecolor=self._cmap.cmap(cmap_index),
            alpha=AttrConf.ALPHA)

    def plot_axis(self, axis, series_list, permute, concat, **kwargs):
        """Internal Method called to draw a list of series on a given axis"""
        for i, (constraint, pivot) in enumerate(series_list):
            result = constraint.result
            line_2d_list = axis.plot(
                result[pivot].index,
                result[pivot].values,
                color=self._cmap.cmap(i),
                **kwargs["args_to_forward"]
            )

            if self._attr["fill"]:
                self.fill_line(axis, line_2d_list[0], i)

            axis.set_title(self.make_title(constraint, pivot, permute, concat))

            self.add_to_legend(i, line_2d_list[0], constraint, pivot, concat)
