#    Copyright 2015-2017 ARM Limited
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


import os
import sys
import unittest
import utils_tests
import trappy
import tempfile
import numpy as np
from trappy.base import trace_parser_explode_array

sys.path.append(os.path.join(utils_tests.TESTS_DIRECTORY, "..", "trappy"))

class TestBaseMethods(unittest.TestCase):
    """Test simple methods that don't need to set up a directory"""
    def test_trace_parser_explode_array(self):
        """TestBaseMethods: Basic test of trace_parser_explode_array()"""

        line = "cpus=0000000f freq=1400000 raw_cpu_power=189 load={3 2 12 2} power=14"
        expected = "cpus=0000000f freq=1400000 raw_cpu_power=189 load0=3 load1=2 load2=12 load3=2 power=14"
        array_lengths = {"load": 4}

        result = trace_parser_explode_array(line, array_lengths)
        self.assertEquals(result, expected)

    def test_trace_parser_explode_array_nop(self):
        """TestBaseMethods: trace_parser_explode_array() returns the same string if there's no array in it"""

        line = "cpus=0000000f freq=1400000 raw_cpu_power=189 load0=3 load1=2 load2=12 load3=2 power=14"
        array_lengths = {"load": 0}

        result = trace_parser_explode_array(line, array_lengths)
        self.assertEquals(result, line)

    def test_trace_parser_explode_array_2(self):
        """TestBaseMethods: trace_parser_explode_array() works if there's two arrays in the string"""

        line = "cpus=0000000f freq=1400000 load={3 2 12 2} power=14 req_power={10 7 2 34}"
        expected = "cpus=0000000f freq=1400000 load0=3 load1=2 load2=12 load3=2 power=14 req_power0=10 req_power1=7 req_power2=2 req_power3=34"
        array_lengths = {'load': 4, 'req_power': 4}

        result = trace_parser_explode_array(line, array_lengths)
        self.assertEquals(result, expected)

    def test_trace_parser_explode_array_diff_lengths(self):
        """TestBaseMethods: trace_parser_explode_array() expands arrays that are shorter than the expected length

        trace_parser_explode_array() has to be able to deal with an array of
        size 2 if we tell it in other parts of the trace it is four.

        """

        line = "cpus=0000000f freq=1400000 load={3 2} power=14"
        expected = "cpus=0000000f freq=1400000 load0=3 load1=2 load2=0 load3=0 power=14"
        array_lengths = {'load': 4}

        result = trace_parser_explode_array(line, array_lengths)
        self.assertEquals(result, expected)

class TestBase(utils_tests.SetupDirectory):
    """Incomplete tests for the Base class"""

    def __init__(self, *args, **kwargs):
        super(TestBase, self).__init__(
             [("../doc/trace.txt", "trace.txt"),
              ("trace_equals.txt", "trace_equals.txt")],
             *args,
             **kwargs)

    def test_parse_empty_array(self):
        """TestBase: Trace with empty array creates a valid DataFrame"""

        in_data = """     kworker/4:1-397   [004]   720.741315: thermal_power_cpu_get: cpus=000000f0 freq=1900000 raw_cpu_power=1259 load={} power=61
     kworker/4:1-397   [004]   720.741349: thermal_power_cpu_get: cpus=0000000f freq=1400000 raw_cpu_power=189 load={} power=14"""

        expected_columns = set(["__comm", "__pid", "__cpu", "__line", "cpus", "freq",
                                "raw_cpu_power", "power"])

        with open("trace.txt", "w") as fout:
            fout.write(in_data)

        trace = trappy.FTrace()
        dfr = trace.cpu_in_power.data_frame

        self.assertEquals(set(dfr.columns), expected_columns)
        self.assertEquals(dfr["power"].iloc[0], 61)

    def test_parse_special_fields(self):
        """TestBase: Task name, PID, CPU and timestamp are properly paresed """

        events = {
                # Trace events using [global] clock format ([us] resolution)
                1001.456789 : { 'task': 'rcu_preempt',       'pid': 1123, 'cpu': 001 },
                1002.456789 : { 'task': 'rs:main',           'pid': 2123, 'cpu': 002 },
                1003.456789 : { 'task': 'AsyncTask #1',      'pid': 3123, 'cpu': 003 },
                1004.456789 : { 'task': 'kworker/1:1H',      'pid': 4123, 'cpu': 004 },
                1005.456789 : { 'task': 'jbd2/sda2-8',       'pid': 5123, 'cpu': 005 },
                1006.456789 : { 'task': 'IntentService[',    'pid': 6123, 'cpu': 005 },
                1006.456789 : { 'task': r'/system/bin/.s$_?.u- \a]}c\./ef[.12]*[[l]in]ger',
                                'pid': 1234, 'cpu': 666 },
                # Trace events using [boot] clock format ([ns] resolution)
                1011456789000: { 'task': 'rcu_preempt',       'pid': 1123, 'cpu': 001 },
                1012456789000: { 'task': 'rs:main',           'pid': 2123, 'cpu': 002 },
                1013456789000: { 'task': 'AsyncTask #1',      'pid': 3123, 'cpu': 003 },
                1014456789000: { 'task': 'kworker/1:1H',      'pid': 4123, 'cpu': 004 },
                1015456789000: { 'task': 'jbd2/sda2-8',       'pid': 5123, 'cpu': 005 },
                1016456789000: { 'task': 'IntentService[',    'pid': 6123, 'cpu': 005 },
                1016456789000: { 'task': r'/system/bin/.s$_?.u- \a]}c\./ef[.12]*[[l]in]ger',
                                'pid': 1234, 'cpu': 666 },
        }

        in_data = """"""
        for timestamp in sorted(events):
            in_data+="{0:>16s}-{1:d} [{2:04d}] {3}: event0:   tag=value\n".\
                    format(
                        events[timestamp]['task'],
                        events[timestamp]['pid'],
                        events[timestamp]['cpu'],
                        timestamp
                        )

        expected_columns = set(["__comm", "__pid", "__cpu", "__line", "tag"])

        with open("trace.txt", "w") as fout:
            fout.write(in_data)

        ftrace_parser = trappy.register_dynamic_ftrace("Event0", "event0", scope="sched")
        trace = trappy.FTrace(normalize_time=False)
        dfr = trace.event0.data_frame

        self.assertEquals(set(dfr.columns), expected_columns)

        for timestamp, event in events.iteritems():
            if type(timestamp) == int:
                timestamp = float(timestamp) / 1e9
            self.assertEquals(dfr["__comm"].loc[timestamp], event['task'])
            self.assertEquals(dfr["__pid"].loc[timestamp],  event['pid'])
            self.assertEquals(dfr["__cpu"].loc[timestamp],  event['cpu'])

        trappy.unregister_dynamic_ftrace(ftrace_parser)


    def test_parse_values_concatenation(self):
        """TestBase: Trace with space separated values created a valid DataFrame"""

        in_data = """     rcu_preempt-7     [000]    73.604532: my_sched_stat_runtime:   comm=Space separated taskname pid=7 runtime=262875 [ns] vruntime=17096359856 [ns]"""

        expected_columns = set(["__comm", "__pid", "__cpu", "__line", "comm", "pid", "runtime", "vruntime"])

        with open("trace.txt", "w") as fout:
            fout.write(in_data)

        ftrace_parser = trappy.register_dynamic_ftrace("sched_stat_runtime",
                                       "my_sched_stat_runtime", scope="sched")
        trace = trappy.FTrace()
        dfr = trace.sched_stat_runtime.data_frame

        self.assertEquals(set(dfr.columns), expected_columns)
        self.assertEquals(dfr["comm"].iloc[0], "Space separated taskname")
        self.assertEquals(dfr["pid"].iloc[0], 7)
        self.assertEquals(dfr["runtime"].iloc[0], 262875)
        self.assertEquals(dfr["vruntime"].iloc[0], 17096359856)

        trappy.unregister_dynamic_ftrace(ftrace_parser)

    def test_get_dataframe(self):
        """TestBase: Thermal.data_frame["thermal_zone"] exists and
           it contains a known value"""
        dfr = trappy.FTrace().thermal.data_frame

        self.assertTrue("thermal_zone" in dfr.columns)
        self.assertEquals(dfr["temp"].iloc[0], 68786)

    def test_write_csv(self):
        """TestBase: Base::write_csv() creates a valid csv"""
        from csv import DictReader

        fname = "thermal.csv"
        trappy.FTrace().thermal.write_csv(fname)

        with open(fname) as fin:
            csv_reader = DictReader(fin)

            self.assertTrue("Time" in csv_reader.fieldnames)
            self.assertTrue("temp" in csv_reader.fieldnames)

            first_data = csv_reader.next()
            self.assertEquals(first_data["Time"], "0.0")
            self.assertEquals(first_data["temp"], "68786")

    def test_normalize_time(self):
        """TestBase: Base::normalize_time() normalizes the time of the trace"""
        thrm = trappy.FTrace().thermal

        last_prev_time = thrm.data_frame.index[-1]

        basetime = thrm.data_frame.index[0]
        thrm.normalize_time(basetime)

        last_time = thrm.data_frame.index[-1]
        expected_last_time = last_prev_time - basetime

        self.assertEquals(round(thrm.data_frame.index[0], 7), 0)
        self.assertEquals(round(last_time - expected_last_time, 7), 0)

    def test_line_num(self):
        """TestBase: Test line number functionality"""
        trace = trappy.FTrace()
        self.assertEquals(trace.lines, 804)

        df = trace.thermal.data_frame
        self.assertEquals(df.iloc[0]['__line'], 0);
        self.assertEquals(df.iloc[-1]['__line'], 792);

        df = trace.thermal_governor.data_frame
        self.assertEquals(df.iloc[0]['__line'], 11);
        self.assertEquals(df.iloc[-1]['__line'], 803)

    def test_equals_in_field_value(self):
        """TestBase: Can parse events with fields with values containing '='"""
        trace = trappy.FTrace("trace_equals.txt", events=['equals_event'])

        df = trace.equals_event.data_frame
        self.assertSetEqual(set(df.columns),
                            set(["__comm", "__pid", "__cpu", "__line", "my_field"]))
        self.assertListEqual(df["my_field"].tolist(),
                             ["foo", "foo=bar", "foo=bar=baz", 1,
                              "1=2", "1=foo", "1foo=2"])

    def test_merge_dfs(self):
        trace_file = tempfile.mktemp(dir="/tmp", suffix=".txt")
        lines = [
        "            adbd-5709  [007]  2943.184105: sched_contrib_scale_f: cpu=7 cpu_scale_factor=1\n"
        "            adbd-5709  [007]  2943.184105: sched_load_avg_cpu:   cpu=7 util_avg=825\n"
        "     ->transport-5713  [006]  2943.184106: sched_load_avg_cpu:   cpu=6 util_avg=292\n"
        "     ->transport-5713  [006]  2943.184107: sched_contrib_scale_f: cpu=6 cpu_scale_factor=2\n"
        "            adbd-5709  [007]  2943.184108: sched_load_avg_cpu:   cpu=7 util_avg=850\n"
        "            adbd-5709  [007]  2943.184109: sched_contrib_scale_f: cpu=7 cpu_scale_factor=3\n"
        "            adbd-5709  [007]  2943.184110: sched_load_avg_cpu:   cpu=6 util_avg=315\n"
        ]
        with open(trace_file, 'w') as fh:
            for line in lines:
                fh.write(line)

        trace = trappy.ftrace.FTrace(trace_file, events=['sched_contrib_scale_f', 'sched_load_avg_cpu'],
                              normalize_time=False)

        df1 = trace.sched_load_avg_cpu.data_frame[['cpu', 'util_avg', '__line']]
        df2 = trace.sched_contrib_scale_f.data_frame[['cpu', 'cpu_scale_factor', '__line']]
        df3 = trappy.utils.merge_dfs(df1, df2, 'cpu')
        cpu_scale_list = ["NaN" if np.isnan(x) else x for x in df3["cpu_scale_factor"].tolist()]
        self.assertListEqual(cpu_scale_list, [1.0, "NaN", 1.0, 2.0])
