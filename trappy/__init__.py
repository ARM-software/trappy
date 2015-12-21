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


import pkg_resources
from trappy.compare_runs import summary_plots, compare_runs
from trappy.ftrace import FTrace
try:
    from trappy.plotter.LinePlot import LinePlot
except ImportError as exc:
    class LinePlot(object):
        def __init__(self, *args, **kwargs):
            raise exc
try:
    from trappy.plotter.ILinePlot import ILinePlot
    from trappy.plotter.EventPlot import EventPlot
except ImportError:
    pass
from trappy.dynamic import register_dynamic, register_class

# For backwards compatibility.  Remove by 2016-12-31
class Run(FTrace):
    """This class is deprecated.  Use trappy.FTrace instead"""
    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn("The Run object is deprecated.  Use trappy.FTrace instead")
        super(Run, self).__init__(*args, **kwargs)

# Load all the modules to make sure all classes are registered with FTrace
import os
for fname in os.listdir(os.path.dirname(__file__)):
    import_name, extension = os.path.splitext(fname)
    if (extension == ".py") and (fname != "__init__.py") and \
       (fname != "plot_utils.py"):
        __import__("trappy.{}".format(import_name))

del fname, import_name, extension

try:
    __version__ = pkg_resources.get_distribution("trappy").version
except pkg_resources.DistributionNotFound:
    __version__ = "local"
