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


# pylint can't see any of the dynamically allocated classes of FTrace
# pylint: disable=no-member

from itertools import ifilter
import os
import re
import pandas as pd

from trappy.utils import listify

def _plot_freq_hists(allfreqs, what, axis, title):
    """Helper function for plot_freq_hists

    allfreqs is the output of a Cpu*Power().get_all_freqs() (for
    example, CpuInPower.get_all_freqs()).  what is a string: "in" or
    "out"

    """
    import trappy.plot_utils

    for ax, actor in zip(axis, allfreqs):
        this_title = "freq {} {}".format(what, actor)
        this_title = trappy.plot_utils.normalize_title(this_title, title)
        xlim = (0, allfreqs[actor].max())

        trappy.plot_utils.plot_hist(allfreqs[actor], ax, this_title, "KHz", 20,
                             "Frequency", xlim, "default")

class FTrace(object):
    """A wrapper class that initializes all the classes of a given run

    - The FTrace class can receive the following optional parameters.

    :param path: Path contains the path to the trace file.  If no path is given, it
        uses the current directory by default.  If path is a file, and ends in
        .dat, it's run through "trace-cmd report".  If it doesn't end in
        ".dat", then it must be the output of a trace-cmd report run.  If path
        is a directory that contains a trace.txt, that is assumed to be the
        output of "trace-cmd report".  If path is a directory that doesn't
        have a trace.txt but has a trace.dat, it runs trace-cmd report on the
        trace.dat, saves it in trace.txt and then uses that.

    :param name: is a string describing the trace.

    :param normalize_time: is used to make all traces start from time 0 (the
        default).  If normalize_time is False, the trace times are the same as
        in the trace file.

    :param scope: can be used to limit the parsing done on the trace.  The default
        scope parses all the traces known to trappy.  If scope is thermal, only
        the thermal classes are parsed.  If scope is sched, only the sched
        classes are parsed.

    :param events: A list of strings containing the name of the trace
        events that you want to include in this FTrace object.  The
        string must correspond to the event name (what you would pass
        to "trace-cmd -e", i.e. 4th field in trace.txt)

    :param window: a tuple indicating a time window.  The first
        element in the tuple is the start timestamp and the second one
        the end timestamp.  Timestamps are relative to the first trace
        event that's parsed.  If you want to trace until the end of
        the trace, set the second element to None.  If you want to use
        timestamps extracted from the trace file use "abs_window".

    :param abs_window: a tuple indicating an absolute time window.
        This parameter is similar to the "window" one but its values
        represent timestamps that are not normalized, (i.e. the ones
        you find in the trace file)

    :type path: str
    :type name: str
    :type normalize_time: bool
    :type scope: str
    :type events: list
    :type window: tuple
    :type abs_window: tuple

    This is a simple example:
    ::

        import trappy
        trappy.FTrace("trace_dir")

    """

    thermal_classes = {}

    sched_classes = {}

    dynamic_classes = {}

    def __init__(self, path=".", name="", normalize_time=True, scope="all",
                 events=[], window=(0, None), abs_window=(0, None)):
        self.name = name
        self.trace_path, self.trace_path_raw = self.__process_path(path)
        self.class_definitions = self.dynamic_classes.copy()
        self.basetime = 0
        self.normalized_time = normalize_time

        self.__add_events(listify(events))

        if scope == "thermal":
            self.class_definitions.update(self.thermal_classes.items())
        elif scope == "sched":
            self.class_definitions.update(self.sched_classes.items())
        elif scope != "custom":
            self.class_definitions.update(self.thermal_classes.items() +
                                          self.sched_classes.items())

        self.trace_classes = []
        for attr, class_def in self.class_definitions.iteritems():
            trace_class = class_def()
            setattr(self, attr, trace_class)
            self.trace_classes.append(trace_class)

        self.__parse_trace_file(window, abs_window)
        self.__parse_trace_file(window, abs_window, raw=True)
        self.__finalize_objects()

        if normalize_time:
            self.normalize_time()

    def __process_path(self, basepath):
        """Process the path and return the path to the trace text file"""

        if os.path.isfile(basepath):
            trace_name = os.path.splitext(basepath)[0]
        else:
            trace_name = os.path.join(basepath, "trace")

        trace_txt = trace_name + ".txt"
        trace_raw = trace_name + ".raw.txt"
        trace_dat = trace_name + ".dat"

        if os.path.isfile(trace_dat):
            # Both TXT and RAW traces must always be generated
            if not os.path.isfile(trace_txt) or \
               not os.path.isfile(trace_raw):
                self.__run_trace_cmd_report(trace_dat)
            # TXT (and RAW) traces must match the most recent binary trace
            elif os.path.getmtime(trace_txt) < os.path.getmtime(trace_dat):
                self.__run_trace_cmd_report(trace_dat)

        if not os.path.isfile(trace_raw):
            trace_raw = None

        return trace_txt, trace_raw

    def __run_trace_cmd_report(self, fname):
        """Run "trace-cmd report fname > fname.txt"
           and "trace-cmd report -R fname > fname.raw.txt"

        The resulting traces are stored in files with extension ".txt"
        and ".raw.txt" respectively.  If fname is "my_trace.dat", the
        trace is stored in "my_trace.txt" and "my_trace.raw.txt".  The
        contents of the destination files are overwritten if they
        exist.

        """
        from subprocess import check_output

        cmd = ["trace-cmd", "report"]

        if not os.path.isfile(fname):
            raise IOError("No such file or directory: {}".format(fname))

        raw_trace_output = os.path.splitext(fname)[0] + ".raw.txt"
        trace_output = os.path.splitext(fname)[0] + ".txt"
        cmd.append(fname)

        with open(os.devnull) as devnull:
            try:
                out = check_output(cmd, stderr=devnull)
            except OSError as exc:
                if exc.errno == 2 and not exc.filename:
                    raise OSError(2, "trace-cmd not found in PATH, is it installed?")
                else:
                    raise

            # Add the -R flag to the trace-cmd
            # for raw parsing
            cmd.insert(-1, "-R")
            raw_out = check_output(cmd, stderr=devnull)

        with open(trace_output, "w") as fout:
            fout.write(out)

        with open(raw_trace_output, "w") as fout:
            fout.write(raw_out)

    def get_duration(self):
        """Returns the largest time value of all classes,
        returns 0 if the data frames of all classes are empty"""
        durations = []

        for trace_class in self.trace_classes:
            try:
                durations.append(trace_class.data_frame.index[-1])
            except IndexError:
                pass

        if len(durations) == 0:
            return 0

        if self.normalized_time:
            return max(durations)
        else:
            return max(durations) - self.basetime

    @classmethod
    def register_class(cls, cobject, scope="all"):
        """Register the class as an Event. This function
        can be used to register a class which is associated
        with an FTrace unique word.

        .. seealso::

            :mod:`trappy.dynamic.register_dynamic` :mod:`trappy.dynamic.register_class`

        """

        if not hasattr(cobject, "name"):
            cobject.name = cobject.unique_word.split(":")[0]

        # Add the class to the classes dictionary
        if scope == "all":
            cls.dynamic_classes[cobject.name] = cobject
        else:
            getattr(cls, scope + "_classes")[cobject.name] = cobject

    def get_filters(self, key=""):
        """Returns an array with the available filters.

        :param key: If specified, returns a subset of the available filters
            that contain 'key' in their name (e.g., :code:`key="sched"` returns
            only the :code:`"sched"` related filters)."""
        filters = []

        for cls in self.class_definitions:
            if re.search(key, cls):
                filters.append(cls)

        return filters

    def normalize_time(self):
        """Normalize the time of all the trace classes

        :param basetime: The offset which needs to be subtracted from
            the time index
        :type basetime: float
        """
        for trace_class in self.trace_classes:
            trace_class.normalize_time(self.basetime)

    def add_parsed_event(self, name, dfr, pivot=None):
        """Add a dataframe to the events in this trace

        This function lets you add other events that have been parsed
        by other tools to the collection of events in this instance.  For
        example, assuming you have some events in a csv, you could add
        them to a trace instance like this:

        >>> trace = trappy.FTrace()
        >>> counters_dfr = pd.DataFrame.from_csv("counters.csv")
        >>> trace.add_parsed_event("pmu_counters", counters_dfr)

        Now you can access :code:`trace.pmu_counters` as you would with any
        other trace event and other trappy classes can interact with
        them.

        :param name: The attribute name in this FTrace instance.  As in the example above, if :code:`name` is "pmu_counters", the parsed event will be accessible using :code:`trace.pmu_counters`.
        :type name: str

        :param dfr: :mod:`pandas.DataFrame` containing the events.  Its index should be time in seconds.  Its columns are the events.
        :type dfr: :mod:`pandas.DataFrame`

        :param pivot: The data column about which the data can be grouped
        :type pivot: str

        """
        from trappy.base import Base
        from trappy.dynamic import DynamicTypeFactory, default_init

        if hasattr(self, name):
            raise ValueError("event {} already present".format(name))

        kwords = {
            "__init__": default_init,
            "unique_word": name + ":",
            "name": name,
        }

        trace_class = DynamicTypeFactory(name, (Base,), kwords)
        self.class_definitions[name] = trace_class

        event = trace_class()
        event.data_frame = dfr
        if pivot:
            event.pivot = pivot

        setattr(self, name, event)

    def __add_events(self, events):
        """Add events to the class_definitions

        If the events are known to trappy just add that class to the
        class definitions list.  Otherwise, register a class to parse
        that event

        """

        from trappy.dynamic import DynamicTypeFactory, default_init
        from trappy.base import Base

        # TODO: scopes should not be hardcoded (nor here nor in the FTrace object)
        all_scopes = [self.thermal_classes, self.sched_classes,
                      self.dynamic_classes]
        known_events = {k: v for sc in all_scopes for k, v in sc.iteritems()}

        for event_name in events:
            for cls in known_events.itervalues():
                if (event_name == cls.unique_word) or \
                   (event_name + ":" == cls.unique_word):
                    self.class_definitions[event_name] = cls
                    break
            else:
                kwords = {
                    "__init__": default_init,
                    "unique_word": event_name + ":",
                    "name": event_name,
                }
                trace_class = DynamicTypeFactory(event_name, (Base,), kwords)
                self.class_definitions[event_name] = trace_class

    def __populate_metadata(self, trace_fh):
        """Populates trace metadata"""

        # Meta Data as expected to be found in the parsed trace header
        metadata_keys = ["version", "cpus"]

        for key in metadata_keys:
            setattr(self, "_" + key, None)

        while metadata_keys:
            line = trace_fh.readline()

            #The trace has been exhausted
            if not line:
                return

            metadata_pattern = r"^\b(" + "|".join(metadata_keys) + \
                               r")\b\s*=\s*([0-9]+)"
            match = re.search(metadata_pattern, line)
            if match:
                setattr(self, "_" + match.group(1), match.group(2))
                metadata_keys.remove(match.group(1))

            if re.search(r"^\s+[^\[]+-\d+\s+\[\d+\]\s+\d+\.\d+:", line):
                # Reached a valid trace line, abort metadata population
                return

    def __populate_data(self, fin, cls_for_unique_word, window, abs_window):
        """Append to trace data from a txt trace"""

        def contains_unique_word(line, unique_words=cls_for_unique_word.keys()):
            for unique_word in unique_words:
                if unique_word in line:
                    return True
            return False

        special_fields_regexp = re.compile(r"^\s+([^\[]+)-(\d+)\s+\[(\d+)\]\s+([0-9]+\.[0-9]+):")
        start_match = re.compile(r"[A-Za-z0-9_]+=")

        for line in ifilter(contains_unique_word, fin):
            for unique_word, cls in cls_for_unique_word.iteritems():
                if unique_word in line:
                    trace_class = cls
                    break
            else:
                raise ValueError("No unique in {}".format(line))

            line = line[:-1]

            special_fields_match = special_fields_regexp.match(line)
            comm = special_fields_match.group(1)
            pid = int(special_fields_match.group(2))
            cpu = int(special_fields_match.group(3))
            timestamp = float(special_fields_match.group(4))

            if not self.basetime:
                self.basetime = timestamp

            if (timestamp < window[0] + self.basetime) or \
               (timestamp < abs_window[0]):
                continue

            if (window[1] and timestamp > window[1] + self.basetime) or \
               (abs_window[1] and timestamp > abs_window[1]):
                return

            try:
                data_start_idx =  start_match.search(line).start()
            except AttributeError:
                continue

            data_str = line[data_start_idx:]

            # Remove empty arrays from the trace
            data_str = re.sub(r"[A-Za-z0-9_]+=\{\} ", r"", data_str)

            trace_class.append_data(timestamp, comm, pid, cpu, data_str)

    def __parse_trace_file(self, window, abs_window, raw=False):
        """parse the trace and create a pandas DataFrame"""

        # Memoize the unique words to speed up parsing the trace file
        cls_for_unique_word = {}
        for trace_name in self.class_definitions.iterkeys():
            trace_class = getattr(self, trace_name)

            if trace_class.parse_raw != raw:
                continue

            unique_word = trace_class.unique_word
            cls_for_unique_word[unique_word] = trace_class

        if len(cls_for_unique_word) == 0:
            return

        if raw:
            if self.trace_path_raw != None:
                trace_file = self.trace_path_raw
            else:
                return
        else:
            trace_file = self.trace_path

        with open(trace_file) as fin:
            self.__populate_metadata(fin)

            # Rewind the file
            fin.seek(0)

            self.__populate_data(fin, cls_for_unique_word, window, abs_window)

    def __finalize_objects(self):
        for trace_class in self.trace_classes:
            trace_class.create_dataframe()
            trace_class.finalize_object()

    # TODO: Move thermal specific functionality

    def get_all_freqs_data(self, map_label):
        """get an array of tuple of names and DataFrames suitable for the
        allfreqs plot"""

        cpu_in_freqs = self.cpu_in_power.get_all_freqs(map_label)
        cpu_out_freqs = self.cpu_out_power.get_all_freqs(map_label)

        ret = []
        for label in map_label.values():
            in_label = label + "_freq_in"
            out_label = label + "_freq_out"

            cpu_inout_freq_dict = {in_label: cpu_in_freqs[label],
                                   out_label: cpu_out_freqs[label]}
            dfr = pd.DataFrame(cpu_inout_freq_dict).fillna(method="pad")
            ret.append((label, dfr))

        try:
            gpu_freq_in_data = self.devfreq_in_power.get_all_freqs()
            gpu_freq_out_data = self.devfreq_out_power.get_all_freqs()
        except KeyError:
            gpu_freq_in_data = gpu_freq_out_data = None

        if gpu_freq_in_data is not None:
            inout_freq_dict = {"gpu_freq_in": gpu_freq_in_data["freq"],
                               "gpu_freq_out": gpu_freq_out_data["freq"]
                           }
            dfr = pd.DataFrame(inout_freq_dict).fillna(method="pad")
            ret.append(("GPU", dfr))

        return ret

    def plot_freq_hists(self, map_label, ax):
        """Plot histograms for each actor input and output frequency

        ax is an array of axis, one for the input power and one for
        the output power

        """

        in_base_idx = len(ax) / 2

        try:
            devfreq_out_all_freqs = self.devfreq_out_power.get_all_freqs()
            devfreq_in_all_freqs = self.devfreq_in_power.get_all_freqs()
        except KeyError:
            devfreq_out_all_freqs = None
            devfreq_in_all_freqs = None

        out_allfreqs = (self.cpu_out_power.get_all_freqs(map_label),
                        devfreq_out_all_freqs, ax[0:in_base_idx])
        in_allfreqs = (self.cpu_in_power.get_all_freqs(map_label),
                       devfreq_in_all_freqs, ax[in_base_idx:])

        for cpu_allfreqs, devfreq_freqs, axis in (out_allfreqs, in_allfreqs):
            if devfreq_freqs is not None:
                devfreq_freqs.name = "GPU"
                allfreqs = pd.concat([cpu_allfreqs, devfreq_freqs], axis=1)
            else:
                allfreqs = cpu_allfreqs

            allfreqs.fillna(method="pad", inplace=True)
            _plot_freq_hists(allfreqs, "out", axis, self.name)

    def plot_load(self, mapping_label, title="", width=None, height=None,
                  ax=None):
        """plot the load of all the clusters, similar to how compare runs did it

        the mapping_label has to be a dict whose keys are the cluster
        numbers as found in the trace and values are the names that
        will appear in the legend.

        """
        import trappy.plot_utils

        load_data = self.cpu_in_power.get_load_data(mapping_label)
        try:
            gpu_data = pd.DataFrame({"GPU":
                                     self.devfreq_in_power.data_frame["load"]})
            load_data = pd.concat([load_data, gpu_data], axis=1)
        except KeyError:
            pass

        load_data = load_data.fillna(method="pad")
        title = trappy.plot_utils.normalize_title("Utilization", title)

        if not ax:
            ax = trappy.plot_utils.pre_plot_setup(width=width, height=height)

        load_data.plot(ax=ax)

        trappy.plot_utils.post_plot_setup(ax, title=title)

    def plot_normalized_load(self, mapping_label, title="", width=None,
                             height=None, ax=None):
        """plot the normalized load of all the clusters, similar to how compare runs did it

        the mapping_label has to be a dict whose keys are the cluster
        numbers as found in the trace and values are the names that
        will appear in the legend.

        """
        import trappy.plot_utils

        load_data = self.cpu_in_power.get_normalized_load_data(mapping_label)
        if "load" in self.devfreq_in_power.data_frame:
            gpu_dfr = self.devfreq_in_power.data_frame
            gpu_max_freq = max(gpu_dfr["freq"])
            gpu_load = gpu_dfr["load"] * gpu_dfr["freq"] / gpu_max_freq

            gpu_data = pd.DataFrame({"GPU": gpu_load})
            load_data = pd.concat([load_data, gpu_data], axis=1)

        load_data = load_data.fillna(method="pad")
        title = trappy.plot_utils.normalize_title("Normalized Utilization", title)

        if not ax:
            ax = trappy.plot_utils.pre_plot_setup(width=width, height=height)

        load_data.plot(ax=ax)

        trappy.plot_utils.post_plot_setup(ax, title=title)

    def plot_allfreqs(self, map_label, width=None, height=None, ax=None):
        """Do allfreqs plots similar to those of CompareRuns

        if ax is not none, it must be an array of the same size as
        map_label.  Each plot will be done in each of the axis in
        ax

        """
        import trappy.plot_utils

        all_freqs = self.get_all_freqs_data(map_label)

        setup_plot = False
        if ax is None:
            ax = [None] * len(all_freqs)
            setup_plot = True

        for this_ax, (label, dfr) in zip(ax, all_freqs):
            this_title = trappy.plot_utils.normalize_title("allfreqs " + label,
                                                        self.name)

            if setup_plot:
                this_ax = trappy.plot_utils.pre_plot_setup(width=width,
                                                        height=height)

            dfr.plot(ax=this_ax)
            trappy.plot_utils.post_plot_setup(this_ax, title=this_title)
