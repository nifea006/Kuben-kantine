import json
from flask import Flask, render_template, request, redirect, url_for, session, g
from datetime import datetime
import mysql.connector
from mysql.connector import Error
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.template_filter('fromjson')
def fromjson(value):
    import json
    try:
        return json.loads(value)
    except:
        return {}

@app.template_filter('format_date')
def format_date(value):
    if not value:
        return ''
    try:
        if isinstance(value, str):
            value = datetime.strptime(value, "%Y-%m-%d").date()
        return value.strftime("%d-%m-%y")
    except Exception:
        return value

app.jinja_env.filters['format_date'] = format_date

app.secret_key = "supersecret"

# Read environment variables
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_KANTINE = os.getenv("DB_KANTINE")

# Database connection
def get_connection_kantine():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_KANTINE
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
                hent_dato DATE,
                hent_tid TIME,
                spise_i_kantina VARCHAR(50),
                melding TEXT,
                ordre TEXT
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print("Feil ved oppretting av tabell:", e)

create_orders_table()

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
        print("Feil ved oppretting av tabell:", e)

create_user_table()


# Routes
@app.before_request
def before_request():
    g.current_endpoint = request.endpoint

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/main")
def main_menu():
    role = session.get("active_role")
    if not role:
        return redirect(url_for("login"))

    return render_template("main_menu.html", role=role)

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


@app.route("/admin-brukere", methods=["GET", "POST"])
def admin_brukere():
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


@app.route("/velg-stedet")
def velg_stedet():
    return render_template("personlig/velg_stedet.html")

@app.route("/bestille-fra-kantina")
def bestille_fra_kantina():
    return render_template("personlig/bestille_fra_kantina.html")

@app.route("/bestille-fra-WAKEUP")
def bestille_fra_WAKEUP():
    return render_template("personlig/bestille_fra_WAKEUP.html")


@app.route("/mine-bestillinger")
def mine_bestillinger():
    user = session.get("user")
    if not user:
        return redirect(url_for("login"))

    email = user["epost"]

    conn = get_connection_kantine()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM orders WHERE epost = %s ORDER BY id DESC", (email,))
    orders = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template("personlig/mine_bestillinger.html", orders=orders)

@app.route("/aktive-bestillinger-i-kantinen")
def aktive_bestillinger_i_kantinen():
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
    return render_template("kjokken/aktive_bestillinger_i_kantinen.html", orders=orders)

@app.route("/sett-levert/<int:order_id>", methods=["POST"])
def sett_levert(order_id):
    conn = get_connection_kantine()
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status_levert = TRUE WHERE id = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("aktive_bestillinger_i_kantinen"))


@app.route("/ferdige-bestillinger")
def ferdige_bestillinger():
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
    return render_template("okonomi/ferdige_bestillinger.html", orders=orders)

@app.route("/sett-fakturert/<int:order_id>", methods=["POST"])
def sett_fakturert(order_id):
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
        "total": total
    }
    return render_template("kvittering.html", order=order_info)

@app.route('/admin-bestillinger', methods=['GET'])
def admin_bestillinger():
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
            o["total"] = sum(item["sum"] for item in ordre_dict.values())
        except Exception:
            o["total"] = 0
        o["user_id"] = user_map.get(o["epost"], "Ukjent")

    return render_template("admin/admin_bestillinger.html", orders=orders)


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

    hent_dato = request.form.get('hent_dato')
    hent_tid = request.form.get('hent_tid')
    melding = request.form.get('melding')

    spise_i_kantina_bool = 'spise_i_kantina' in request.form
    antall_personer = request.form.get('antall_personer', '').strip()
    spise_i_kantina = f"Ja, {antall_personer} personer" if spise_i_kantina_bool else "Nei"

    meny = {
        "antall_Kaffekanne_1l": {"navn": "Kaffekanne 1 liter", "pris": 90},
        "antall_Kaffekontainer_5l": {"navn": "Kaffekontainer 5 liter", "pris": 250},
        "antall_Brus": {"navn": "Brus", "pris": 35},
        "antall_Mineralvann": {"navn": "Mineralvann m/u kullsyre", "pris": 25},
        "antall_Juice": {"navn": "Liten juice (eple/appelsin)", "pris": 20},
        "antall_Melk": {"navn": "Melk 1 liter", "pris": 35},
        "antall_Oksegryte": {"navn": "Oksegryte med ris", "pris": 165},
        "antall_ChiliSinCarne": {"navn": "Chili sin carne", "pris": 155},
        "antall_Kyllinggryte": {"navn": "Kyllinggryte med ris/poteter", "pris": 165},
        "antall_FruktOppskåret": {"navn": "Sesongens frukt (oppskåret)", "pris": 40},
        "antall_FruktTwist": {"navn": "Sesongens frukt med Twist", "pris": 50},
        "antall_Nøttemiks": {"navn": "Nøttemiks", "pris": 29},
        "antall_Kjeks": {"navn": "Kjeks (pris pr person)", "pris": 19},
        "antall_Muffins": {"navn": "Muffins", "pris": 25},
        "antall_Kake": {"navn": "Dagens kake", "pris": 30},
        "antall_Cæsarsalat": {"navn": "Cæsarsalat med kylling", "pris": 79},
        "antall_Tunfisksalat": {"navn": "Salat med tunfisk og egg", "pris": 79},
        "antall_KyllingPesto": {"navn": "Salat med kylling og pesto", "pris": 79}
    }

    ordre = {}
    total = 0
    for key, val in request.form.items():
        if key in meny and val and int(val) > 0:
            antall = int(val)
            pris = meny[key]["pris"]
            sum_vare = antall * pris
            ordre[meny[key]["navn"]] = {"antall": antall, "pris": pris, "sum": sum_vare}
            total += sum_vare

    try:
        conn = get_connection_kantine()
        cursor = conn.cursor()
        sql = """
            INSERT INTO orders
            (navn, mobil, organisasjonsnummer, fakturaadresse, epost, ressursnummer,
             koststed, hent_dato, hent_tid, spise_i_kantina, melding, ordre)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(sql, (
            navn, mobil, organisasjonsnummer, fakturaadresse, epost, ressursnummer,
            koststed, hent_dato, hent_tid, spise_i_kantina, melding, json.dumps(ordre)
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
        "hent_dato": hent_dato, "hent_tid": hent_tid,
        "spise_i_kantina": spise_i_kantina,
        "melding": melding,
        "ordre": ordre, "total": total
    }

    return render_template("kvittering.html", order=order_info)



if __name__ == '__main__':
    app.run(debug=True)
