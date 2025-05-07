$(function () {
  // Automatically hide flash messages after 3 seconds
  setTimeout(function () {
    $('.flashes').fadeOut();
  }, 3000);

  const dropdownContainer = document.getElementById('dropdown-container');
  const addCityCheckbox = document.getElementById('add-city-checkbox');
  const visualizeButton = document.getElementById('visualize-datasets');
  const exportPdfButton = document.getElementById('export-pdf');
  const exportImageButton = document.getElementById('export-image');
  let solarChartInstance = null; // Declare the chart instance only once
  let dropdownCount = 1; // Keep track of the number of dropdowns

  // Add event listener for the checkbox
  if (addCityCheckbox && dropdownContainer) {
    addCityCheckbox.addEventListener('change', function () {
      if (addCityCheckbox.checked && dropdownCount < 4) {
        dropdownCount++;

        // Get the options from the first dropdown
        const firstDropdown = document.getElementById('dataset-select-1');
        if (!firstDropdown) return;

        const optionsHTML = firstDropdown.innerHTML;

        // Create a new dropdown with a delete button
        const newDropdown = document.createElement('div');
        newDropdown.classList.add('dropdown-item', 'mt-4', 'flex', 'items-center');
        newDropdown.setAttribute('id', `dropdown-item-${dropdownCount}`);
        newDropdown.innerHTML = `
          <div class="flex-grow">
            <label for="dataset-select-${dropdownCount}" class="block text-lg font-medium mb-2">Choose another dataset:</label>
            <select id="dataset-select-${dropdownCount}" class="border border-gray-300 rounded-md p-2 w-full">
              ${optionsHTML}
            </select>
          </div>
          <button class="ml-4 bg-red-500 text-white px-4 py-2 rounded-md delete-city-button" data-dropdown-id="${dropdownCount}">Delete</button>
        `;
        dropdownContainer.appendChild(newDropdown);

        // Reset the checkbox
        addCityCheckbox.checked = false;

        if (dropdownCount === 4) {
          addCityCheckbox.disabled = true;
        }

        // Add event listener for the delete button
        const deleteButton = newDropdown.querySelector('.delete-city-button');
        deleteButton.addEventListener('click', function () {
          const dropdownId = this.getAttribute('data-dropdown-id');
          const dropdownItem = document.getElementById(`dropdown-item-${dropdownId}`);
          dropdownItem.remove();

          dropdownCount--;
          if (dropdownCount < 4) {
            addCityCheckbox.disabled = false;
          }
        });
      }
    });
  }

  // Add event listener for the visualize button
  if (visualizeButton && dropdownContainer) {
    visualizeButton.addEventListener('click', function () {
      const selectedFileIds = [];
      const cityNames = []; // Store city names for the legend

      // Loop through all dropdowns and collect valid selections
      const dropdowns = dropdownContainer.querySelectorAll('select');
      dropdowns.forEach((dropdown) => {
        if (dropdown && dropdown.value) {
          selectedFileIds.push(dropdown.value);
          cityNames.push(dropdown.options[dropdown.selectedIndex].text); // Get the city name
        }
      });

      if (selectedFileIds.length > 0) {
        const fetchPromises = selectedFileIds.map(fileId =>
          fetch(`/get-file-data/${fileId}`).then(response => {
            if (!response.ok) throw new Error(`Failed to fetch file data for ${fileId}`);
            return response.json();
          })
        );

        Promise.all(fetchPromises)
          .then(dataArray => {
            const chartDataArray = dataArray.map(data => processFileData(data.data));
            renderChart(chartDataArray, cityNames); // Pass city names to the renderChart function
          })
          .catch(error => {
            console.error('Error fetching file data:', error);
          });
      } else {
        alert('Please select at least one dataset.');
      }
    });
  }

  // Process file data for Chart.js (Yearly Averages)
  function processFileData(fileData) {
    const yearlyData = {};

    fileData.forEach(row => {
      if (row.solar_exposure !== null) {
        const year = new Date(row.date).getFullYear();
        if (!yearlyData[year]) {
          yearlyData[year] = { total: 0, count: 0 };
        }
        yearlyData[year].total += row.solar_exposure;
        yearlyData[year].count += 1;
      }
    });

    const labels = Object.keys(yearlyData).sort();
    const values = labels.map(year => (yearlyData[year].total / yearlyData[year].count).toFixed(2));

    return { labels, values };
  }

  // Render the chart using Chart.js
  function renderChart(chartDataArray, cityNames) {
    const canvas = document.getElementById('solarChart');
    const ctx = canvas.getContext('2d');

    if (solarChartInstance) {
      solarChartInstance.destroy();
      solarChartInstance = null;
    }

    // Combine all unique labels (years) from all datasets
    const combinedLabels = Array.from(new Set(chartDataArray.flatMap(data => data.labels))).sort();

    // Align each dataset's values with the combinedLabels array
    const datasets = chartDataArray.map((chartData, index) => {
      const values = combinedLabels.map(label => {
        const labelIndex = chartData.labels.indexOf(label);
        return labelIndex !== -1 ? chartData.values[labelIndex] : null; // Fill null for missing years
      });

      return {
        label: cityNames[index], // Use city name for the legend
        data: values,
        borderColor: `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 1)`,
        borderWidth: 2,
        fill: false
      };
    });

    // Create the chart
    solarChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: combinedLabels,
        datasets: datasets
      },
      options: {
        responsive: true,
        scales: {
          x: {
            title: {
              display: true,
              text: 'Year'
            }
          },
          y: {
            title: {
              display: true,
              text: 'Average Solar Exposure (MJ/m²)'
            }
          }
        }
      }
    });
  }

  // Export chart as PNG/JPG
  if (exportImageButton) {
    exportImageButton.addEventListener('click', function () {
      const canvas = document.getElementById('solarChart');
      canvas.toBlob(function (blob) {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'solar_analysis.png'; // Default filename
        link.click();
      }, 'image/png');
    });
  }
});