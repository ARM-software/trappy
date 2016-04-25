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
"""Preprocessor to remove Marked Lines from IPython Output Cells"""


from nbconvert.preprocessors import Preprocessor

REMOVE_START = '/* TRAPPY_PUBLISH_REMOVE_START */'
REMOVE_STOP = '/* TRAPPY_PUBLISH_REMOVE_STOP */'
REMOVE_LINE = '/* TRAPPY_PUBLISH_REMOVE_LINE */'


def filter_output(output):
    """Function to remove marked lines"""

    lines = output.split('\n')

    final_lines = []
    multi_line_remove = False
    for line in lines:
        if REMOVE_START in line:
            multi_line_remove = True
            continue
        if REMOVE_STOP in line:
            multi_line_remove = False
            continue
        if multi_line_remove or REMOVE_LINE in line:
            continue
        final_lines.append(line)

    return '\n'.join(final_lines)


class TrappyPlotterPreprocessor(Preprocessor):
    """Preprocessor to remove Marked Lines from IPython Output Cells"""

    def preprocess_cell(self, cell, resources, cell_index):
        """Check if cell has text/html output and filter it"""

        if cell.cell_type == 'code' and hasattr(cell, "outputs"):
            for output in cell.outputs:
                if output.output_type == "display_data" and hasattr(
                        output.data, "text/html"):
                    output.data["text/html"] = filter_output(
                        output.data["text/html"])
        return cell, resources
