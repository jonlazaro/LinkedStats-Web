/* 
	Author: Jon Lazaro Aduna (jlazaro@deusto.es)
*/
var chartlist = []

function getContainerColor(waste) {
switch(waste)
{
  case 'Organic waste':
    return "#BFBBB8";
  case 'Plastic waste':
    return "#F2EC3D";
  case 'Paper waste':
    return "#22A9D6";
  case 'Glass waste':
    return "#45D645";
  case 'Voluminous waste':
    return "#FF8214";
}
}

// Little hack for pie chart colors (order is important, got by try-error }:-))
function getContainerColorRange() {
return ["#BFBBB8", "#45D645", "#F2EC3D", "#FF8214", "#22A9D6"];
}

// Function for drawing "KG per year" data.
function draw_kg_per_year(data) {
  var jsonObj = []

  // Adapt data to NVD3.js format
  for (wastetype in data)
  {
      var tempjson = {};
      tempjson['key'] = wastetype;
      tempjson['values'] = [];
      for (year in data[wastetype])
        tempjson['values'].push([parseInt(year), parseInt(data[wastetype][year])]);
      tempjson['color'] = getContainerColor(wastetype);
      jsonObj.push(tempjson);
  }

  // Draw MultiBar chart
  nv.addGraph(function() {
      var chart = nv.models.multiBarChart()
                  .x(function(d) { return d[0] })
                  .y(function(d) { return d[1] })
                  .clipEdge(true);

      chart.xAxis
          .tickFormat(function(d) {
            var date = new Date();
            date.setYear(parseInt(d));
            return d3.time.format('%Y')(date)
          });
          //.tickFormat(d3.format('.f'));

      chart.yAxis
          .tickFormat(function(d) { return d3.format(',f')(d) + ' kg' });

      d3.select('#kg_per_year svg')
          .datum(jsonObj)
        .transition().duration(500).call(chart);

      nv.utils.windowResize(chart.update);

      chart.legend.dispatch.on('legendClick.updateExamples', function() {
        setTimeout(function() {
          for (var i = 0; i < chartlist.length; i++)
            //alert(chartlist[i]);
            chartlist[i].update();
        }, 100);
      });

      chartlist.push(chart);

      return chart;
  });
}

function draw_kg_per_year_pie(data) {
  var piediv = document.getElementById('kg_per_year_pies');

  var yearlist = Object.keys(data[Object.keys(data)[0]]);

  for (var i = 0; i < yearlist.length; i++) {
    var htmlid = 'kg_per_year_pie_' + yearlist[i];
    piediv.innerHTML += '<div class="minichartdiv span2" id="' + htmlid + '"><h4 class="text-center">' + yearlist[i] + '</h4><svg></svg></div>';

    var jsondatalist = [];
    for (wastetype in data)
    {
        for (year in data[wastetype]) {
          if (year == yearlist[i]) {
            jsondatalist.push({"label": wastetype, "color": getContainerColor(wastetype), "value": parseInt(data[wastetype][year])});
          }
        }
    }
    nv.addGraph(generate_pie_chart_function(htmlid, jsondatalist));
  }
}

// Closure function factory with "local" variables (for each iteration of the loop)
function generate_pie_chart_function(htmlid, datalist) {
return function() {
  var chart = nv.models.pieChart()
    .x(function(d) { return d.label })
    .y(function(d) { return d.value })
    .showLabels(false)
    .values(function(d) { return d })
    .color(getContainerColorRange())
    .showLegend(false)
    .margin({top: -20, bottom: 15, left: -15, right: -15});

  d3.select('#' + htmlid + ' svg')
      .datum([datalist])
      .transition().duration(1200)
      .call(chart);

  chartlist.push(chart);
  return chart;
};
}

// Function for drawing "KG per person" data.
function draw_kg_per_person_with_biscay_avg(municipality_data, biscay_avg_adata, municipality_name) {
  // Adapt data to NVD3.js format
  var jsonObj = [];
  var maxvalue = 0;

  var tempjson = {};
  tempjson['key'] = municipality_name;
  tempjson['bar'] = true;
  tempjson['values'] = [];
  for (year in municipality_data) {
    if (municipality_data[year] > maxvalue)
      maxvalue = municipality_data[year];
    tempjson['values'].push([parseInt(year), municipality_data[year]]);
  }
  jsonObj.push(tempjson);

  var tempjson = {};
  tempjson['key'] = 'Biscay average';
  tempjson['values'] = [];
  for (year in biscay_avg_adata)
    tempjson['values'].push([parseInt(year), biscay_avg_adata[year]]);
  jsonObj.push(tempjson);
  
  // Draw MultiBar chart
  nv.addGraph(function() {
      var chart = nv.models.linePlusBarChart()
            //.margin({top: 30, right: 60, bottom: 50, left: 70})
            .x(function(d) { return d[0] })
            .y(function(d) { return d[1] })
            .color(d3.scale.category20().range());

      chart.xAxis
          .tickValues(Object.keys(municipality_data))
          .tickFormat(function(d) {
            var date = new Date();
            date.setYear(parseInt(d));
            return d3.time.format('%Y')(date)
          });
          //.tickFormat(d3.format('.f'));

      chart.y1Axis
          .tickFormat(function(d) { return d3.format(',.4f')(d) + ' kg' });

      chart.y2Axis
          .tickFormat(function(d) { return d3.format(',.4f')(d) + ' kg' });

      // Max limit will be the maximum value + 0.5 rounded to 1 decimal
      var maxlimit = Math.round((parseFloat(maxvalue) + 0.5) * 10)/10
      chart.bars.forceY([0, maxlimit]);
      chart.lines.forceY([0, maxlimit]);

      d3.select('#kg_per_person svg')
          .datum(jsonObj)
        .transition().duration(500).call(chart);

      nv.utils.windowResize(chart.update);

      return chart;
  });
}