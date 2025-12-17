# Kuben Cafeteria – Teacher Page

This project is a practice assignment from Kuben VGS, where the task was to create a new webpage
for the school cafeteria, specifically designed for teachers.

---

## How to Run the Project

### 1. Install Dependencies

After opening the project folder in your code editor, install the required Python dependencies.

It is recommended (but optional) to use a virtual environment so you don’t clutter your global Python installation.

Example:

    python -m venv venv
    source venv/bin/activate        # macOS/Linux
    venv\Scripts\activate           # Windows

Then install the dependencies:

    pip install -r requirements.txt

If you don’t have the `requirements.txt`, install manually:

    pip install flask mysql-connector-python python-dotenv requests

---

## Database Setup (MariaDB / MySQL)

To run the webpage, you must use a MySQL-based database (such as MariaDB).

1. Create a new database in MariaDB/MySQL.  
2. Fill out your database connection settings inside **app.py**:

Find this inside [`app.py`](/app.py):

    def get_connection_kantine():
    return mysql.connector.connect(
        host=DB_HOST or "localhost",
        user=DB_USER or "your_user_name",
        password=DB_PASSWORD or "your_password",
        database=DB_KANTINE or "your_database_name"
    )

Make sure these match your local database configuration.

---

## Running the Project

After installing dependencies and configuring the database, you can start the server with:

    python app.py

Then open your browser and visit:

    http://127.0.0.1:5000/
