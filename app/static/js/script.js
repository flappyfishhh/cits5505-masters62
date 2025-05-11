$(function () {
  // Constants and Variables
  const dropdownContainer = document.getElementById('dropdown-container');
  const addCityCheckbox = document.getElementById('add-city-checkbox');
  const visualizeButton = document.getElementById('visualize-datasets');
  const exportPdfButton = document.getElementById('export-pdf');
  const exportImageButton = document.getElementById('export-image');
  const timeSpanButtons = document.querySelectorAll('.time-span-button');
  const yearDropdown = document.getElementById('year-select');
  const loadDatasetButton = document.getElementById('load-dataset');
  const clearChartButton = document.getElementById('clear-chart');
  let solarChartInstance = null, dropdownCount = 1, selectedTimeSpan = 'year', selectedYear = null;

  // Utility Functions
  const updateDropdownOptions = () => {
    const selectedValues = Array.from(dropdownContainer.querySelectorAll('select'))
      .map(dropdown => dropdown.value).filter(value => value);
    dropdownContainer.querySelectorAll('select').forEach(dropdown => {
      const currentValue = dropdown.value;
      dropdown.querySelectorAll('option').forEach(option => {
        option.style.display = selectedValues.includes(option.value) && option.value !== currentValue ? 'none' : '';
      });
    });
  };

  const populateYearDropdown = (dataArray) => {
    const allYears = new Set(dataArray.flatMap(data => data.data.map(row => new Date(row.date).getFullYear())));
    yearDropdown.innerHTML = `<option value="" disabled selected>Select a year</option><option value="all">Select All</option>`;
    Array.from(allYears).sort().forEach(year => {
      yearDropdown.innerHTML += `<option value="${year}">${year}</option>`;
    });
  };

  const calculateTotalSolarExposure = (data, year) => {
    return data.filter(row => !year || new Date(row.date).getFullYear() === year)
      .reduce((sum, row) => sum + row.solar_exposure, 0);
  };

  const displayRegionDescription = (total) => {
    const descriptionContainer = document.getElementById('region-description');
    if (!descriptionContainer) return;
    const recommendations = [
      { limit: 4000, text: 'Usually not recommended (unless heavily subsidized)' },
      { limit: 6000, text: 'Moderate (check financial payback time)' },
      { limit: 8000, text: 'Good candidate for solar installation' },
      { limit: Infinity, text: 'Excellent location for solar' }
    ];
    const recommendation = recommendations.find(r => total < r.limit).text;
    descriptionContainer.innerHTML = `
      <h3>Region Solar Panel Recommendation</h3>
      <p><strong>Annual Accumulated Solar Exposure:</strong> ${total.toFixed(2)} MJ/m²/year</p>
      <p><strong>Recommendation:</strong> ${recommendation}</p>`;
  };

  const processFileData = (fileData, timeSpan) => {
    const groupedData = {};
    fileData.forEach(row => {
      if (row.solar_exposure !== null) {
        const date = new Date(row.date);
        const key = {
          year: date.getFullYear(),
          '6months': `${date.getFullYear()}-${Math.ceil((date.getMonth() + 1) / 6)}`,
          month: `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}`,
          week: new Date(date.setDate(date.getDate() - date.getDay())).toISOString().split('T')[0],
          day: date.toISOString().split('T')[0]
        }[timeSpan] || date.getFullYear();
        groupedData[key] = groupedData[key] || { total: 0, count: 0 };
        groupedData[key].total += row.solar_exposure;
        groupedData[key].count += 1;
      }
    });
    const labels = Object.keys(groupedData).sort((a, b) => timeSpan === 'month' ? new Date(a) - new Date(b) : a.localeCompare(b, undefined, { numeric: true }));
    const values = labels.map(key => (groupedData[key].total / groupedData[key].count).toFixed(2));
    return { labels, values };
  };

  const renderChart = (chartDataArray, cityNames) => {
    const canvas = document.getElementById('solarChart');
    if (solarChartInstance) solarChartInstance.destroy();
    const combinedLabels = Array.from(new Set(chartDataArray.flatMap(data => data.labels))).sort();
    const datasets = chartDataArray.map((chartData, index) => ({
      label: cityNames[index],
      data: combinedLabels.map(label => chartData.labels.includes(label) ? chartData.values[chartData.labels.indexOf(label)] : null),
      borderColor: `rgba(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255}, 1)`,
      borderWidth: 2,
      fill: false
    }));
    solarChartInstance = new Chart(canvas.getContext('2d'), {
      type: 'line',
      data: { labels: combinedLabels, datasets },
      options: {
        responsive: true,
        plugins: { tooltip: { callbacks: { label: ctx => ctx.raw !== null ? `Value: ${ctx.raw}` : 'No Data' } } },
        scales: { x: { title: { display: true, text: 'Time' } }, y: { title: { display: true, text: 'Average Solar Exposure (MJ/m²)' } } }
      }
    });
  };

  // Event Listeners
  timeSpanButtons.forEach(button => button.addEventListener('click', function () {
    timeSpanButtons.forEach(btn => btn.classList.remove('active'));
    this.classList.add('active');
    selectedTimeSpan = this.getAttribute('data-timespan');
    visualizeButton.click();
  }));

  addCityCheckbox.addEventListener('change', function () {
    if (addCityCheckbox.checked && dropdownCount < 4) {
      dropdownCount++;
      const firstDropdown = document.getElementById('dataset-select-1');
      const newDropdown = document.createElement('div');
      newDropdown.classList.add('dropdown-item', 'mt-4', 'flex', 'items-center');
      newDropdown.setAttribute('id', `dropdown-item-${dropdownCount}`);
      newDropdown.innerHTML = `
        <div class="flex-grow">
          <label for="dataset-select-${dropdownCount}" class="block text-lg font-medium mb-2">Choose another dataset:</label>
          <select id="dataset-select-${dropdownCount}" class="border border-gray-300 rounded-md p-2 w-full">${firstDropdown.innerHTML}</select>
        </div>
        <button class="ml-4 bg-red-500 text-white px-4 py-2 rounded-md delete-city-button" data-dropdown-id="${dropdownCount}">Delete</button>`;
      dropdownContainer.appendChild(newDropdown);
      addCityCheckbox.checked = false;
      if (dropdownCount === 4) addCityCheckbox.disabled = true;
      newDropdown.querySelector('.delete-city-button').addEventListener('click', function () {
        document.getElementById(`dropdown-item-${this.getAttribute('data-dropdown-id')}`).remove();
        dropdownCount--;
        if (dropdownCount < 4) addCityCheckbox.disabled = false;
        updateDropdownOptions();
      });
      newDropdown.querySelector('select').addEventListener('change', updateDropdownOptions);
      updateDropdownOptions();
    }
  });

  loadDatasetButton.addEventListener('click', function () {
    const selectedFileIds = Array.from(dropdownContainer.querySelectorAll('select')).map(dropdown => dropdown.value).filter(Boolean);
    if (!selectedFileIds.length) return alert('Please select at least one dataset to load.');
    Promise.all(selectedFileIds.map(fileId => fetch(`/get-file-data/${fileId}`).then(res => res.ok ? res.json() : Promise.reject(`Failed to fetch file data for ${fileId}`))))
      .then(dataArray => {
        populateYearDropdown(dataArray);
        alert('Dataset loaded successfully! Select a year to visualize.');
      })
      .catch(error => {
        console.error('Error loading dataset:', error);
        alert('Failed to load dataset. Please try again.');
      });
  });

  visualizeButton.addEventListener('click', function () {
    const selectedFileIds = Array.from(dropdownContainer.querySelectorAll('select')).map(dropdown => dropdown.value).filter(Boolean);
    const cityNames = Array.from(dropdownContainer.querySelectorAll('select')).map(dropdown => dropdown.options[dropdown.selectedIndex]?.text).filter(Boolean);
    if (!selectedFileIds.length) return alert('Please select at least one dataset.');
    Promise.all(selectedFileIds.map(fileId => fetch(`/get-file-data/${fileId}`).then(res => res.ok ? res.json() : Promise.reject(`Failed to fetch file data for ${fileId}`))))
      .then(dataArray => {
        const chartDataArray = dataArray.map(data => processFileData(data.data, selectedTimeSpan));
        renderChart(chartDataArray, cityNames);
      })
      .catch(error => console.error('Error fetching file data:', error));
  });

  clearChartButton.addEventListener('click', function () {
    if (solarChartInstance) solarChartInstance.destroy();
    const canvas = document.getElementById('solarChart');
    canvas.getContext('2d').clearRect(0, 0, canvas.width, canvas.height);
    const descriptionContainer = document.getElementById('region-description');
    if (descriptionContainer) descriptionContainer.innerHTML = '<p>Chart cleared. Please select a dataset to visualize.</p>';
  });

  exportPdfButton.addEventListener('click', function () {
    const canvas = document.getElementById('solarChart');
    const pdf = new jsPDF('landscape');
    pdf.setFontSize(18);
    pdf.text('Solar Exposure Analysis', 10, 10);
    pdf.addImage(canvas.toDataURL('image/png', 1.0), 'PNG', 10, 20, 280, 150);
    pdf.save('solar_analysis.pdf');
  });

  exportImageButton.addEventListener('click', function () {
    const canvas = document.getElementById('solarChart');
    canvas.toBlob(blob => {
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'solar_analysis.png';
      link.click();
    }, 'image/png');
  });
});