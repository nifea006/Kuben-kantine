from flask import Flask, render_template, request, redirect
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# Database connection
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="nikita",
        password="nikita2007",
        database="kuben_kantine"
    )

# Create table if not exists
def create_table():
    try:
        conn = get_connection()
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
                spise_i_kantina BOOLEAN,
                melding TEXT,
                ordre TEXT
            )
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        print("Feil ved oppretting av tabell:", e)

create_table()

# Routes
@app.route('/')
def home():
    return render_template('Bestillingsskjema.html')

@app.route('/submit', methods=['POST'])
def submit():
    navn = request.form['navn']
    mobil = request.form['mobil']
    organisasjonsnummer = request.form['organisasjonsnummer']
    fakturaadresse = request.form['fakturaadresse']
    epost = request.form['epost']
    ressursnummer = request.form['ressursnummer']
    koststed = request.form['koststed']
    hent_dato = request.form['hent_dato']
    hent_tid = request.form['hent_tid']
    spise_i_kantina = 'spise_i_kantina' in request.form
    melding = request.form['melding']

    # Menu with prices
    priser = {
    "antall_Kaffekanne_1l": {"navn": "Kaffekanne 1 liter", "pris": 90},
    "antall_Kaffekontainer_5l": {"navn": "Kaffekontainer 5 liter", "pris": 250},
    "antall_Brus": {"navn": "Brus", "pris": 35},
    "antall_Mineralvann": {"navn": "Mineralvann m/u kullsyre", "pris": 25},
    "antall_Juice": {"navn": "Liten juice (eple/appelsin)", "pris": 20},
    "antall_Melk": {"navn": "Melk 1 liter", "pris": 35},
    "antall_Oksegryte": {"navn": "Oksegryte med ris", "pris": 165},
    "antall_ChiliSinCarne": {"navn": "Chili sin carne med rømme og basmatiris", "pris": 155},
    "antall_Kyllinggryte": {"navn": "Kyllinggryte med basmatiris/poteter", "pris": 165},
    "antall_FruktOppskåret": {"navn": "Sesongens frukt (oppskåret)", "pris": 40},
    "antall_FruktTwist": {"navn": "Sesongens frukt med Twist", "pris": 50},
    "antall_Nøttemiks": {"navn": "Nøttemiks med tørket frukt", "pris": 29},
    "antall_Kjeks": {"navn": "Kjeks (pris pr person)", "pris": 19},
    "antall_Muffins": {"navn": "Muffins", "pris": 25},
    "antall_Kake": {"navn": "Dagens kake (Sjokolade eller gulrot)", "pris": 30},
    "antall_Cæsarsalat": {"navn": "Cæsarsalat med krutonger og kylling", "pris": 79},
    "antall_Tunfisksalat": {"navn": "Salat med tunfisk og egg", "pris": 79},
    "antall_KyllingPesto": {"navn": "Salat med kylling og pesto", "pris": 79}
}

    # Collect order items
    ordre = {}
    total = 0
    for key, value in request.form.items():
        if key in priser and value and int(value) > 0:
            antall = int(value)
            navn_vare = priser[key]["navn"]
            pris = priser[key]["pris"]
            sum_vare = antall * pris
            total += sum_vare
            ordre[navn_vare] = {"antall": antall, "pris": pris, "sum": sum_vare}


    # Save to database
    try:
        conn = get_connection()
        cursor = conn.cursor()
        sql = """
            INSERT INTO orders
            (navn, mobil, organisasjonsnummer, fakturaadresse, epost, ressursnummer, koststed,
             hent_dato, hent_tid, spise_i_kantina, melding, ordre)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        cursor.execute(sql, (
            navn, mobil, organisasjonsnummer, fakturaadresse, epost,
            ressursnummer, koststed, hent_dato, hent_tid,
            spise_i_kantina, melding, str(ordre)
        ))
        conn.commit()
        cursor.close()
        conn.close()
    except Error as e:
        return f"Databasefeil: {e}"

    # Build data for receipt
    order_info = {
        "navn": navn,
        "epost": epost,
        "mobil": mobil,
        "koststed": koststed,
        "hent_dato": hent_dato,
        "hent_tid": hent_tid,
        "spise_i_kantina": spise_i_kantina,
        "ordre": ordre,
        "total": total
    }

    return render_template("success.html", order=order_info)


if __name__ == '__main__':
    app.run(debug=True)
