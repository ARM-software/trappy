#    Copyright 2015-2016 ARM Limited
#    Copyright 2016 Google Inc. All Rights Reserved.
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
"""HTML Exporter for TRAPPY plotter data. This allows
* Custom Preprocessing
* Custom Jinja Templates
"""

import os
import os.path

from traitlets.config import Config
from nbconvert.exporters.html import HTMLExporter
from trappy.nbexport.preprocessors import TrappyPlotterPreprocessor


class HTML(HTMLExporter):
    """HTML Exporter class for TRAPy notebooks"""

    def __init__(self, **kwargs):
        self.preprocessors.append(TrappyPlotterPreprocessor)
        super(HTML, self).__init__(**kwargs)

    @property
    def template_path(self):
        """Append to the template path"""
        return super(HTML, self).template_path + [os.path.join(
            os.path.dirname(__file__), "templates")]

    def _template_file_default(self):
        """Default template File"""
        return "trappy"
