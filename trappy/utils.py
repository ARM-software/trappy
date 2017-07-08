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

import pandas as pd
import numpy as np

"""Generic functions that can be used in multiple places in trappy
"""

def listify(to_select):
    """Utitlity function to handle both single and
    list inputs
    """

    if not isinstance(to_select, list):
        to_select = [to_select]

    return to_select

def handle_duplicate_index(data,
                           max_delta=0.000001):
    """Handle duplicate values in index

    :param data: The timeseries input
    :type data: :mod:`pandas.Series`

    :param max_delta: Maximum interval adjustment value that
        will be added to duplicate indices
    :type max_delta: float

    Consider the following case where a series needs to be reindexed
    to a new index (which can be required when different series need to
    be combined and compared):
    ::

        import pandas
        values = [0, 1, 2, 3, 4]
        index = [0.0, 1.0, 1.0, 6.0, 7.0]
        series = pandas.Series(values, index=index)
        new_index = [0.0, 1.0, 2.0, 3.0, 4.0, 6.0, 7.0]
        series.reindex(new_index)

    The above code fails with:
    ::

        ValueError: cannot reindex from a duplicate axis

    The function :func:`handle_duplicate_axis` changes the duplicate values
    to
    ::

        >>> import pandas
        >>> from trappy.utils import handle_duplicate_index

        >>> values = [0, 1, 2, 3, 4]
        index = [0.0, 1.0, 1.0, 6.0, 7.0]
        series = pandas.Series(values, index=index)
        series = handle_duplicate_index(series)
        print series.index.values
        >>> [ 0.        1.        1.000001  6.        7.      ]

    """

    index = data.index
    new_index = index.values

    dups = index.get_duplicates()

    for dup in dups:
        # Leave one of the values intact
        dup_index_left = index.searchsorted(dup, side="left")
        dup_index_right = index.searchsorted(dup, side="right") - 1
        num_dups = dup_index_right - dup_index_left + 1

        # Calculate delta that needs to be added to each duplicate
        # index
        try:
            delta = (index[dup_index_right + 1] - dup) / num_dups
        except IndexError:
            # dup_index_right + 1 is outside of the series (i.e. the
            # dup is at the end of the series).
            delta = max_delta

        # Clamp the maximum delta added to max_delta
        if delta > max_delta:
            delta = max_delta

        # Add a delta to the others
        dup_index_left += 1
        while dup_index_left <= dup_index_right:
            new_index[dup_index_left] += delta
            delta += delta
            dup_index_left += 1

    return data.reindex(new_index)

# Iterate fast over all rows in a data frame and apply fn
def apply_callback(df, fn, *kwargs):
    """
    A generic API to apply a function onto a data frame and optionally pass
    it an argument (kwargs). This is faster than `DataFrame.apply` method.

    :param df: DataFrame to apply fn onto
    :type df: :mod:`pandas.DataFrame`

    :param fn: Function that is applied onto the DataFrame
    :type fn: function

    :param kwargs: Optional argument to pass to the callback
    :type kwargs: dict
    """
    iters = df.itertuples()
    event_tuple = iters.next()

    # Column names beginning with underscore will not be preserved in tuples
    # due to constraints on namedtuple field names, so store mappings from
    # column name to column number for each trace event.
    col_idxs = { name: idx for idx, name in enumerate(['Time'] + df.columns.tolist()) }

    while True:
        if not event_tuple:
            break
        event_dict = { col: event_tuple[idx] for col, idx in col_idxs.iteritems() }

        if kwargs:
            fn(event_dict, kwargs)
        else:
            fn(event_dict)

        event_tuple = next(iters, None)

def merge_dfs(pr_df, sec_df, pivot):
    """
    Merge information from secondary DF into a primary DF. During the merge
    take into account the latest secondary rows based on time stamp. A pivot
    is used to differentiate between rows. The returned DF has same number of
    rows as the primary DF.

    For example, Say the following is a primary DF:
                cpu util_avg    __line
    Time
    2943.184105 7   825         1
    2943.184106 6   292         2
    2943.184108 7   850         4
    2943.184110 6   315         6

    And the following is a secondary DF:
                cpu cpu_scale_factor    __line
    Time
    2943.184105 7   1                   0
    2943.184107 6   2                   3
    2943.184109 7   3                   5

    And, pivot = 'cpu'. Then, the returned DF will look like:
                __line  cpu cpu_scale_factor    util_avg
    Time
    2943.184105 1       7   1.0                 825.0
    2943.184106 2       6   NaN                 292.0
    2943.184108 4       7   1.0                 850.0
    2943.184110 6       6   2.0                 315.0

    :param pr_df: Primary data frame to merge into.
    :type pr_df: :mod:`pandas.DataFrame`

    :param sec_df: Secondary data frame as source of data.
    :type sec_df: :mod:`pandas.DataFrame`
    """

    # Keep track of last secondary event
    pivot_map = {}

    # An array accumating dicts with merged data
    merged_data = []
    def df_fn(data):
        # Store the latest secondary info
        if data['Time'][0] == 'secondary':
            pivot_map[data[pivot]] = data
            # Get rid of primary/secondary labels
            data['Time'] = data['Time'][1]
            return

        # Propogate latest secondary info
        for key, value in data.iteritems():
            if key == pivot:
                continue
            # Fast check for if value is nan (faster than np.isnan + try/except)
            if value != value and pivot_map.has_key(data[pivot]):
                data[key] = pivot_map[data[pivot]][key]

        # Get rid of primary/secondary labels
        data['Time'] = data['Time'][1]
        merged_data.append(data)

    df = pd.concat([pr_df, sec_df], keys=['primary', 'secondary']).sort_values(by='__line')
    apply_callback(df, df_fn)
    merged_df = pd.DataFrame.from_dict(merged_data)
    merged_df.set_index('Time', inplace=True)

    return merged_df
