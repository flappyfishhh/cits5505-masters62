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
  const timeSpanButtons = document.querySelectorAll('.time-span-button'); // Buttons for time spans
  const yearDropdown = document.getElementById('year-select'); // Year dropdown
  const loadDatasetButton = document.getElementById('load-dataset'); // Load Dataset button
  const clearChartButton = document.getElementById('clear-chart');

  let solarChartInstance = null; // Declare the chart instance only once
  let dropdownCount = 1; // Keep track of the number of dropdowns
  let selectedTimeSpan = 'year'; // Default time span
  let selectedYear = null; // Store the selected year

  // Function to update dropdown options dynamically
  function updateDropdownOptions() {
    const selectedValues = Array.from(dropdownContainer.querySelectorAll('select'))
      .map(dropdown => dropdown.value)
      .filter(value => value); // Filter out empty values

    dropdownContainer.querySelectorAll('select').forEach(dropdown => {
      const currentValue = dropdown.value; // Preserve the current value
      const options = dropdown.querySelectorAll('option');

      options.forEach(option => {
        if (selectedValues.includes(option.value) && option.value !== currentValue) {
          option.style.display = 'none'; // Hide already-selected options
        } else {
          option.style.display = ''; // Show available options
        }
      });
    });
  }

  // Add event listener for time span buttons
  timeSpanButtons.forEach(button => {
    button.addEventListener('click', function () {
      // Remove active class from all buttons and add it to the clicked button
      timeSpanButtons.forEach(btn => btn.classList.remove('active'));
      this.classList.add('active');
      selectedTimeSpan = this.getAttribute('data-timespan');
    });
  });

  // Add event listener for the "Add another city" checkbox
  addCityCheckbox.addEventListener('change', function () {
    if (addCityCheckbox.checked && dropdownCount < 4) {
      dropdownCount++;

      // Get the options from the first dropdown
      const firstDropdown = document.getElementById('dataset-select-1');
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

      // Reset the checkbox to unchecked after adding a dropdown
      addCityCheckbox.checked = false;

      // Disable the checkbox if the maximum number of dropdowns is reached
      if (dropdownCount === 4) {
        addCityCheckbox.disabled = true;
      }

      // Add event listener for the delete button
      const deleteButton = newDropdown.querySelector('.delete-city-button');
      deleteButton.addEventListener('click', function () {
        const dropdownId = this.getAttribute('data-dropdown-id');
        const dropdownItem = document.getElementById(`dropdown-item-${dropdownId}`);
        dropdownItem.remove();

        // Decrease the dropdown count and re-enable the checkbox if necessary
        dropdownCount--;
        if (dropdownCount < 4) {
          addCityCheckbox.disabled = false;
        }

        // Update dropdown options after deletion
        updateDropdownOptions();
      });

      // Add event listener for the new dropdown to update options dynamically
      const newSelect = newDropdown.querySelector('select');
      newSelect.addEventListener('change', updateDropdownOptions);

      // Update dropdown options after adding a new dropdown
      updateDropdownOptions();
    }
  });

// Populate the year dropdown dynamically based on available data
function populateYearDropdown(dataArray) {
  const allYears = new Set();

  dataArray.forEach(data => {
    data.data.forEach(row => {
      const year = new Date(row.date).getFullYear();
      allYears.add(year);
    });
  });

  const sortedYears = Array.from(allYears).sort();
  yearDropdown.innerHTML = `
    <option value="" disabled selected>Select a year</option>
    <option value="all">Select All</option>
  `; // Reset dropdown and add "Select All"

  sortedYears.forEach(year => {
    const option = document.createElement('option');
    option.value = year;
    option.textContent = year;
    yearDropdown.appendChild(option);
  });
}

// Add event listener for year selection
yearDropdown.addEventListener('change', function () {
  selectedYear = this.value === "all" ? null : parseInt(this.value, 10); // If "Select All" is chosen, set selectedYear to null
});


  // Add event listener for the "Load Dataset" button
  loadDatasetButton.addEventListener('click', function () {
    const selectedFileIds = [];
    const dropdowns = dropdownContainer.querySelectorAll('select');

    // Collect selected file IDs from dropdowns
    dropdowns.forEach((dropdown) => {
      if (dropdown && dropdown.value) {
        selectedFileIds.push(dropdown.value);
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
          populateYearDropdown(dataArray); // Populate the year dropdown dynamically
          alert('Dataset loaded successfully! Select a year to visualize.');
        })
        .catch(error => {
          console.error('Error loading dataset:', error);
          alert('Failed to load dataset. Please try again.');
        });
    } else {
      alert('Please select at least one dataset to load.');
    }
  });

  // Add event listener for year selection
  yearDropdown.addEventListener('change', function () {
    selectedYear = parseInt(this.value, 10); // Store the selected year
  });

  // Add event listener for the visualize button
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
          // Filter data based on the selected year
          const filteredDataArray = dataArray.map(data => {
            return {
              ...data,
              data: data.data.filter(row => {
                const year = new Date(row.date).getFullYear();
                return selectedYear ? year === selectedYear : true; // Filter by year if selected
              })
            };
          });

          const chartDataArray = filteredDataArray.map(data => processFileData(data.data, selectedTimeSpan));
          renderChart(chartDataArray, cityNames); // Pass city names to the renderChart function
        })
        .catch(error => {
          console.error('Error fetching file data:', error);
        });
    } else {
      alert('Please select at least one dataset.');
    }
  });

  // Process file data for Chart.js based on the selected time span
  function processFileData(fileData, timeSpan) {
    const groupedData = {};

    fileData.forEach(row => {
      if (row.solar_exposure !== null) {
        const date = new Date(row.date);
        let key;

        // Group data based on the selected time span
        switch (timeSpan) {
          case 'year':
            key = date.getFullYear();
            break;
          case '6months':
            key = `${date.getFullYear()}-${Math.ceil((date.getMonth() + 1) / 6)}`; // 1 or 2 for first/second half
            break;
          case 'month':
            key = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`; // Year-Month (e.g., "2025-01")
            break;
          case 'week':
            const weekStart = new Date(date);
            weekStart.setDate(date.getDate() - date.getDay()); // Start of the week (Sunday)
            key = weekStart.toISOString().split('T')[0]; // Format as YYYY-MM-DD
            break;
          case 'day':
            key = date.toISOString().split('T')[0]; // Format as YYYY-MM-DD
            break;
          default:
            key = date.getFullYear();
        }

        if (!groupedData[key]) {
          groupedData[key] = { total: 0, count: 0 };
        }
        groupedData[key].total += row.solar_exposure;
        groupedData[key].count += 1;
      }
    });

    const labels = Object.keys(groupedData).sort((a, b) => {
      if (timeSpan === 'month') {
        return new Date(a).getTime() - new Date(b).getTime(); // Sort by date for months
      }
      return a.localeCompare(b, undefined, { numeric: true }); // Numeric sort for other cases
    });

    const values = labels.map(key => parseFloat((groupedData[key].total / groupedData[key].count).toFixed(2)));
    return { labels, values };
  }

  function renderChart(chartDataArray, cityNames) {
    const canvas = document.getElementById('solarChart');
    const ctx = canvas.getContext('2d');
  
    // Destroy the existing chart instance if it exists
    if (solarChartInstance) {
      solarChartInstance.destroy();
      solarChartInstance = null;
    }
  
    const combinedLabels = Array.from(new Set(chartDataArray.flatMap(data => data.labels))).sort();
  
    const datasets = chartDataArray.map((chartData, index) => {
      const values = combinedLabels.map(label => {
        const labelIndex = chartData.labels.indexOf(label);
        return labelIndex !== -1 ? chartData.values[labelIndex] : null; // Fill null for missing labels
      });
  
      return {
        label: cityNames[index],
        data: values,
        borderColor: `rgba(${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, ${Math.floor(Math.random() * 255)}, 1)`,
        borderWidth: 2,
        fill: false
      };
    });
  
    solarChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: combinedLabels,
        datasets: datasets
      },
      options: {
        responsive: true,
        plugins: {
          tooltip: {
            callbacks: {
              label: function (context) {
                const value = context.raw;
                return value !== null ? `Value: ${value.toFixed(2)}` : 'No Data';
              }
            }
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Time'
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

  clearChartButton.addEventListener('click', function () {
    if (solarChartInstance) {
      solarChartInstance.destroy(); // Destroy the existing chart instance
      solarChartInstance = null; // Reset the chart instance
    }
  
    // Clear the canvas
    const canvas = document.getElementById('solarChart');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  
    // Optionally, clear the region description
    const descriptionContainer = document.getElementById('region-description');
    if (descriptionContainer) {
      descriptionContainer.innerHTML = '<p>Chart cleared. Please select a dataset to visualize.</p>';
    }
  });
  
  // Export chart as PDF
  const { jsPDF } = window.jspdf;

  exportPdfButton.addEventListener('click', function () {
    const canvas = document.getElementById('solarChart');
    const chartImage = canvas.toDataURL('image/png', 1.0); // Convert chart to image

    const pdf = new jsPDF('landscape'); // Create a new PDF in landscape mode
    pdf.setFontSize(18);
    pdf.text('Solar Exposure Analysis', 10, 10); // Add a title
    pdf.addImage(chartImage, 'PNG', 10, 20, 280, 150); // Add the chart image to the PDF
    pdf.save('solar_analysis.pdf'); // Save the PDF
  });

  // Export chart as PNG/JPG
  exportImageButton.addEventListener('click', function () {
    const canvas = document.getElementById('solarChart');
    canvas.toBlob(function (blob) {
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'solar_analysis.png'; // Default filename
      link.click();
    }, 'image/png');
  });
});