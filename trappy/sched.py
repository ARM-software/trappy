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


"""Definitions of scheduler events registered by the FTrace class"""

from trappy.base import Base
from trappy.dynamic import register_dynamic
from trappy.ftrace import FTrace

class SchedLoadAvgSchedGroup(Base):
    """Corresponds to Linux kernel trace event sched_load_avg_sched_group"""

    unique_word = "sched_load_avg_sg:"
    """The unique word that will be matched in a trace line"""

    _cpu_mask_column = "cpus"

    pivot = "cpus"
    """The Pivot along which the data is orthogonal"""

    def finalize_object(self):
        """This condition is necessary to force column 'cpus' to be printed
        as 8 digits w/ leading 0
        """
        if self._cpu_mask_column in self.data_frame.columns:
            dfr = self.data_frame[self._cpu_mask_column].apply('{:0>8}'.format)
            self.data_frame[self._cpu_mask_column] = dfr

FTrace.register_class(SchedLoadAvgSchedGroup, "sched")

class SchedLoadAvgTask(Base):
    """Corresponds to Linux kernel trace event sched_load_avg_task"""

    unique_word = "sched_load_avg_task:"
    """The unique word that will be matched in a trace line"""

    pivot = "pid"
    """The Pivot along which the data is orthogonal"""

    def get_pids(self, key=""):
        """Returns a list of (comm, pid) that contain
        'key' in their 'comm'."""
        dfr = self.data_frame.drop_duplicates(subset=['comm', 'pid'])
        dfr = dfr.ix[:, ['comm', 'pid']]

        return dfr[dfr['comm'].str.contains(key)].values.tolist()

FTrace.register_class(SchedLoadAvgTask, "sched")

# pylint doesn't like globals that are not ALL_CAPS
# pylint: disable=invalid-name
SchedLoadAvgCpu = register_dynamic("SchedLoadAvgCpu",
                                   "sched_load_avg_cpu:",
                                   "sched", pivot="cpu")
"""Load and Utilization Signals for CPUs"""

SchedContribScaleFactor = register_dynamic("SchedContribScaleFactor",
                                           "sched_contrib_scale_f:",
                                           "sched")
"""Event to register tracing of contrib factor"""

class SchedCpuCapacity(Base):
    """Corresponds to Linux kernel trace event sched/cpu_capacity"""

    unique_word = "cpu_capacity:"
    """The unique word that will be matched in a trace line"""

    pivot = "cpu"
    """The Pivot along which the data is orthogonal"""

    def finalize_object(self):
        """This renaming is necessary because our cpu related pivot is 'cpu'
        and not 'cpu_id'. Otherwise you cannot 'mix and match' with other
        classes
        """
        self.data_frame.rename(columns={'cpu_id':'cpu'}, inplace=True)
        self.data_frame.rename(columns={'state' :'capacity'}, inplace=True)

FTrace.register_class(SchedCpuCapacity, "sched")

SchedSwitch = register_dynamic("SchedSwitch",
                               "sched_switch",
                               "sched",
                               parse_raw=True)
"""Register SchedSwitch Event"""
# pylint: enable=invalid-name

class SchedCpuFrequency(Base):
    """Corresponds to Linux kernel trace event power/cpu_frequency"""

    unique_word = "cpu_frequency:"
    """The unique word that will be matched in a trace line"""

    pivot = "cpu"
    """The Pivot along which the data is orthogonal"""

    def finalize_object(self):
        """This renaming is necessary because our cpu related pivot is 'cpu'
        and not 'cpu_id'. Otherwise you cannot 'mix and match' with other
        classes
        """
        self.data_frame.rename(columns={'cpu_id':'cpu'}, inplace=True)
        self.data_frame.rename(columns={'state' :'frequency'}, inplace=True)

FTrace.register_class(SchedCpuFrequency, "sched")
