# Kuben Cafeteria – Teacher Page

This project is a practice assignment from Kuben VGS. The goal is to build a cafeteria web app
for teachers with ordering, kitchen/admin views, and menu editing.

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
2. Create a `.env` file in the project root with your settings:

3. The app will auto-create required tables on startup.

If you prefer, you can also set the values directly in `app.py` in `get_connection_kantine()`.

---

## Running the Project

After installing dependencies and configuring the database, you can start the server with:

    python app.py

Then open your browser and visit:

    http://127.0.0.1:5000/

---

## Notes / Tips

- On first run, the app creates missing tables automatically.
- If uploads don’t show, ensure `static/uploads/` exists and is writable.
- To get admin access, set `rolle_admin` to `1` for your user in the `users` table (e.g. via a SQL update):

```sql
UPDATE users
SET rolle_admin = 1
WHERE epost = 'your@email.com';
```
