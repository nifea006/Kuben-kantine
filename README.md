# Kuben Cafeteria – Teacher Page

This project is a practice assignment from Kuben VGS. The goal is to build a cafeteria web app
for teachers with ordering, kitchen/admin views, and menu editing.

---

## Requirements

- [python 3.xx](https://www.python.org/downloads/)
- MySQL-compatible database such as [MySQL](https://www.mysql.com/downloads/) or [MariaDB](https://mariadb.org/download/?t=mariadb&p=mariadb&r=12.2.2&os=windows&cpu=x86_64&pkg=msi&mirror=dotsrc)

## How to Run the Project

### 1. Install Dependencies

After opening the project folder in your code editor, install the required Python dependencies.

It is recommended (but optional) to use a virtual environment so you don’t clutter your global Python installation.

Example:

```bash
python -m venv venv
venv\Scripts\activate           # Windows
source venv/bin/activate        # macOS/Linux
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

If you don’t have the `requirements.txt`, install manually:

```bash
pip install flask mysql-connector-python python-dotenv requests
```

---

## Database Setup (MariaDB / MySQL)

To run the webpage, you must use a MySQL-compatible database such as MySQL or MariaDB.

1. Create a new database in MariaDB/MySQL.  
2. Open [`app.py`](/app.py#L69) and find `get_connection_kantine()`.
3. Replace the placeholder values with your own database settings:

    ```python
    def get_connection_kantine():
        return mysql.connector.connect(
            host="localhost",
            user="your_user_name",
            password="your_password",   
            database="your_database_name"
        )
    ```

4. Save the file and start the app. The required tables will be created automatically on first startup.

---

## Running the Project

After installing dependencies and configuring the database, you can start the server with:

```bash
python app.py
```

Then open your browser and visit:

[`http://127.0.0.1:5000/`](/http://127.0.0.1:5000/)

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

## Links

The food images:

- [Pexels](https://www.pexels.com/)

The icons:

- [Heroicons](https://heroicons.com/)
- [SVG Repo](https://www.svgrepo.com/)
- [Flaticon](https://www.flaticon.com/)
