# [Project Name]

## Purpose of the Application

[a description of the purpose of the application, explaining its design and use]

## MasterGroup62

| UWA ID   | Name                    | GitHub Username |
| -------- | ----------------------- | --------------- |
| 23927347 | Nanxi Rao               | flappyfishhh    |
| 24486055 | Ethan Zhang             | EthanZ-SH       |
| 24284623 | Joshua Wang             | JoJohowl        |
| 24289358 | Chamodhi Withana Gamage | chamodhii       |

## Launching the Application

```bash
# Step 1: Clone the repository
git clone https://github.com/flappyfishhh/cits5505-masters62.git

# Step 2: Navigate to the project directory
cd cits5505-masters62/

# Step 3: Create a virtual environment
python -m venv venv

# Step 4: Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Step 5: Install Python dependencies
pip install -r requirements.txt

# Step 6: Apply database migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Step 7: Run the project
flask run
