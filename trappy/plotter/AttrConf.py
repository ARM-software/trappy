#    Copyright 2015-2015 ARM Limited
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

"""These are the default plotting Attributes"""
WIDTH = 7
LENGTH = 7
PER_LINE = 2
CONCAT = False
PIVOT = "__TRAPPY_PIVOT_DEFAULT"
PIVOT_VAL = "__TRAPPY_DEFAULT_PIVOT_VAL"
DUPLICATE_VALUE_MAX_DELTA = 0.000001
XLIM = None
YLIM = None
FILL = False
ALPHA = 0.75

MPL_STYLE = {
    'axes.axisbelow': True,
    'axes.color_cycle': ['#348ABD',
                         '#7A68A6',
                         '#A60628',
                         '#467821',
                         '#CF4457',
                         '#188487',
                         '#E24A33'],
    'axes.edgecolor': '#bcbcbc',
    'axes.facecolor': '#eeeeee',
    'axes.grid': True,
    'axes.labelcolor': '#555555',
    'axes.labelsize': 'large',
    'axes.linewidth': 1.0,
    'axes.titlesize': 'x-large',
    'figure.edgecolor': 'white',
    'figure.facecolor': 'white',
    'figure.figsize': (6.0, 4.0),
    'figure.subplot.hspace': 0.5,
    'font.size': 10,
    'interactive': True,
    'keymap.all_axes': ['a'],
    'keymap.back': ['left', 'c', 'backspace'],
    'keymap.forward': ['right', 'v'],
    'keymap.fullscreen': ['f'],
    'keymap.grid': ['g'],
    'keymap.home': ['h', 'r', 'home'],
    'keymap.pan': ['p'],
    'keymap.save': ['s'],
    'keymap.xscale': ['L', 'k'],
    'keymap.yscale': ['l'],
    'keymap.zoom': ['o'],
    'legend.fancybox': True,
    'lines.antialiased': True,
    'lines.linewidth': 1.0,
    'patch.antialiased': True,
    'patch.edgecolor': '#EEEEEE',
    'patch.facecolor': '#348ABD',
    'patch.linewidth': 0.5,
    'toolbar': 'toolbar2',
    'xtick.color': '#555555',
    'xtick.direction': 'in',
    'xtick.major.pad': 6.0,
    'xtick.major.size': 0.0,
    'xtick.minor.pad': 6.0,
    'xtick.minor.size': 0.0,
    'ytick.color': '#555555',
    'ytick.direction': 'in',
    'ytick.major.pad': 6.0,
    'ytick.major.size': 0.0,
    'ytick.minor.pad': 6.0,
    'ytick.minor.size': 0.0
}
ARGS_TO_FORWARD = [
    "marker",
    "markersize",
    "markevery",
    "linestyle",
    "linewidth",
    "drawstyle"]

HTML_WIDTH =  900
HTML_HEIGHT = 400
# Sync Graph zoom by default in
# ILinePlot graph groups
DEFAULT_SYNC_ZOOM = False
EVENT_PLOT_STRIDE = False

