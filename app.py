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
        "Kaffekanne 1 liter": 90,
        "Kaffekontainer 5 liter": 250,
        "Brus": 35,
        "Mineralvann m/u kullsyre": 25,
        "Liten juice (eple/appelsin)": 20,
        "Melk 1 liter": 35,
        "Oksegryte med ris": 165,
        "Chili sin carne med rømme og basmatiris": 155,
        "Kyllinggryte med basmatiris/poteter": 165,
        "Sesongens frukt (oppskåret)": 40,
        "Sesongens frukt med Twist": 50,
        "Nøttemiks med tørket frukt": 29,
        "Kjeks (pris pr person)": 19,
        "Muffins": 25,
        "Dagens kake (Sjokolade eller gulrot)": 30,
        "Cæsarsalat med krutonger og kylling": 79,
        "Salat med tunfisk og egg": 79,
        "Salat med kylling og pesto": 79
    }

    # Collect order items
    ordre = {}
    total = 0
    for key, value in request.form.items():
        if key.startswith("antall_") and value and int(value) > 0:
            navn_vare = key.replace("antall_", "").replace("_", " ")
            pris = 0
            for n, p in priser.items():
                if navn_vare.lower() in n.lower():
                    pris = p
                    break
            antall = int(value)
            sum_vare = antall * pris
            total += sum_vare
            ordre[n] = {"antall": antall, "pris": pris, "sum": sum_vare}

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
