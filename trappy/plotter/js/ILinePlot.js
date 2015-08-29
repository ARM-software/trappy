/*
 *    Copyright 2015-2015 ARM Limited
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var ILinePlot = ( function() {

   var graphs = new Array();
   var syncObjs = new Array();

   var convertToDataTable = function (d, index_col) {

        var columns = _.keys(d);
        var out = [];
        var index_col_default = false;
        var index;

        if (index_col == undefined) {

            var index = [];

            columns.forEach(function(col) {
                index = index.concat(Object.keys(d[col]));
            });

            index = $.unique(index);
            index_col_default = true;
            index = index.sort(function(a, b) {
                return (parseFloat(a) - parseFloat(b));
            });
        } else {
            index = d[index_col];
            columns.splice(columns.indexOf(index_col), 1);
        }

        for (var ix in index) {

            var ix_val = ix;

            if (index_col_default)
                ix_val = index[ix];

            var row = [parseFloat(ix_val)];
            columns.forEach(function(col) {

                var val = d[col][ix_val];
                if (val == undefined)
                    val = null;

                row.push(val);
            });
            out.push(row);
        }

        var labels = ["index"].concat(columns);
        return {
            data: out,
            labels: labels
        }
    };

    var purge = function() {
        for (var div_name in graphs) {
            if (document.getElementById(div_name) == null) {
                delete graphs[div_name];
            }
        }
    };

    var sync = function(group) {

        var syncGraphs = Array();
        var xRange;
        var yRange;
        var syncZoom = true;

        for (var div_name in graphs) {

            if (graphs[div_name].group == group) {
                syncGraphs.push(graphs[div_name].graph);
                syncZoom = syncZoom & graphs[div_name].syncZoom;

                var xR = graphs[div_name].graph.xAxisRange();
                var yR = graphs[div_name].graph.yAxisRange();

                if (xRange != undefined) {
                    if (xR[0] < xRange[0])
                        xRange[0] = xR[0];
                    if (xR[1] > xRange[1])
                        xRange[1] = xR[1];
                } else
                    xRange = xR;

                if (yRange != undefined) {
                    if (yR[0] < yRange[0])
                        yRange[0] = yR[0];
                    if (yR[1] > yRange[1])
                        yRange[1] = yR[1];
                } else
                    yRange = yR;
            }
        }

        if (syncGraphs.length >= 2) {
            if (syncZoom) {
                if (syncObjs[group] != undefined)
                    syncObjs[group].detach();

                syncObjs[group] = Dygraph.synchronize(syncGraphs, {
                    zoom: true,
                    selection: false,
                    range: true
                });
            }

            $.each(syncGraphs, function(g) {
                var graph = syncGraphs[g];

                graph.updateOptions({
                    valueRange: yRange,
                    dateWindow: xRange
                });

                if (graph.padFront_ == undefined) {
                    graph.padFront_ = true;
                    var _decoy_elem = new Array(graph.rawData_[0].length);
                    graph.rawData_.unshift(_decoy_elem);
                }
                graph.rawData_[0][0] = xRange[0];

                if (graph.padBack_ == undefined) {
                    graph.padBack_ = true;
                    var _decoy_elem = new Array(graph.rawData_[0].length);
                    graph.rawData_.push(_decoy_elem);
                }
                graph.rawData_[graph.rawData_.length - 1][0] = xRange[1];
            });
        }
    };

    var generate = function(div_name, base) {
        var json_file = base + "plotter_data/" + div_name + ".json";
            $.getJSON( json_file, function( data ) {
                create_graph(data);
                purge();
                if (data.syncGroup != undefined)
                    sync(data.syncGroup);
            });
    };

    var create_graph = function(t_info) {
        var tabular = convertToDataTable(t_info.data, t_info.index_col);

        var graph = new Dygraph(document.getElementById(t_info.name), tabular.data, {
            legend: 'always',
            title: t_info.title,
            labels: tabular.labels,
            labelsDivStyles: {
                'textAlign': 'right'
            },
            rollPeriod: 1,
            animatedZooms: true,
            connectSeparatedPoints: true,
            showRangeSelector: t_info.rangesel,
            rangeSelectorHeight: 50,
            stepPlot: t_info.step_plot,
            logscale: t_info.logscale,
            fillGraph: t_info.fill_graph,
            labelsDiv: t_info.name + "_legend",
            errorBars: false,
            valueRange: t_info.valueRange

        });

        graphs[t_info.name] =
            {
                graph: graph,
                group: t_info.syncGroup,
                syncZoom: t_info.syncZoom
            };

    };

    return {
        generate: generate
    };

}());
