$(function () {
    // Fetch the raw JSON string from the script tag
    var scriptTag = document.getElementById('positions-data'); 
    var data_set = scriptTag ? scriptTag.textContent : ""; // Get the content of the script tag if it exists
    // Retrieve series data from the DOM element and parse it as JSON
    // Retrieve series data from the DOM element and parse it as JSON
    var breakup_seriesTag = document.getElementById('breakup_series');
    var breakup_seriesdata = breakup_seriesTag ? breakup_seriesTag.textContent : "";
    try {
      // Parse the JSON data and round each number
      var parsedSeriesData = JSON.parse(breakup_seriesdata);
      var breakup_series = parsedSeriesData.map(num => Math.round(num));
    
      // Check if the second value is negative and make it positive if so
      if (breakup_series[1] < 0) {
        breakup_series[1] = Math.abs(breakup_series[1]);
      }
      
      // Set colors based on the second value's positivity/negativity
      var colors = [
        "#3267ff", // First color - Blue (default)
        breakup_series[1] > 0 ? "#fa2d2d" : "#00FF00", // Red if positive, Green if originally negative
        "#fff47d" // Third color - Orange (default)
      ];
    
    } catch (e) {
      console.error("Failed to parse breakup_seriesdata as JSON:", e);
      var breakup_series = [0, 0, 0]; // Default values if parsing fails
      var colors = ["#3267ff", "#fa2d2d", "#fff47d"]; // Default color scheme
    }
    

    // Retrieve labels data from the DOM element and parse it as JSON
    var breakup_labelsTag = document.getElementById('breakup_labels');
    var breakup_labelsdata = breakup_labelsTag ? breakup_labelsTag.textContent : "";

    // Convert single quotes to double quotes if necessary
    breakup_labelsdata = breakup_labelsdata.replace(/'/g, '"');

    try {
      var breakup_labels = JSON.parse(breakup_labelsdata);
    } catch (e) {
      console.error("Failed to parse breakup_labelsdata as JSON:", e);
      var breakup_labels = ["Label1", "Label2", "Label3"]; // Default labels if parsing fails
    }

    // Initialize positions array
    var positions = [];

    // Check if data_set has content
    if (!data_set || data_set.trim() === "") {
        console.log('No data found in Raw Data');
    } else {
        try {
            // Parse JSON string to JavaScript object
            positions = JSON.parse(data_set);
            console.log('Parsed Positions:', positions); // Log the parsed JavaScript object
        } catch (e) {
            console.error('Error parsing JSON data:', e); // Log error if JSON parsing fails
        }
    }

    // Remove the script tag from the DOM if it exists
    if (scriptTag) {
        scriptTag.remove();
    }

    // Variables to hold categories (trading symbols), earnings, and expenses
    var categories = [];
    var earnings = [];
    var expenses = [];
    var chart_earning = [];

    // Process positions to populate categories, earnings, and expenses
    if (positions.length > 0) {
        positions.forEach(function(position) {
            categories.push(position.tradingSymbol);  // Add trading symbol to categories
              chart_earning.push(position.realizedProfit);
              chart_earning.push(0);
            // If realizedProfit is positive, add to earnings; otherwise, add to expenses
            if (position.realizedProfit > 0) {
                earnings.push(position.realizedProfit);
                expenses.push(0);  // No expense for positive profit
            } else {
                earnings.push(0);  // No earnings for negative profit
                expenses.push(Math.abs(position.realizedProfit));  // Convert negative to positive for expense
            }
        });
    } else {
        // Default values if no positions data is available
        categories = ["Default Symbol"];
        earnings = [0];
        expenses = [0];
    }

    // =====================================
    // Profit Chart
    // =====================================
    var chartOptions = {
        series: [
            { name: "Profit of Position:", data: earnings },
            { name: "Loss of Position:", data: expenses },
        ],

        chart: {
            type: "bar",
            height: 345,
            offsetX: -15,
            toolbar: { show: true },
            foreColor: "#adb0bb",
            fontFamily: 'inherit',
            sparkline: { enabled: false },
        },

        colors: ["#3569ff", "#FF0000"],

        plotOptions: {
            bar: {
                horizontal: false,
                columnWidth: "35%",
                borderRadius: [6],
                borderRadiusApplication: 'end',
                borderRadiusWhenStacked: 'all'
            },
        },
        markers: { size: 0 },

        dataLabels: {
            enabled: false,
        },

        legend: {
            show: false,
        },

        grid: {
            borderColor: "rgba(0,0,0,0.1)",
            strokeDashArray: 3,
            xaxis: {
                lines: {
                    show: false,
                },
            },
        },

        xaxis: {
            type: "category",
            categories: categories,  // Dynamic trading symbols
            labels: {
                style: { cssClass: "grey--text lighten-2--text fill-color" },
            },
        },

        yaxis: {
            show: true,
            min: 0,
            max: Math.max(...earnings.concat(expenses)) || 10,  // Dynamically adjust the max value or use default
            tickAmount: 4,
            labels: {
                style: {
                    cssClass: "grey--text lighten-2--text fill-color",
                },
            },
        },
        stroke: {
            show: true,
            width: 3,
            lineCap: "butt",
            colors: ["transparent"],
        },

        tooltip: { theme: "light" },

        responsive: [
            {
                breakpoint: 600,
                options: {
                    plotOptions: {
                        bar: {
                            borderRadius: 3,
                        }
                    },
                }
            }
        ]
    };

    var chart = new ApexCharts(document.querySelector("#chart"), chartOptions);
    chart.render();


    
  // =====================================
  // Earning
  // =====================================
  var earning = {
    chart: {
      id: "sparkline3",
      type: "area",
      height: 60,
      sparkline: {
        enabled: true,
      },
      group: "sparklines",
      fontFamily: "Plus Jakarta Sans', sans-serif",
      foreColor: "#adb0bb",
    },
    series: [
      {
        name: "Earnings",
        color: "#49BEFF",
        data:chart_earning,
      },
    ],
    stroke: {
      curve: "smooth",
      width: 2,
    },
    fill: {
      colors: ["#f3feff"],
      type: "solid",
      opacity: 0.05,
    },

    markers: {
      size: 0,
    },
    tooltip: {
      theme: "dark",
      fixed: {
        enabled: true,
        position: "right",
      },
      x: {
        show: false,
      },
    },
  };
  new ApexCharts(document.querySelector("#earning"), earning).render();



    // =====================================
  // Breakup
  // =====================================
  var breakup = {
    color: "#adb5bd",
    series: breakup_series, // Use the parsed series data
    labels: breakup_labels, // Use the parsed labels data
    chart: {
      width: 180,
      type: "donut",
      fontFamily: "Plus Jakarta Sans', sans-serif",
      foreColor: "#adb0bb",
    },
    plotOptions: {
      pie: {
        startAngle: 0,
        endAngle: 360,
        donut: {
          size: '75%',
        },
      },
    },
    stroke: {
      show: false,
    },

    dataLabels: {
      enabled: false,
    },

    legend: {
      show: false,
    },
    colors: colors,

    responsive: [
      {
        breakpoint: 991,
        options: {
          chart: {
            width: 150,
          },
        },
      },
    ],
    tooltip: {
      theme: "dark",
      fillSeriesColor: false,
    },
  };

  var chart = new ApexCharts(document.querySelector("#breakup"), breakup);
  chart.render();
})

