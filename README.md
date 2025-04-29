# Solar Exposure Data Sharing & Analysis Platform

## Purpose of the Application

Our project is a web-based system that allows users to upload, share, and analyze solar exposure data. Users can choose to keep their data private, share it with specific individuals, or make it publicly accessible to the community.

Once uploaded, the system provides intuitive visualization tools to help users make sense of their data. It supports insightful comparisons across regions or time periods, generates trend reports (such as seasonal or year-over-year changes), and can detect anomalies or outliers that may signal issues like equipment failure or unusual weather patterns.

The platform also offers smart recommendations, including estimates of potential solar energy generation based on local exposure levels.

To support collaboration and reporting, users can export processed data in CSV, JSON, or Excel formats, and download visualizations as high-quality images or PDFs.

## MasterGroup62

| UWA ID   | Name                    | GitHub Username |
| -------- | ----------------------- | --------------- |
| 23927347 | Nanxi Rao               | flappyfishhh    |
| 24486055 | Ethan Zhang             | EthanZ-SH       |
| 24284623 | Joshua Wang             | JoJohowl        |
| 24289358 | Chamodhi Withana Gamage | chamodhii       |

## Launching the Application (With Test Data)

Step 1: Clone the Repository

```bash
git clone https://github.com/flappyfishhh/cits5505-masters62.git
```

Step 2: Navigate to the Project Directory

```bash
cd cits5505-masters62/
```

Step 3: Create a Virtual Environment

```bash
python -m venv venv
```

Step 4: Activate the Virtual Environment

- On Windows:

```bash
venv\Scripts\activate
```

- On macOS/Linux:

```bash
source venv/bin/activate
```

Step 5: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Step 6: Initialize the Database
Run database migrations to set up the database schema:

```bash
flask db upgrade
```

Step7: Insert Test Data
run the provided `seed_data.py` script to automatically populate the database with test users, files, and uploads.

```bash
python seed_data.py
```

Step 8: Run the project

```bash
flask run
```

The app will be available at 'http://127.0.0.1:5000/'
