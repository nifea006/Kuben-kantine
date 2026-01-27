import json
from flask import Flask, render_template, request, redirect, url_for, session, g
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Format date
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

# Format time
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

# Read environment variables
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_KANTINE = os.getenv("DB_KANTINE")
SECRET_KEY = os.getenv("SECRET_KEY") or "supersecretkey"

app.secret_key = SECRET_KEY

# ----- Fill out your database connection settings ----- #

# Database connection
def get_connection_kantine():
    return mysql.connector.connect(
        host = DB_HOST or "localhost",
        user = DB_USER or "your_user_name",
        password = DB_PASSWORD or "your_password",
        database = DB_KANTINE or "your_database_name"
    )

# Create user table if not exists
def create_orders_table():
    try:
        conn = get_connection_kantine()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INT AUTO_INCREMENT PRIMARY KEY,
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
                ordre TEXT,
                sum INT,
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print("Feil ved oppretting av orders-tabell:", e)

create_orders_table()

def create_menu_tables():
    try:
        conn = get_connection_kantine()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_kantine (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(100) DEFAULT 'Ukjent',
                title VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(8,2) DEFAULT 0,
                image_url VARCHAR(255),
                position INT DEFAULT 0,
                active BOOLEAN DEFAULT TRUE
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS menu_wakeup (
                id INT AUTO_INCREMENT PRIMARY KEY,
                category VARCHAR(100) DEFAULT 'Ukjent',
                title VARCHAR(255) NOT NULL,
                description TEXT,
                price DECIMAL(8,2) DEFAULT 0,
                image_url VARCHAR(255),
                position INT DEFAULT 0,
                active BOOLEAN DEFAULT TRUE
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print("Feil ved oppretting av menu-tabeller:", e)

create_menu_tables()

# Create user table if not exists
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
                orgnummer VARCHAR(50),
                fakturaadresse VARCHAR(255),
                ressursnummer VARCHAR(50),
                kosted VARCHAR(50),
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
        print("Feil ved oppretting av users-tabell:", e)

create_user_table()


# Routes
@app.before_request
def before_request():
    g.current_endpoint = request.endpoint

@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("main_menu"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email").strip().lower()
        navn = request.form.get("navn").strip()

        conn = get_connection_kantine()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE epost = %s", (email,))
        user = cursor.fetchone()

        if not user:
            cursor.execute("""
                INSERT INTO users (navn, epost)
                VALUES (%s, %s)
            """, (navn, email))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE epost = %s", (email,))
            user = cursor.fetchone()

        cursor.close()
        conn.close()

        roles = []
        if user["rolle_personlig"]:
            roles.append("personlig")
        if user["rolle_kjokken"]:
            roles.append("kjokken")
        if user["rolle_okonomi"]:
            roles.append("okonomi")
        if user["rolle_admin"]:
            roles.append("admin")

        session["user"] = user
        session["roles"] = roles

        if len(roles) == 1:
            session["active_role"] = roles[0]
            return redirect(url_for("main_menu"))
        else:
            return render_template("velg_rolle.html", roles=roles, navn=user["navn"])

    return render_template("login.html")

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
        else:
            return render_template("velg_rolle.html", roles=roles, navn=navn, error="Ugyldig rolle valgt.")

    return render_template("velg_rolle.html", roles=roles, navn=navn)

@app.route("/main")
def main_menu():
    role = session.get("active_role")
    if not role:
        return redirect(url_for("login"))

    return render_template("main_menu.html", role=role)

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
        new_id = request.form.get("new_id")

        if action == "save":
            rolle_personlig = 'rolle_personlig' in request.form
            rolle_okonomi = 'rolle_okonomi' in request.form
            rolle_kjokken = 'rolle_kjokken' in request.form
            rolle_admin = 'rolle_admin' in request.form

            cursor.execute("""
                UPDATE users
                SET rolle_personlig=%s, rolle_okonomi=%s, rolle_kjokken=%s, rolle_admin=%s
                WHERE id=%s
            """, (rolle_personlig, rolle_okonomi, rolle_kjokken, rolle_admin, user_id))

            if new_id and new_id != user_id:
                cursor.execute("UPDATE users SET id=%s WHERE id=%s", (new_id, user_id))

        elif action == "delete":
            cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))

        conn.commit()

    cursor.execute("SELECT * FROM users ORDER BY navn ASC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin/admin_brukere.html", users=users)

@app.route("/sett_rolle", methods=["POST"])
def sett_rolle():
    role = request.form.get("rolle")
    session["active_role"] = role
    return redirect(url_for("main_menu"))


@app.route("/mine-bestillinger")
def mine_bestillinger():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    role = session.get("active_role")
    if not role:
        return redirect(url_for("login"))

    epost = user["epost"]

    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE epost = %s ORDER BY id DESC", (epost,))
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("bestillinger.html", orders=orders, role=role)

@app.route("/aktive-bestillinger-i-kantinen")
def aktive_bestillinger_i_kantinen():
    role = session.get("active_role")
    if role != "kjokken":
        return redirect(url_for("login"))
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM orders
        WHERE status_levert = FALSE
        ORDER BY id ASC
    """)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("bestillinger.html", orders=orders, role=role)

@app.route("/sett-levert/<int:order_id>", methods=["POST"])
def sett_levert(order_id):
    role = session.get("active_role")
    if role != "kjokken":
        return redirect(url_for("login"))
    conn = get_connection_kantine()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status_levert = TRUE WHERE id = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("aktive_bestillinger_i_kantinen"))


@app.route("/ferdige-bestillinger")
def ferdige_bestillinger():
    role = session.get("active_role")
    if role != "okonomi":
        return redirect(url_for("login"))
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM orders
        WHERE status_levert = TRUE AND status_fakturert = FALSE
        ORDER BY hent_dato DESC
    """)
    orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("bestillinger.html", orders=orders, role=role)

@app.route("/sett-fakturert/<int:order_id>", methods=["POST"])
def sett_fakturert(order_id):
    role = session.get("active_role")
    if role != "okonomi":
        return redirect(url_for("login"))
    conn = get_connection_kantine()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status_fakturert = TRUE WHERE id = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("ferdige_bestillinger"))


@app.route("/vis-bestilling/<int:order_id>")
def vis_bestilling(order_id):
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    cursor.close()
    conn.close()

    if not order:
        return "Bestilling ikke funnet"

    ordre_dict = json.loads(order["ordre"]) if order["ordre"] else {}
    total = sum(item["sum"] for item in ordre_dict.values())

    order_info = {
        **order,
        "ordre": ordre_dict,
        "sum": total
    }
    return render_template("kvittering.html", order=order_info)

@app.route('/admin-bestillinger', methods=['GET'])
def admin_bestillinger():
    role = session.get("active_role")
    if role != "admin":
        return redirect(url_for("login"))
    conn_kantine = get_connection_kantine()
    cursor_kantine = conn_kantine.cursor(dictionary=True)
    cursor_kantine.execute("SELECT * FROM orders ORDER BY id DESC")
    orders = cursor_kantine.fetchall()
    cursor_kantine.close()
    conn_kantine.close()

    conn_users = get_connection_kantine()
    cursor_users = conn_users.cursor(dictionary=True)
    cursor_users.execute("SELECT id, epost FROM users")
    users = cursor_users.fetchall()
    cursor_users.close()
    conn_users.close()

    user_map = {u["epost"]: u["id"] for u in users}
    
    for o in orders:
        try:
            ordre_dict = json.loads(o["ordre"]) if o["ordre"] else {}
            o["sum"] = sum(item["sum"] for item in ordre_dict.values())
        except Exception:
            o["sum"] = 0
        o["user_id"] = user_map.get(o["epost"], "Ukjent")

    return render_template("bestillinger.html", orders=orders)

# @app.route("/rediger-meny/<menu_name>")
# def rediger_meny(menu_name):
#     role = session.get("active_role")
#     if role != "kjokken":
#         return redirect(url_for("login"))
#     if menu_name not in ("kantine", "wakeup"):
#         return "Ukjent meny", 404

#     items = get_all_menu_items(menu_name)
#     categories = {}
#     for it in items:
#         categories.setdefault(it["category"] or "Ukjent", []).append(it)

#     return render_template("kjokken/rediger_meny.html", categories=categories, menu_name=menu_name)

def _table_for(menu_name):
    if menu_name == "kantine":
        return "menu_kantine"
    if menu_name == "wakeup":
        return "menu_wakeup"
    return None

def get_menu_items(menu_name="kantine"):
    table = _table_for(menu_name)
    if not table:
        return []
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table} WHERE active=TRUE ORDER BY position ASC, id ASC")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return items

# def get_all_menu_items(menu_name="kantine"):
    table = _table_for(menu_name)
    if not table:
        return []
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table} ORDER BY category ASC, position ASC")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return items

# @app.route("/rediger-meny/mass-save", methods=["POST"])
# def rediger_meny_mass_save():
    role = session.get("active_role")
    if role != "kjokken":
        return {"ok": False, "error": "Unauthorized"}

    data = request.get_json()
    menu = data.get("menu", "kantine")
    changes = data.get("changes", {})
    new_items = data.get("newItems", {})
    deleted_items = data.get("deletedItems", [])
    positions = data.get("positions", {})

    table = _table_for(menu)
    if not table:
        return {"ok": False, "error": "Invalid menu"}

    conn = get_connection_kantine()
    cursor = conn.cursor()

    try:
        # Update existing items
        allowed_fields = {"title", "description", "price"}
        for item_id, fields in changes.items():
            for field, value in fields.items():
                if field not in allowed_fields:
                    continue
                cursor.execute(
                    f"UPDATE {table} SET {field}=%s WHERE id=%s",
                    (value, item_id)
                )

        # Add new items
        for temp_id, item_data in new_items.items():
            cursor.execute(
                f"""INSERT INTO {table} (category, title, description, price, position, active)
                   VALUES (%s, %s, %s, %s, %s, TRUE)""",
                (
                    item_data.get("category", "Ukjent"),
                    item_data.get("title", "Ny vare"),
                    item_data.get("description", ""),
                    float(item_data.get("price", 0))
                )
            )

        # Delete items
        for item_id in deleted_items:
            cursor.execute(f"DELETE FROM {table} WHERE id=%s", (item_id,))

        # Update positions
        for item_id, position in positions.items():
            if not str(item_id).startswith('new_'):
                cursor.execute(
                    f"UPDATE {table} SET position=%s WHERE id=%s",
                    (position, item_id)
                )

        conn.commit()
        return {"ok": True}

    except Exception as e:
        conn.rollback()
        return {"ok": False, "error": str(e)}
    finally:
        cursor.close()
        conn.close()

@app.route("/bestille-fra-kantina")
def bestille_fra_kantina():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    categories = {}
    items = get_menu_items("kantine")
    for it in items:
        categories.setdefault(it["category"] or "Ukjent", []).append(it)
    return render_template("personlig/bestille_fra_kantina.html", categories=categories, menu_source="kantine")

@app.route("/bestille-fra-WAKEUP")
def bestille_fra_WAKEUP():
    categories = {}
    items = get_menu_items("wakeup")
    for it in items:
        categories.setdefault(it["category"] or "Ukjent", []).append(it)
    return render_template("personlig/bestille_fra_WAKEUP.html", categories=categories, menu_source="wakeup")

@app.route('/submit', methods=['POST'])
def submit():
    navn = request.form.get('navn')
    mobil = request.form.get('mobil')
    organisasjonsnummer = request.form.get('organisasjonsnummer')
    fakturaadresse = request.form.get('fakturaadresse')
    epost = request.form.get('epost')
    ressursnummer = request.form.get('ressursnummer')
    koststed = request.form.get('koststed')
    if koststed == "other":
        koststed = request.form.get("koststedCustom", "").strip() or "Ukjent"

    ordre_dato = datetime.now()
    ordre_tid = datetime.now().strftime("%H:%M")
    hent_dato = request.form.get('hent_dato')
    hent_tid = request.form.get('hent_tid')
    melding = request.form.get('melding')

    spise_i_kantina_bool = 'spise_i_kantina' in request.form
    antall_personer = request.form.get('antall_personer', '').strip()
    spise_i_kantina = f"Ja, {antall_personer} personer" if spise_i_kantina_bool else "Nei"

    menu_source = request.form.get("menu_source") or "kantine"
    menu_items = get_menu_items(menu_source)
    menu_map = {str(it["id"]): it for it in menu_items}

    ordre = {}
    total = 0
    for key, val in request.form.items():
        if key.startswith("item_"):
            item_id = key.split("_", 1)[1]
            qty = val.strip()
            if qty and qty.isdigit() and int(qty) > 0:
                item = menu_map.get(item_id)
                if not item:
                    continue
                antall = int(qty)
                pris = float(item["price"])
                sum_vare = antall * pris
                ordre[item["title"]] = {"antall": antall, "pris": pris, "sum": sum_vare}
                total += sum_vare

    try:
        conn = get_connection_kantine()
        cursor = conn.cursor()
        sql = """
            INSERT INTO orders
            (navn, mobil, organisasjonsnummer, fakturaadresse, epost, ressursnummer,
             koststed, ordre_dato, ordre_tid, hent_dato, hent_tid, spise_i_kantina, melding, ordre, sum)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(sql, (
            navn, mobil, organisasjonsnummer, fakturaadresse, epost, ressursnummer,
            koststed, ordre_dato, ordre_tid, hent_dato, hent_tid, spise_i_kantina, melding, json.dumps(ordre), total
        ))
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        return f"Databasefeil: {e}"

    order_info = {
        "navn": navn, "mobil": mobil, "epost": epost,
        "organisasjonsnummer": organisasjonsnummer,
        "fakturaadresse": fakturaadresse,
        "ressursnummer": ressursnummer,
        "koststed": koststed,
        "ordre_dato": ordre_dato, "ordre_tid": ordre_tid,
        "hent_dato": hent_dato, "hent_tid": hent_tid,
        "spise_i_kantina": spise_i_kantina,
        "melding": melding,
        "ordre": ordre, "total": total
    }

    return render_template("kvittering.html", order=order_info)



if __name__ == '__main__':
    app.run(debug=True)
