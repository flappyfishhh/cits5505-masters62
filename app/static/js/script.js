$(function(){
    // Wait for the DOM to be fully loaded

    // Automatically hide flash messages after 3 seconds
    setTimeout(function(){
      $('.flashes').fadeOut(); // Smoothly fade out elements with class 'flashes'
    }, 3000); // 3000 milliseconds = 3 seconds
  
  const datasetSelect = document.getElementById('dataset-select');
  const loadDatasetButton = document.getElementById('load-dataset');

  if (datasetSelect && loadDatasetButton) {
    loadDatasetButton.addEventListener('click', function () {
      const selectedFileId = datasetSelect.value; // The file ID is the filename
      if (selectedFileId) {
        fetch(`/get-file-data/${selectedFileId}`)
          .then(response => {
            if (!response.ok) {
              throw new Error('Failed to fetch file data');
            }
            return response.json();
          })
          .then(data => {
            console.log('File Data:', data);
            const chartData = processFileData(data.data); // Process the file data for Chart.js
            renderChart(chartData); // Render the chart
          })
          .catch(error => {
            console.error('Error fetching file data:', error);
            //alert('Failed to load dataset. Please try again.');
          });
      } else {
        alert('Please select a dataset first.');
      }
    });
  }

  // Process file data for Chart.js
  function processFileData(fileData) {
    const labels = [];
    const values = [];
  
    fileData.forEach(row => {
      if (row.solar_exposure !== null) { // Skip rows with missing data
        labels.push(row.date); // Use the 'date' field for labels
        values.push(row.solar_exposure); // Use the 'solar_exposure' field for values
      }
    });
  
    return { labels, values };
  }

  // Render the chart using Chart.js
  let solarChartInstance = null; // Variable to store the chart instance


  function renderChart(chartData) {
    const canvas = document.getElementById('solarChart');
    const ctx = canvas.getContext('2d');

    // Destroy the existing chart instance if it exists
    if (solarChartInstance) {
      console.log('Destroying existing chart instance');
      solarChartInstance.destroy();
      solarChartInstance = null; // Reset the chart instance
    }

    // Clear the canvas manually
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Create a new chart instance
    console.log('Creating new chart instance');
    solarChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: chartData.labels,
        datasets: [{
          label: 'Solar Exposure (MJ/m²)',
          data: chartData.values,
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 2,
          fill: false
        }]
      },
      options: {
        responsive: true,
        scales: {
          x: {
            title: {
              display: true,
              text: 'Date'
            }
          },
          y: {
            title: {
              display: true,
              text: 'Solar Exposure (MJ/m²)'
            }
          }
        }
      }
    });
  }
 });
  