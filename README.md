# SolarScope: Solar Exposure Data Sharing & Analysis Platform

## Purpose of the Application

**SolarScope** is a web-based system that allows users to upload, share, and analyze solar exposure data. Users can choose to keep their data private, share it with specific individuals, or make it publicly accessible to the community.

Once your data is uploaded, SolarScope makes it easy to explore and understand using visual tools. You can:

- Compare solar data across places and over time (like monthly, yearly, or by season)

- See summaries of the data like averages, highest and lowest values

- Spot unusual patterns or problems

- Estimate how much solar energy your area could produce

You can also download your data in CSV format or save charts as images or PDFs for reports.

SolarScope helps users make better decisions about solar panels, energy use, and planning based on real sunlight data.

## MasterGroup62

| UWA ID   | Name                    | GitHub Username |
| -------- | ----------------------- | --------------- |
| 23927347 | Nanxi Rao               | flappyfishhh    |
| 24486055 | Ethan Zhang             | EthanZ-SH       |
| 24284623 | Joshua Wang             | JoJohowl        |
| 24289358 | Chamodhi Withana Gamage | chamodhii       |

## Launching the Application (With Test Data)

### Step 1: Clone the Repository

```bash
git clone https://github.com/flappyfishhh/cits5505-masters62.git
```

### Step 2: Navigate to the Project Directory

```bash
cd cits5505-masters62/
```

### Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

### Step 4: Activate the Virtual Environment

- On Windows:

```bash
venv\Scripts\activate
```

- On macOS/Linux:

```bash
source venv/bin/activate
```

### Step 5: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 6: Initialize the Database

Run database migrations to set up the database schema:

```bash
flask db upgrade
```

### Step7: Insert Test Data

Run the provided `seed_data.py` script to populate the database with test users, files, and uploads.

```bash
python seed_data.py
```

### Step 8: Run the project

```bash
flask run
```

The app will be available at 'http://127.0.0.1:5000/'

## Running Tests

This project includes both unit tests and end-to-end tests using **Pytest** and **Selenium**.

If you plan to run Selenium tests, ensure you have the appropriate browser driver installed and in your system PATH:

- For Chrome: [Download ChromeDriver](https://sites.google.com/chromium.org/driver/)
- For Firefox: [Download GeckoDriver](https://github.com/mozilla/geckodriver/releases)

### Running the Tests

To run all tests:

```bash
pytest
```

### Test Structure

This project also includes a `pytest.ini` configuration file to manage test discovery and reporting.

- `tests/` – main test directory
  - `conftest.py` – shared fixtures for both unit and Selenium tests
  - `selenium/` – end-to-end browser tests
  - `unit/` – unit tests for backend logic
  - `assets/` – test CSV files used for seeding and visualization tests
