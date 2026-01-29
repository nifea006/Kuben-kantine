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
                sum INT
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
                price DECIMAL(10,2) DEFAULT 0,
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
        epost = request.form.get("email").strip().lower()
        navn = request.form.get("navn").strip()

        conn = get_connection_kantine()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE epost = %s", (epost,))
        user = cursor.fetchone()

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
        session["id"] = user["id"]
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


# ↓ Bestillinger ↓
# Personlig:
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
    order_info = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("bestillinger.html", order_info=order_info, role=role)

# Kjøkken:
@app.route("/aktive-bestillinger-i-kantinen")
def aktive_bestillinger_i_kantinen():
    role = session.get("active_role")
    if role != "kjokken":
        return redirect(url_for("login"))
    
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE status_levert = FALSE OR status_levert IS NULL ORDER BY id ASC")
    order_info = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("bestillinger.html", order_info=order_info, role=role)

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

# Økonomi:
@app.route("/ferdige-bestillinger")
def ferdige_bestillinger():
    role = session.get("active_role")
    if role != "okonomi":
        return redirect(url_for("login"))
    
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
    return render_template("bestillinger.html", order_info=order_info, role=role)

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

# Vis kvittering:
@app.route("/vis-bestilling/<int:order_id>")
def vis_bestilling(order_id):
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order_info = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("kvittering.html", order_info=order_info, order_array=json.loads(order_info["order_array"]))

# Admin:
@app.route('/admin-bestillinger', methods=['GET'])
def admin_bestillinger():
    role = session.get("active_role")
    if role != "admin":
        return redirect(url_for("login"))
    
    conn_kantine = get_connection_kantine()
    cursor = conn_kantine.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    order_info = cursor.fetchall()
    cursor.execute("SELECT * FROM users")
    users_info = cursor.fetchall()
    cursor.close()
    conn_kantine.close()
    return render_template("bestillinger.html", order_info=order_info, users_info=users_info, role=role)

@app.route('/slett-bestilling/<int:order_id>', methods=["POST"])
def slett_bestilling(order_id):
    role = session.get("active_role")
    if role != "admin":
        return redirect(url_for("login"))
    
    conn = get_connection_kantine()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM orders WHERE id = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_bestillinger"))
# ↑ Bestillinger ↑

def _table_for(menu_source):
    if menu_source == "kantine":
        return "menu_kantine"
    if menu_source == "wakeup":
        return "menu_wakeup"
    return None

def get_menu_items(menu_source):
    table = _table_for(menu_source)
    if not table:
        return []
    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table} WHERE active=TRUE ORDER BY position ASC, id ASC")
    items = cursor.fetchall()
    cursor.close()
    conn.close()
    return items

@app.route("/bestille-fra-kantina")
def bestille_fra_kantina():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    session["menu_source"] = "kantine"
    categories = {}
    items = get_menu_items("kantine")
    for item in items:
        categories.setdefault(item["category"] or "Ukjent", []).append(item)
    return render_template("personlig/bestille_mat.html", categories=categories, menu_source="kantine")

@app.route("/bestille-fra-WAKEUP")
def bestille_fra_WAKEUP():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))
    session["menu_source"] = "wakeup"
    categories = {}
    items = get_menu_items("wakeup")
    for item in items:
        categories.setdefault(item["category"] or "Ukjent", []).append(item)
    return render_template("personlig/bestille_mat.html", categories=categories, menu_source="wakeup")

@app.route('/submit', methods=['POST'])
def submit():
    user_id = session.get("id")

    # Menu source
    menu_source = session.get("menu_source")
    menu_items = get_menu_items(menu_source)

    # Dato, tid og melding
    ordre_dato = datetime.now()
    ordre_tid = datetime.now().strftime("%H:%M")
    hent_dato = request.form.get('hent_dato')
    hent_tid = request.form.get('hent_tid')
    melding = request.form.get('melding')

    # Tell summen
    order_array = {}
    ordresum = 0

    for ordered_item, ordered_amount in request.form.items():
        if ordered_item.startswith("item_") and ordered_amount and int(ordered_amount) > 0:
            for item in menu_items:
                if item['id'] == int(ordered_item[5:]):
                    sum = int(item['price']) * int(ordered_amount)
                    ordresum = ordresum + sum
                    order_array[item["title"]] = {"antall": int(ordered_amount), "pris": int(item['price']), "sum": int(sum)}

    if menu_source == "kantine":
        # Kundeinformasjon
        navn = request.form.get('navn')
        mobil = request.form.get('mobil')
        organisasjonsnummer = request.form.get('organisasjonsnummer')
        fakturaadresse = request.form.get('fakturaadresse')
        epost = request.form.get('epost')
        ressursnummer = request.form.get('ressursnummer')
        koststed = request.form.get('koststed')
        if koststed == "other":
                koststed = request.form.get("koststedCustom", "").strip() or "Ukjent"

        # Oppdater kundeinformasjon
        conn = get_connection_kantine()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users SET navn=%s, epost=%s, mobil=%s, organisasjonsnummer=%s, fakturaadresse=%s, ressursnummer=%s, koststed=%s
            WHERE id=%s
        """, (navn, epost, mobil, organisasjonsnummer, fakturaadresse, ressursnummer, koststed, user_id))
        conn.commit()
        cursor.close()
        conn.close()

        # Spise i kantina
        spise_i_kantina_bool = 'spise_i_kantina' in request.form
        antall_personer = request.form.get('antall_personer', '').strip()
        spise_i_kantina = f"Ja, {antall_personer} personer" if spise_i_kantina_bool else "Nei"

        # Legg til bestillingen
        try:
            conn = get_connection_kantine()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                INSERT INTO orders
                (kunde_id, navn, mobil, organisasjonsnummer, fakturaadresse, epost, ressursnummer, 
                koststed, ordre_dato, ordre_tid, hent_dato, hent_tid, spise_i_kantina, melding, order_array, sum)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                user_id, navn, mobil, organisasjonsnummer, fakturaadresse, epost,
                ressursnummer, koststed, ordre_dato, ordre_tid, hent_dato, hent_tid,
                spise_i_kantina, melding, json.dumps(order_array), ordresum
            ))
            conn.commit()
            order_id = cursor.lastrowid
            cursor.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
            order_info = cursor.fetchone()
            cursor.close()
            conn.close()
        except Error as e:
                return f"Databasefeil: {e}"

    elif menu_source == "wakeup":
        navn = request.form.get('navn')
        epost = request.form.get('epost')
        mobil = request.form.get('mobil')

        conn = get_connection_kantine()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            INSERT INTO orders
            (kunde_id, navn, epost, mobil, ordre_dato, ordre_tid, hent_dato, hent_tid, order_array, sum)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            user_id, navn, epost, mobil, ordre_dato, ordre_tid, hent_dato, hent_tid, json.dumps(order_array), ordresum
        ))
        conn.commit()
        order_id = cursor.lastrowid
        cursor.execute("SELECT * FROM orders WHERE id=%s", (order_id,))
        order_info = cursor.fetchone()
        cursor.close()
        conn.close()


    return render_template("kvittering.html", order_info=order_info, order_array=json.loads(order_info["order_array"]))



if __name__ == '__main__':
    app.run(debug=True)
