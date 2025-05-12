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

## Launching the Application

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

### (Optional) Step7: Seed the Database with Sample Data

Use the provided `seed_data.py` script to populate the database with sample users, files, and uploads.

```bash
python seed_data.py
```

### Step 8: Start the Application

```bash
flask run
```

Visit the app at: `http://127.0.0.1:5000/`

## Running Tests

This project includes both unit and end-to-end (E2E) tests using **Pytest** and **Selenium**.

Our Selenium tests use `webdriver_manager.chrome`, which automatically downloads the correct ChromeDriver when you run `pytest`.
If you're using a different browser or prefer manual setup, ensure the correct driver is installed and in your system PATH:

- For Chrome: [Download ChromeDriver](https://sites.google.com/chromium.org/driver/)
- For Firefox: [Download GeckoDriver](https://github.com/mozilla/geckodriver/releases)

### Run All Tests

```bash
pytest
```

### Test Structure

This project also includes a `pytest.ini` configuration file to manage test discovery and reporting.

The test suite is organized as follows:

- `tests/`
  - `conftest.py` – Shared fixtures for unit and Selenium tests
  - `selenium/` – End-to-end browser-based tests
  - `unit/` – Unit tests for backend functionality
  - `assets/` – CSV test data for file upload & visualization
  - `reset_dev_db.sh` - Script to reset app.db and migrations (for dev use)

We use a **daemon thread** to run the test server during Selenium testing. This means it shuts down automatically when tests finish.
If something goes wrong and your development database ends up in a broken state, run:

```bash
./tests/reset_dev_db.sh
```

This will reset the database and reapply all migrations for a clean development setup.
