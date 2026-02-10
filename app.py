import json
import hashlib
import glob
from flask import Flask, render_template, request, redirect, url_for, session, g
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import requests
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Initialize environment variables
load_dotenv()

app = Flask(__name__)

# Uploads
UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
# Format date for display (dd.mm.yyyy)
@app.template_filter('format_date')
def format_date(value):
    if not value:
        return ''
    try:
        if isinstance(value, str):
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"]:
                try:
                    value = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            else:
                return value
        return value.strftime("%d.%m.%Y")
    except Exception:
        return value

# Format time for display (HH:MM)
@app.template_filter('format_time')
def format_time(value):
    if not value:
        return ''
    try:
        if isinstance(value, str):
            for fmt in ["%Y-%m-%d %H:%M:%S", "%H:%M:%S", "%H:%M"]:
                try:
                    value = datetime.strptime(value, fmt)
                    break
                except ValueError:
                    continue
            else:
                return value
        return value.strftime("%H:%M")
    except Exception:
        return value

# Database configuration from .env
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_KANTINE = os.getenv("DB_KANTINE")
SECRET_KEY = os.getenv("SECRET_KEY") or "supersecretkey"

app.secret_key = SECRET_KEY

# Establish database connection
def get_connection_kantine():
    return mysql.connector.connect(
        host = DB_HOST or "localhost",
        user = DB_USER or "your_user_name",
        password = DB_PASSWORD or "your_password",
        database = DB_KANTINE or "your_database_name"
    )

# Create orders table if missing
def create_orders_table():
    try:
        conn = get_connection_kantine()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
                kunde_id INT,
                navn VARCHAR(100),
                mobil VARCHAR(20),
                organisasjonsnummer VARCHAR(50),
                fakturaadresse VARCHAR(255),
                epost VARCHAR(100),
                ressursnummer VARCHAR(50),
                koststed VARCHAR(50),
                ordre_dato DATE,
                ordre_tid TIME,
                hent_dato DATE,
                hent_tid TIME,
                spise_i_kantina VARCHAR(50),
                status_levert BOOLEAN,
                status_fakturert BOOLEAN,
                melding TEXT,
                order_array TEXT,
                sum INT,
                menu_source TEXT
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print("Error creating orders table:", e)

create_orders_table()

# Create menu tables for Canteen and Wakeup
def create_menu_tables():
    try:
        conn = get_connection_kantine()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_kantine (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(100) DEFAULT 'Unknown',
                title VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(8,2) DEFAULT 0,
                image_url VARCHAR(255),
                active BOOLEAN DEFAULT TRUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_wakeup (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(100) DEFAULT 'Unknown',
                title VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(8,2) DEFAULT 0,
                image_url VARCHAR(255),
                active BOOLEAN DEFAULT TRUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                menu_source VARCHAR(50) NOT NULL,
                name VARCHAR(100) NOT NULL,
                sort_order INT DEFAULT 0,
                UNIQUE KEY uniq_menu_category (menu_source, name)
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print("Error creating menu tables:", e)

create_menu_tables()

# Create users table with role flags
def create_user_table():
    try:
        conn = get_connection_kantine()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                navn VARCHAR(255) NOT NULL,
                epost VARCHAR(255) UNIQUE NOT NULL,
                mobil VARCHAR(20),
                organisasjonsnummer VARCHAR(50),
                fakturaadresse VARCHAR(255),
                ressursnummer VARCHAR(50),
                koststed VARCHAR(50),
                rolle_personlig BOOLEAN DEFAULT TRUE,
                rolle_okonomi BOOLEAN DEFAULT FALSE,
                rolle_kjokken BOOLEAN DEFAULT FALSE,
                rolle_admin BOOLEAN DEFAULT FALSE
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print("Error creating users table:", e)

create_user_table()


# Track active endpoint
@app.before_request
def before_request():
    g.current_endpoint = request.endpoint

# Redirect to login or menu
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("main_menu"))

# User login and role assignment
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        epost = request.form.get("email").strip().lower()
        navn = request.form.get("navn").strip()

        conn = get_connection_kantine()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE epost = %s", (epost,))
        user = cursor.fetchone()

        # Create user if they don't exist
        if not user:
            cursor.execute("""
                INSERT INTO users (navn, epost)
                VALUES (%s, %s)
            """, (navn, epost))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE epost = %s", (epost,))
            user = cursor.fetchone()

        cursor.close()
        conn.close()

        # Gather user roles
        roles = []
        if user["rolle_personlig"]: roles.append("personlig")
        if user["rolle_kjokken"]: roles.append("kjokken")
        if user["rolle_okonomi"]: roles.append("okonomi")
        if user["rolle_admin"]: roles.append("admin")

        session["user"] = user
        session["id"] = user["id"]
        session["roles"] = roles

        # Redirect if only one role, otherwise show selection
        if len(roles) == 1:
            session["active_role"] = roles[0]
            return redirect(url_for("main_menu"))
        else:
            return render_template("velg_rolle.html", roles=roles, navn=user["navn"])

    return render_template("login.html")

# Role selection page
@app.route("/velg-rolle", methods=["GET", "POST"])
def velg_rolle():
    if "user" not in session:
        return redirect(url_for("login"))

    roles = session.get("roles", [])
    navn = session["user"]["navn"]

    if request.method == "POST":
        valgt_rolle = request.form.get("rolle")
        if valgt_rolle in roles:
            session["active_role"] = valgt_rolle
            return redirect(url_for("main_menu"))

    return render_template("velg_rolle.html", roles=roles, navn=navn)

# Display main menu based on active role
@app.route("/main")
def main_menu():
    role = session.get("active_role")
    if not role:
        return redirect(url_for("login"))
    return render_template("navigation/main_menu.html", role=role)

# Admin: Manage users and roles
@app.route("/admin-brukere", methods=["GET", "POST"])
def admin_brukere():
    role = session.get("active_role")
    if role != "admin":
        return redirect(url_for("login"))
    
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    if request.method == "POST":
        action = request.form.get("action")
        user_id = request.form.get("id")

        if action == "save":
            cursor.execute("""
                UPDATE users
                SET rolle_personlig=%s, rolle_okonomi=%s, rolle_kjokken=%s, rolle_admin=%s
                WHERE id=%s
            """, ('rolle_personlig' in request.form, 'rolle_okonomi' in request.form, 
                  'rolle_kjokken' in request.form, 'rolle_admin' in request.form, user_id))
        elif action == "delete":
            cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
        conn.commit()

    cursor.execute("SELECT * FROM users ORDER BY navn ASC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin/admin_brukere.html", users=users)

# Switch active role
@app.route("/sett_rolle", methods=["POST"])
def sett_rolle():
    session["active_role"] = request.form.get("rolle")
    return redirect(url_for("main_menu"))


# --- ORDERS SECTION ---

# User view: List personal orders
@app.route("/mine-bestillinger")
def mine_bestillinger():
    user = session.get("user")
    role = session.get("active_role")
    if not user or not role:
        return redirect(url_for("login"))

    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE kunde_id = %s ORDER BY id DESC", (user["id"],))
    order_info = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("bestillinger.html", order_info=order_info, role=role)

# Kitchen view: List pending orders
@app.route("/aktive-bestillinger-i-kantinen")
def aktive_bestillinger_i_kantinen():
    role = session.get("active_role")
    if role != "kjokken": return redirect(url_for("login"))
    
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE status_levert = FALSE OR status_levert IS NULL ORDER BY id ASC")
    order_info = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("bestillinger.html", order_info=order_info, role=role)

# Kitchen action: Mark order as delivered
@app.route("/sett-levert/<int:order_id>", methods=["POST"])
def sett_levert(order_id):
    if session.get("active_role") != "kjokken": return redirect(url_for("login"))
    
    conn = get_connection_kantine()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status_levert = TRUE WHERE id = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("aktive_bestillinger_i_kantinen"))

# Economy view: List delivered but not yet invoiced orders
@app.route("/ferdige-bestillinger")
def ferdige_bestillinger():
    if session.get("active_role") != "okonomi": return redirect(url_for("login"))
    
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM orders 
        WHERE status_levert = TRUE AND (status_fakturert = FALSE OR status_fakturert IS NULL)
        ORDER BY hent_dato DESC
    """)
    order_info = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("bestillinger.html", order_info=order_info, role="okonomi")

# Economy action: Mark order as invoiced
@app.route("/sett-fakturert/<int:order_id>", methods=["POST"])
def sett_fakturert(order_id):
    if session.get("active_role") != "okonomi": return redirect(url_for("login"))
    
    conn = get_connection_kantine()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status_fakturert = TRUE WHERE id = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("ferdige_bestillinger"))

# View single order receipt
@app.route("/vis-bestilling/<int:order_id>")
def vis_bestilling(order_id):
    if "user" not in session: return redirect(url_for("login"))

    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order_info = cursor.fetchone()
    cursor.close()
    conn.close()

    if not order_info:
        return "Order not found", 404

    return render_template("kvittering.html", 
                           order_info=order_info, 
                           order_array=json.loads(order_info["order_array"]))

# Admin view: See all orders and users
@app.route('/admin-bestillinger', methods=['GET'])
def admin_bestillinger():
    if session.get("active_role") != "admin": return redirect(url_for("login"))
    
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    order_info = cursor.fetchall()
    cursor.execute("SELECT * FROM users")
    users_info = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("bestillinger.html", order_info=order_info, users_info=users_info, role="admin")

# Admin action: Delete an order
@app.route('/slett-bestilling/<int:order_id>', methods=["POST"])
def slett_bestilling(order_id):
    if session.get("active_role") != "admin": return redirect(url_for("login"))
    
    conn = get_connection_kantine()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_bestillinger"))


# Helper: Map menu source to table name
def _table_for(menu_source):
    return "menu_kantine" if menu_source == "Kantina" else "menu_wakeup" if menu_source == "WAKEUP" else None

# Helper: Fetch active menu items
def get_menu_items(menu_source):
    table = _table_for(menu_source)
    if not table: return []
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table} WHERE active=TRUE ORDER BY title ASC")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return items

# Helper: Fetch all menu items (including inactive)
def get_all_menu_items(menu_source):
    table = _table_for(menu_source)
    if not table: return []
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table} ORDER BY title ASC")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return items


def build_categories_with_order(menu_source, items):
    categories = {}
    category_first_id = {}
    for item in items:
        category = item["category"] or "Unknown"
        categories.setdefault(category, []).append(item)
        if category not in category_first_id or item["id"] < category_first_id[category]:
            category_first_id[category] = item["id"]

    ordered = {}
    category_list = get_menu_categories(menu_source)
    for name in category_list:
        if name in categories:
            ordered[name] = categories[name]

    remaining = [name for name in categories.keys() if name not in ordered]
    for name in sorted(remaining, key=lambda n: category_first_id.get(n, 0)):
        ordered[name] = categories[name]

    return ordered

# Helper: Fetch distinct categories
def get_menu_categories(menu_source):
    table = _table_for(menu_source)
    if not table:
        return []

    conn = get_connection_kantine()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name FROM menu_categories
        WHERE menu_source = %s
        ORDER BY sort_order ASC, name ASC
    """, (menu_source,))
    rows = cursor.fetchall()
    category_list = [row[0] for row in rows if row[0]]

    if not category_list:
        cursor.execute(f"SELECT DISTINCT category FROM {table} ORDER BY category ASC")
        rows = cursor.fetchall()
        category_list = [row[0] for row in rows if row[0]]

    cursor.close()
    conn.close()
    return category_list


def sync_menu_categories(menu_source):
    table = _table_for(menu_source)
    if not table:
        return

    conn = get_connection_kantine()
    cursor = conn.cursor()

    cursor.execute(f"SELECT DISTINCT category FROM {table}")
    item_categories = {row[0] for row in cursor.fetchall() if row[0]}

    cursor.execute("SELECT name FROM menu_categories WHERE menu_source = %s", (menu_source,))
    existing = {row[0] for row in cursor.fetchall()}

    missing = [c for c in item_categories if c not in existing]
    if missing:
        cursor.execute(
            "SELECT COALESCE(MAX(sort_order), 0) FROM menu_categories WHERE menu_source = %s",
            (menu_source,),
        )
        max_sort = cursor.fetchone()[0] or 0
        for i, name in enumerate(sorted(missing), start=1):
            cursor.execute(
                "INSERT IGNORE INTO menu_categories (menu_source, name, sort_order) VALUES (%s, %s, %s)",
                (menu_source, name, max_sort + i),
            )

    conn.commit()
    cursor.close()
    conn.close()

def _parse_price(value):
    if value is None:
        return 0
    text = str(value).strip().lower().replace("kr", "").replace(",", ".")
    text = "".join(ch for ch in text if ch.isdigit() or ch == ".")
    try:
        return float(text)
    except ValueError:
        return 0


def _allowed_image(filename):
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_IMAGE_EXTENSIONS


def _save_menu_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    if not _allowed_image(filename):
        return None

    ext = os.path.splitext(filename)[1].lower()
    if ext == ".jpeg":
        ext = ".jpg"

    data = file_storage.read()
    if not data:
        return None

    file_hash = hashlib.sha256(data).hexdigest()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    existing = glob.glob(os.path.join(UPLOAD_FOLDER, f"{file_hash}.*"))
    if existing:
        existing_name = os.path.basename(existing[0])
        return f"/static/uploads/{existing_name}"

    target_name = f"{file_hash}{ext}"
    target_path = os.path.join(UPLOAD_FOLDER, target_name)
    with open(target_path, "wb") as f:
        f.write(data)

    return f"/static/uploads/{target_name}"


# Kitchen: Menu editor
@app.route("/meny-editor/<menu_source>", methods=["GET", "POST"])
def meny_editor(menu_source):
    if session.get("active_role") != "kjokken":
        return redirect(url_for("login"))

    table = _table_for(menu_source)
    if not table:
        return "Ugyldig menyvalg", 400

    if request.method == "POST":
        conn = get_connection_kantine()
        cursor = conn.cursor()

        # Update category order and create/rename categories
        raw_order = request.form.getlist("category_order")
        new_categories = request.form.getlist("new_category")
        category_names = request.form.getlist("category_name")

        order_list = []
        seen = set()
        for name in raw_order + category_names + new_categories:
            clean = (name or "").strip()
            if not clean or clean in seen:
                continue
            seen.add(clean)
            order_list.append(clean)

        if order_list:
            for idx, name in enumerate(order_list):
                cursor.execute(
                    """
                    INSERT INTO menu_categories (menu_source, name, sort_order)
                    VALUES (%s, %s, %s)
                    ON DUPLICATE KEY UPDATE sort_order = VALUES(sort_order)
                    """,
                    (menu_source, name, idx),
                )

        # Handle deleted categories
        for name in order_list:
            if request.form.get(f"category_deleted_{name}") == "1":
                cursor.execute(
                    "DELETE FROM menu_categories WHERE menu_source = %s AND name = %s",
                    (menu_source, name),
                )

        # Update or delete existing items
        for item_id in request.form.getlist("item_id"):
            delete_flag = request.form.get(f"delete_{item_id}") == "1"
            if delete_flag:
                cursor.execute(f"DELETE FROM {table} WHERE id = %s", (item_id,))
                continue

            title = request.form.get(f"title_{item_id}", "").strip()
            description = request.form.get(f"description_{item_id}", "").strip()
            category = request.form.get(f"category_{item_id}", "").strip() or "Unknown"
            price = _parse_price(request.form.get(f"price_{item_id}"))
            image_url = request.form.get(f"image_url_{item_id}", "").strip()
            uploaded_url = _save_menu_image(request.files.get(f"image_file_{item_id}"))
            if uploaded_url:
                image_url = uploaded_url
            active = request.form.get(f"active_{item_id}") == "on"

            cursor.execute(
                f"""
                UPDATE {table}
                SET category=%s, title=%s, description=%s, price=%s, image_url=%s, active=%s
                WHERE id=%s
                """,
                (category, title, description, price, image_url, active, item_id),
            )

        # Insert new items
        for idx in request.form.getlist("new_item_index"):
            title = request.form.get(f"new_title_{idx}", "").strip()
            if not title:
                continue
            description = request.form.get(f"new_description_{idx}", "").strip()
            category = request.form.get(f"new_category_{idx}", "").strip() or "Unknown"
            price = _parse_price(request.form.get(f"new_price_{idx}"))
            image_url = request.form.get(f"new_image_url_{idx}", "").strip()
            uploaded_url = _save_menu_image(request.files.get(f"new_image_file_{idx}"))
            if uploaded_url:
                image_url = uploaded_url
            active = request.form.get(f"new_active_{idx}") == "on"

            cursor.execute(
                f"""
                INSERT INTO {table} (category, title, description, price, image_url, active)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (category, title, description, price, image_url, active),
            )

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for("meny_editor", menu_source=menu_source))

    sync_menu_categories(menu_source)

    items = get_all_menu_items(menu_source)
    ordered_categories = build_categories_with_order(menu_source, items)
    category_list = list(ordered_categories.keys())

    return render_template(
        "kjokken/meny_editor.html",
        categories=ordered_categories,
        menu_source=menu_source,
        category_list=category_list,
    )

# Page: Order from Canteen
@app.route("/bestille-fra-kantina")
def bestille_fra_kantina():
    if "user" not in session: return redirect(url_for("login"))
    session["menu_source"] = "Kantina"
    items = get_menu_items("Kantina")
    categories = build_categories_with_order("Kantina", items)
    return render_template("personlig/bestille_mat.html", 
                           categories=categories, 
                           menu_source="Kantina", 
                           user=session.get("user"))

# Page: Order from WAKEUP
@app.route("/bestille-fra-WAKEUP")
def bestille_fra_WAKEUP():
    if "user" not in session: return redirect(url_for("login"))
    session["menu_source"] = "WAKEUP"
    items = get_menu_items("WAKEUP")
    categories = build_categories_with_order("WAKEUP", items)
    return render_template("personlig/bestille_mat.html",
                           categories=categories,
                           menu_source="WAKEUP",
                           user=session.get("user"))

# Process order submission
@app.route('/submit', methods=['POST'])
def submit():
    user_id = session.get("id")
    menu_source = session.get("menu_source")
    menu_items = get_menu_items(menu_source)

    # Metadata
    ordre_dato = datetime.now()
    ordre_tid = datetime.now().strftime("%H:%M")
    hent_dato = request.form.get('hent_dato')
    hent_tid = request.form.get('hent_tid')
    melding = request.form.get('melding')

    # Calculate total and build item list
    order_array = {}
    ordresum = 0
    for key, amount in request.form.items():
        if key.startswith("item_") and amount and int(amount) > 0:
            for item in menu_items:
                if item['id'] == int(key[5:]):
                    price = int(item['price'])
                    item_sum = price * int(amount)
                    ordresum += item_sum
                    order_array[item["title"]] = {"antall": int(amount), "pris": price, "sum": item_sum}

    # Handle Canteen-specific logic (Company details)
    if menu_source == "Kantina":
        navn = request.form.get('navn')
        mobil = request.form.get('mobil')
        org_nr = request.form.get('organisasjonsnummer')
        f_adr = request.form.get('fakturaadresse')
        epost = request.form.get('epost')
        res_nr = request.form.get('ressursnummer')
        koststed = request.form.get('koststed')
        if koststed == "other":
            koststed = request.form.get("koststedCustom", "").strip() or "Unknown"

        # Update user profile
        conn = get_connection_kantine()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET navn=%s, epost=%s, mobil=%s, organisasjonsnummer=%s, 
                       fakturaadresse=%s, ressursnummer=%s, koststed=%s WHERE id=%s
        """, (navn, epost, mobil, org_nr, f_adr, res_nr, koststed, user_id))
        conn.commit()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        updated_user = cursor.fetchone()
        cursor.close()
        conn.close()

        session["user"] = updated_user


        # Dining preference
        spise_i_kantina_true = 'spise_i_kantina' in request.form
        antall_personer = request.form.get('antall_personer', '').strip()
        if antall_personer.isdigit():
            antall_personer = int(antall_personer)

            if antall_personer >= 2:
                spise_i_kantina = f"{antall_personer} personer" if spise_i_kantina_true else "Nei"
            elif antall_personer == 1:
                spise_i_kantina = f"{antall_personer} person" if spise_i_kantina_true else "Nei"
        else:
            antall_personer = 0
        if spise_i_kantina == None:
            spise_i_kantina = "Nei"

        # Save order
        try:
            conn = get_connection_kantine()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                INSERT INTO orders (kunde_id, navn, mobil, organisasjonsnummer, fakturaadresse, epost, ressursnummer, 
                koststed, ordre_dato, ordre_tid, hent_dato, hent_tid, spise_i_kantina, melding, order_array, sum, menu_source)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (user_id, navn, mobil, org_nr, f_adr, epost, res_nr, koststed, ordre_dato, ordre_tid, hent_dato, 
                  hent_tid, spise_i_kantina, melding, json.dumps(order_array), ordresum, menu_source))
            conn.commit()
            order_id = cursor.lastrowid
            cursor.close()
            conn.close()
        except Error as e: return f"Database Error: {e}"

    # Handle Wakeup-specific logic
    elif menu_source == "WAKEUP":
        navn, epost, mobil = request.form.get('navn'), request.form.get('epost'), request.form.get('mobil')
        conn = get_connection_kantine()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO orders (kunde_id, navn, epost, mobil, ordre_dato, ordre_tid, 
                       hent_dato, hent_tid, order_array, sum, menu_source, spise_i_kantina)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (user_id, navn, epost, mobil, ordre_dato, ordre_tid, 
              hent_dato, hent_tid, json.dumps(order_array), ordresum, menu_source, "Nei"))
        conn.commit()
        order_id = cursor.lastrowid
        cursor.close()
        conn.close()

    return redirect(url_for('vis_bestilling', order_id=order_id, menu_source=menu_source))

if __name__ == '__main__':
    app.run(debug=True)
