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

"""
This module contains the class for plotting Power vs Performance curves
"""
import pandas as pd
import os
from trappy.plotter.DualPlotNorm import DualPlotNorm


class PowerPerfPlot(DualPlotNorm):
    """
    This class draws two Power vs Performance diagrams (one with error bars,
    the other Normalized) from a WA results.csv.

    It requires the WA runs to have:
     * The daq instrument enabled to measure power
     * The csv results processor to generate results.csv
     * The csv results processor setting "use_all_classifier" set to true
     * Each job should have a "core" and a "freq" classifier to identify what
       core type this spec ran on and the frequency it ran at.

       Any jobs with the same "core" and "freq" classifiers are assumed to be
       repeats of the same job and will be used to calculate mean and 95%
       confidence intervals.

    :param workload: The name of the workload to be shown in the subtitle
    :type workload: str

    :param device: The name of the device to be shown in the subtitle
    :type device: str

    """

    def __init__(self, base_dir, workload=None, device=None, process=True, * args, **kwargs):
        if isinstance(base_dir, str):
            df = pd.read_csv(os.path.join(base_dir, "results.csv"))
        else:
            df = pd.concat([pd.read_csv(os.path.join(path, "results.csv")) for path in base_dir])
        super(PowerPerfPlot, self).__init__(df, *args, **kwargs)

        if process:
            self._process()

        if workload != "":
            self._attr["title"] += "Running " + workload
        if device != "":
            self._attr["title"] += " on " + device

    def _process(self):
        df = self.runs
        # filter out unwanted data
        df = df[['core', 'freq', 'iteration', 'metric', 'value']]
        df = df[(df.metric == "total DMIPS") | (df.metric.apply(lambda x: x.endswith("power")))]

        # make power column
        df = df.pivot_table(index=["core", "freq", "iteration"], columns="metric", values="value")
        df = self._mergePower(df)
        df = df.reset_index()
        for core in df.core.unique():
            if "power" not in df:
                df["power"] = df[df.core == core][core + "_power"]
            else:
                df.ix[df.core == core, "power"] = df[df.core == core][core + "_power"]
            df = df.drop(core + "_power", axis=1)

        self.runs = df[['core', 'freq', 'power', 'total DMIPS']]

    def _mergePower(self, df):
        '''Sums multiple DAQ channel columns if they have the same name but
        have sequential letters suffixed
        '''
        from string import ascii_lowercase

        channels = [x.strip("_power") for x in df.columns if x.endswith("power")]
        potential_merge = {}
        for channel in sorted(channels):
            if channel[:-1] not in potential_merge:
                potential_merge[channel[:-1]] = [channel[-1]]
            else:
                potential_merge[channel[:-1]] += channel[-1]

        for core, suffixes in potential_merge.iteritems():
            for i, letter in enumerate(ascii_lowercase[:len(suffixes)]):
                if suffixes[i] != letter:
                    break
            else:
                cols = [core + x + "_power" for x in suffixes]
                df[core + "_power"] = df[cols].sum(axis=1)
                df = df.drop(cols, axis=1)
        return df

    def set_defaults(self):
        super(PowerPerfPlot, self).set_defaults()
        self._attr['title'] = "Power vs Performance\n"
        self._attr['xlabel'] = "Performance"
        self._attr['xunit'] = "DMIPS"
        self._attr['ylabel'] = "Power"
        self._attr['yunit'] = "W"
        self._attr['fig_size'] = (15, 10)
        self._attr["x_col"] = "total DMIPS"
        self._attr["y_col"] = "power"
        self._attr["legend_col"] = "core"
        self._attr["group_col"] = "freq"
