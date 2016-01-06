#    Copyright 2015-2016 ARM Limited
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

"""Defines a generic indexable ColorMap Class"""
import matplotlib.colors as clrs
import matplotlib.cm as cmx
from matplotlib.colors import ListedColormap, Normalize


class ColorMap(object):

    """The Color Map Class to return a gradient method

    :param num_colors: Number or colors for which a gradient
        is needed
    :type num_colors: int
    """

    def __init__(self, num_colors):
        self.color_norm = clrs.Normalize(vmin=0, vmax=num_colors)
        self.scalar_map = cmx.ScalarMappable(norm=self.color_norm, cmap='hsv')
        self.num_colors = num_colors

    def cmap(self, index):
        """
        :param index: Index for the gradient array
        :type index: int

        :return: The color at specified index
        """
        return self.scalar_map.to_rgba(index)

    def cmap_inv(self, index):
        """
        :param index: Index for the gradient array
        :type index: int

        :return: The color at :math:`N_{colors} - i`
        """
        return self.cmap(self.num_colors - index)

    def rgb_cmap(self, rgb_list):
        if any([c > 1 for rgb in rgb_list for c in rgb]):
            rgb_list = [[x / 255.0 for x in rgb[:3]] for rgb in rgb_list]
        self.color_norm = Normalize(vmin=0, vmax=len(rgb_list))
        rgb_map = ListedColormap(rgb_list, name='defualt_color_map', N=None)
        self.scalar_map = cmx.ScalarMappable(norm=self.color_norm, cmap=rgb_map)
        self.num_colors = len(rgb_list)
