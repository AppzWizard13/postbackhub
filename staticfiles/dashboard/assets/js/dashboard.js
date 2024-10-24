$(function () {
  // Fetch the raw JSON string from the script tag
  var scriptTag = document.getElementById('positions-data'); 
  var data_set = scriptTag.textContent; // Get the content of the script tag
  console.log('Raw Data:', data_set); // Log the raw JSON string for debugging
  
  // Parse JSON string to JavaScript object
  var positions = JSON.parse(data_set);
  console.log('Parsed Positions:', positions); // Log the parsed JavaScript object

  // Remove the script tag from the DOM if needed
  scriptTag.remove(); // This line will remove the script tag

  // Variables to hold categories (trading symbols), earnings, and expenses
  var categories = [];
  var earnings = [];
  var expenses = [];

  // Process positions to populate categories, earnings, and expenses
  positions.forEach(function(position) {
      categories.push(position.tradingSymbol);  // Add trading symbol to categories

      // If realizedProfit is positive, add to earnings; otherwise, add to expenses
      if (position.realizedProfit > 0) {
          earnings.push(position.realizedProfit);
          expenses.push(0);  // No expense for positive profit
      } else {
          earnings.push(0);  // No earnings for negative profit
          expenses.push(Math.abs(position.realizedProfit));  // Convert negative to positive for expense
      }
  });

  // =====================================
  // Profit Chart
  // =====================================
  var chart = {
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

      colors: ["#5D87FF", "#FF0000"],

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
          max: Math.max(...earnings.concat(expenses)),  // Dynamically adjust the max value
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

  var chart = new ApexCharts(document.querySelector("#chart"), chart);
  chart.render();
});
