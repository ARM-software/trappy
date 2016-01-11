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

    def _check_add_scatter(self):
        """Check if a scatter plot is needed
        and augment the forwarded args accordingly"""

        if self._attr["scatter"]:
            self._attr["args_to_forward"]["linestyle"] = ""
            self._attr["args_to_forward"]["marker"] = "o"
            if "point_size" in self._attr:
                self._attr["args_to_forward"]["markersize"] = \
                    self._attr["point_size"]

    def plot(self, series_index, axis, data_index, data_values, **kwargs):
        """Internal Method called to draw a series on an axis"""
        line_2d_list = axis.plot(
            data_index,
            data_values,
            color=self._cmap.cmap(series_index),
            **kwargs["args_to_forward"])

        return line_2d_list
