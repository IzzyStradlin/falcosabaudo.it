from flask import Flask, render_template, request, redirect, g, session, url_for, jsonify
import webbrowser
from threading import Timer
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
from src.routes import module3_routes
from src.utils.db import get_db_connection

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "supersecretkey")  # Add a secure key here in production

app.register_blueprint(module3_routes.module3_bp)

DATABASE_URL = os.environ.get("DATABASE_URL")
USERNAME = os.environ.get("APP_USERNAME", "testuser")
PASSWORD = os.environ.get("APP_PASSWORD", "mscairspa")

# --- Utility functions ---

def safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (TypeError, ValueError):
        return default

def time_to_minutes(h, m):
    return safe_int(h) * 60 + safe_int(m)

def minutes_to_hhmm(minutes):
    hours = minutes // 60
    mins = minutes % 60
    return f"{str(hours).zfill(2)}:{str(mins).zfill(2)}"

@app.teardown_appcontext
def close_db_connection(exception):
    db_conn = g.pop('db_conn', None)
    if db_conn is not None:
        db_conn.close()

# --- Authentication ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == USERNAME and password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('intro_page'))
        else:
            return render_template('html/login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.before_request
def require_login():
    if request.endpoint not in ['login', 'static'] and not session.get('logged_in'):
        return redirect(url_for('login'))
    
# Route for the Intro Page
@app.route('/')
def intro_page():
    return render_template('intro_page.html')

# Route for the Landing Page
@app.route('/landing')
def landing_page():
    return render_template('landing_page.html')

# --- Route for Module 1 (OCC Department) ---
@app.route('/module/1', methods=['GET', 'POST'])
def module_1():
    conn = get_db_connection()
    cur = conn.cursor()

    spi_names = [
        "Fleet Block time (HH:MM) - COM flights only",
        "Block time (I-MSCA)",
        "Block time (I-MSCB)",
        "Block time (I-MSCC)",
        "Fleet Flight cycles - COM flights only",
        "Flight cycles (I-MSCA)",
        "Flight cycles (I-MSCB)",
        "Flight cycles (I-MSCC)",
        "Fleet Flight hours per cycle",
        "Flight hours per cycle (I-MSCA)",
        "Flight hours per cycle (I-MSCB)",
        "Flight hours per cycle (I-MSCC)"
    ]

    now = datetime.now()
    previous_month_date = now - relativedelta(months=1)
    previous_month = previous_month_date.strftime("%b-%y")

    month_labels = []
    for i in range(4, 0, -1):
        m = now - relativedelta(months=i)
        month_labels.append(m.strftime("%b-%y"))
    if previous_month not in month_labels:
        month_labels.append(previous_month)

    # --- SAVE: always use "Mon-YY" format ---
    if request.method == 'POST':
        for spi in spi_names:
            is_group = (
                "Fleet Block time" in spi or
                "Fleet Flight cycles" in spi or
                "Fleet Flight hours per cycle" in spi
            )
            if spi in ["Flight cycles (I-MSCA)", "Flight cycles (I-MSCB)", "Flight cycles (I-MSCC)"]:
                cycle = safe_int(request.form.get(f"{spi}_cycle"))
                if cycle:
                    # Check if record exists
                    cur.execute("""
                        SELECT id FROM occ_flight_data 
                        WHERE spi_name = %s AND reference_month = %s
                    """, (spi, previous_month))
                    existing_record = cur.fetchone()
                    if existing_record:
                        cur.execute("""
                            UPDATE occ_flight_data 
                            SET flight_cycle = %s
                            WHERE spi_name = %s AND reference_month = %s
                        """, (cycle, spi, previous_month))
                    else:
                        cur.execute("""
                            INSERT INTO occ_flight_data (spi_name, reference_month, flight_cycle)
                            VALUES (%s, %s, %s)
                        """, (spi, previous_month, cycle))
            elif not is_group:
                hours = safe_int(request.form.get(f"{spi}_hours"))
                minutes = safe_int(request.form.get(f"{spi}_minutes"))
                if hours or minutes:
                    # Check if record exists
                    cur.execute("""
                        SELECT id FROM occ_flight_data 
                        WHERE spi_name = %s AND reference_month = %s
                    """, (spi, previous_month))
                    existing_record = cur.fetchone()
                    if existing_record:
                        cur.execute("""
                            UPDATE occ_flight_data 
                            SET flight_hours = %s, flight_minutes = %s
                            WHERE spi_name = %s AND reference_month = %s
                        """, (hours, minutes, spi, previous_month))
                    else:
                        cur.execute("""
                            INSERT INTO occ_flight_data (spi_name, reference_month, flight_hours, flight_minutes)
                            VALUES (%s, %s, %s, %s)
                        """, (spi, previous_month, hours, minutes))
        conn.commit()

        # --- UPDATE/CREATE FLEET BLOCK TIME RECORD ---
        block_time_children = ["Block time (I-MSCA)", "Block time (I-MSCB)", "Block time (I-MSCC)"]
        cur.execute("""
            SELECT flight_hours, flight_minutes
            FROM occ_flight_data
            WHERE spi_name = ANY(%s) AND reference_month = %s
        """, (block_time_children, previous_month))
        times = cur.fetchall()
        total_minutes = sum([time_to_minutes(h, m) for h, m in times if h is not None and m is not None])
        count = len([1 for h, m in times if h is not None and m is not None])
        if count > 0:
            avg_minutes = total_minutes // count
            avg_hours = avg_minutes // 60
            avg_only_minutes = avg_minutes % 60
            # Check if record exists
            cur.execute("""
                SELECT id FROM occ_flight_data 
                WHERE spi_name = %s AND reference_month = %s
            """, ("Fleet Block time (HH:MM) - COM flights only", previous_month))
            existing_record = cur.fetchone()
            if existing_record:
                cur.execute("""
                    UPDATE occ_flight_data 
                    SET flight_hours = %s, flight_minutes = %s
                    WHERE spi_name = %s AND reference_month = %s
                """, (avg_hours, avg_only_minutes, "Fleet Block time (HH:MM) - COM flights only", previous_month))
            else:
                cur.execute("""
                    INSERT INTO occ_flight_data (spi_name, reference_month, flight_hours, flight_minutes)
                    VALUES (%s, %s, %s, %s)
                """, ("Fleet Block time (HH:MM) - COM flights only", previous_month, avg_hours, avg_only_minutes))

        # --- UPDATE/CREATE FLEET FLIGHT CYCLES RECORD ---
        flight_cycle_children = ["Flight cycles (I-MSCA)", "Flight cycles (I-MSCB)", "Flight cycles (I-MSCC)"]
        cur.execute("""
            SELECT flight_cycle
            FROM occ_flight_data
            WHERE spi_name = ANY(%s) AND reference_month = %s
        """, (flight_cycle_children, previous_month))
        cycles = cur.fetchall()
        total_cycles = sum([safe_int(c[0]) for c in cycles if c[0] is not None])
        # Check if record exists
        cur.execute("""
            SELECT id FROM occ_flight_data 
            WHERE spi_name = %s AND reference_month = %s
        """, ("Fleet Flight cycles - COM flights only", previous_month))
        existing_record = cur.fetchone()
        if existing_record:
            cur.execute("""
                UPDATE occ_flight_data 
                SET flight_cycle = %s
                WHERE spi_name = %s AND reference_month = %s
            """, (total_cycles, "Fleet Flight cycles - COM flights only", previous_month))
        else:
            cur.execute("""
                INSERT INTO occ_flight_data (spi_name, reference_month, flight_cycle)
                VALUES (%s, %s, %s)
            """, ("Fleet Flight cycles - COM flights only", previous_month, total_cycles))

        conn.commit()

        update_fleet_annual(cur, now)
        conn.commit()
        # ...existing code...

    # Always update fleet annuals also in GET (to keep them consistent)
    update_fleet_annual(cur, now)
    conn.commit()

    # --- READ: always use "Mon-YY" format ---
    cur.execute("""
        SELECT spi_name, reference_month, flight_hours, flight_minutes, flight_cycle
        FROM occ_flight_data
        WHERE spi_name = ANY(%s) AND reference_month = ANY(%s)
    """, (spi_names, month_labels))
    rows = cur.fetchall()

    # Organize data in a dictionary: data[spi][month] = value
    data = {spi: {m: "" for m in month_labels} for spi in spi_names}
    for spi, ref_month, fh, fm, fc in rows:
        if spi in ["Flight cycles (I-MSCA)", "Flight cycles (I-MSCB)", "Flight cycles (I-MSCC)", "Fleet Flight cycles - COM flights only"]:
            if fc is not None:
                data[spi][ref_month] = str(fc)
        else:
            if fh is not None and fm is not None:
                data[spi][ref_month] = f"{fh}:{str(fm).zfill(2)}"

    # Calcola la media da inizio anno per Fleet Flight cycles - COM flights only (mesi vuoti = 0)
    fleet_cycles = []
    fleet_block_times = []
    year_start = datetime(now.year, 1, 1)
    for m in month_labels:
        m_date = datetime.strptime(m, "%b-%y")
        if m_date >= year_start and m_date <= previous_month_date:
            # Fleet Flight cycles
            val = data["Fleet Flight cycles - COM flights only"].get(m)
            fleet_cycles.append(int(val) if val and val.isdigit() else 0)
            # Fleet Block time
            val_bt = data["Fleet Block time (HH:MM) - COM flights only"].get(m)
            if val_bt and ":" in val_bt:
                h, mi = val_bt.split(":")
                total_minutes = int(h) * 60 + int(mi)
            else:
                total_minutes = 0
            fleet_block_times.append(total_minutes)

    # Media Fleet Flight cycles
    if fleet_cycles:
        avg_fleet_cycles = round(sum(fleet_cycles) / len(fleet_cycles), 2)
    else:
        avg_fleet_cycles = ""

    # Media Fleet Block time (in formato HH:MM)
    if fleet_block_times:
        avg_minutes = sum(fleet_block_times) // len(fleet_block_times)
        avg_hours = avg_minutes // 60
        avg_only_minutes = avg_minutes % 60
        avg_fleet_block_time = f"{str(avg_hours).zfill(2)}:{str(avg_only_minutes).zfill(2)}"
    else:
        avg_fleet_block_time = "00:00"

    # Calcolo Rolling 12M per ogni SPI (escludendo previous_month)
    rolling_12m = {}
    rolling_months = []
    for i in range(13, 1, -1):  # 13 mesi fa fino a 2 mesi fa
        m = now - relativedelta(months=i)
        rolling_months.append(m.strftime("%b-%y"))

    for spi in spi_names:
        if spi == "Fleet Block time (HH:MM) - COM flights only":
            # Calcola la media dei figli per ogni mese della rolling window
            block_time_children = ["Block time (I-MSCA)", "Block time (I-MSCB)", "Block time (I-MSCC)"]
            total_minutes = 0
            for m in rolling_months:
                minutes_sum = 0
                count = 0
                for child in block_time_children:
                    val_bt = data[child].get(m)
                    if val_bt and ":" in val_bt:
                        h, mi = val_bt.split(":")
                        minutes_sum += int(h) * 60 + int(mi)
                        count += 1
                if count > 0:
                    total_minutes += minutes_sum // count  # media mensile dei figli
                else:
                    total_minutes += 0
            rolling_12m[spi] = f"{str(total_minutes // 60).zfill(2)}:{str(total_minutes % 60).zfill(2)}"
        elif spi == "Fleet Flight cycles - COM flights only":
            # Calcola la somma dei figli per ogni mese della rolling window
            flight_cycle_children = ["Flight cycles (I-MSCA)", "Flight cycles (I-MSCB)", "Flight cycles (I-MSCC)"]
            total_cycles = 0
            for m in rolling_months:
                cycles_sum = 0
                for child in flight_cycle_children:
                    val = data[child].get(m)
                    cycles_sum += int(val) if val and val.isdigit() else 0
                total_cycles += cycles_sum
            rolling_12m[spi] = total_cycles
        elif "Block time" in spi:
            # Somma minuti totali (come prima)
            total_minutes = 0
            for m in rolling_months:
                val_bt = data[spi].get(m)
                if val_bt and ":" in val_bt:
                    h, mi = val_bt.split(":")
                    total_minutes += int(h) * 60 + int(mi)
                else:
                    total_minutes += 0
            rolling_12m[spi] = f"{str(total_minutes // 60).zfill(2)}:{str(total_minutes % 60).zfill(2)}"
        elif "Flight cycles" in spi:
            # Somma cicli totali (come prima)
            total_cycles = 0
            for m in rolling_months:
                val = data[spi].get(m)
                total_cycles += int(val) if val and val.isdigit() else 0
            rolling_12m[spi] = total_cycles
        else:
            rolling_12m[spi] = ""  # O calcolo diverso se serve

    # --- Calcolo Aver./Sum e Rolling 12M per Flight hours per cycle ---
    avg_hours_per_cycle = {}
    rolling_12m_hours_per_cycle = {}

    # Aver./Sum (da inizio anno a previous_month)
    # Fleet
    total_fleet_minutes = sum(fleet_block_times)
    total_fleet_cycles = sum(fleet_cycles)
    if total_fleet_cycles > 0:
        avg = total_fleet_minutes / total_fleet_cycles
        avg_hours = int(avg // 60)
        avg_minutes = int(avg % 60)
        avg_hours_per_cycle["Fleet Flight hours per cycle"] = f"{str(avg_hours).zfill(2)}:{str(avg_minutes).zfill(2)}"
    else:
        avg_hours_per_cycle["Fleet Flight hours per cycle"] = "00:00"

    # Figli
    for ac in ["I-MSCA", "I-MSCB", "I-MSCC"]:
        block = []
        cycles = []
        for m in month_labels:
            val_bt = data[f"Block time ({ac})"].get(m)
            if val_bt and ":" in val_bt:
                h, mi = val_bt.split(":")
                block.append(int(h) * 60 + int(mi))
            else:
                block.append(0)
            val_cy = data[f"Flight cycles ({ac})"].get(m)
            cycles.append(int(val_cy) if val_cy and val_cy.isdigit() else 0)
        total_block = sum(block)
        total_cycles = sum(cycles)
        if total_cycles > 0:
            avg = total_block / total_cycles
            avg_hours = int(avg // 60)
            avg_minutes = int(avg % 60)
            avg_hours_per_cycle[f"Flight hours per cycle ({ac})"] = f"{str(avg_hours).zfill(2)}:{str(avg_minutes).zfill(2)}"
        else:
            avg_hours_per_cycle[f"Flight hours per cycle ({ac})"] = "00:00"

    # Rolling 12M (finestra mobile)
    # Fleet
    rolling_fleet_minutes = 0
    rolling_fleet_cycles = 0
    for m in rolling_months:
        # Fleet Block time
        val_bt = data["Fleet Block time (HH:MM) - COM flights only"].get(m)
        if val_bt and ":" in val_bt:
            h, mi = val_bt.split(":")
            rolling_fleet_minutes += int(h) * 60 + int(mi)
        # Fleet Flight cycles
        val_cy = data["Fleet Flight cycles - COM flights only"].get(m)
        rolling_fleet_cycles += int(val_cy) if val_cy and val_cy.isdigit() else 0
    if rolling_fleet_cycles > 0:
        avg = rolling_fleet_minutes / rolling_fleet_cycles
        avg_hours = int(avg // 60)
        avg_minutes = int(avg % 60)
        rolling_12m_hours_per_cycle["Fleet Flight hours per cycle"] = f"{str(avg_hours).zfill(2)}:{str(avg_minutes).zfill(2)}"
    else:
        rolling_12m_hours_per_cycle["Fleet Flight hours per cycle"] = "00:00"

    # Figli
    for ac in ["I-MSCA", "I-MSCB", "I-MSCC"]:
        block = 0
        cycles = 0
        for m in rolling_months:
            val_bt = data[f"Block time ({ac})"].get(m)
            if val_bt and ":" in val_bt:
                h, mi = val_bt.split(":")
                block += int(h) * 60 + int(mi)
            val_cy = data[f"Flight cycles ({ac})"].get(m)
            cycles += int(val_cy) if val_cy and val_cy.isdigit() else 0
        if cycles > 0:
            avg = block / cycles
            avg_hours = int(avg // 60)
            avg_minutes = int(avg % 60)
            rolling_12m_hours_per_cycle[f"Flight hours per cycle ({ac})"] = f"{str(avg_hours).zfill(2)}:{str(avg_minutes).zfill(2)}"
        else:
            rolling_12m_hours_per_cycle[f"Flight hours per cycle ({ac})"] = "00:00"

    # --- Calcolo Previous Full Year per Flight hours per cycle ---
    prev_year = (now - relativedelta(years=1)).year
    prev_year_months = [f"{datetime(prev_year, m, 1).strftime('%b-%y')}" for m in range(1, 13)]

    prev_year_hours_per_cycle = {}

    # Fleet
    total_fleet_minutes = 0
    total_fleet_cycles = 0
    for m in prev_year_months:
        val_bt = data["Fleet Block time (HH:MM) - COM flights only"].get(m)
        if val_bt and ":" in val_bt:
            h, mi = val_bt.split(":")
            total_fleet_minutes += int(h) * 60 + int(mi)
        val_cy = data["Fleet Flight cycles - COM flights only"].get(m)
        total_fleet_cycles += int(val_cy) if val_cy and val_cy.isdigit() else 0
    if total_fleet_cycles > 0:
        avg = total_fleet_minutes / total_fleet_cycles
        avg_hours = int(avg // 60)
        avg_minutes = int(avg % 60)
        prev_year_hours_per_cycle["Fleet Flight hours per cycle"] = f"{str(avg_hours).zfill(2)}:{str(avg_minutes).zfill(2)}"
    else:
        prev_year_hours_per_cycle["Fleet Flight hours per cycle"] = "00:00"

    # Figli
    for ac in ["I-MSCA", "I-MSCB", "I-MSCC"]:
        block = 0
        cycles = 0
        for m in prev_year_months:
            val_bt = data[f"Block time ({ac})"].get(m)
            if val_bt and ":" in val_bt:
                h, mi = val_bt.split(":")
                block += int(h) * 60 + int(mi)
            val_cy = data[f"Flight cycles ({ac})"].get(m)
            cycles += int(val_cy) if val_cy and val_cy.isdigit() else 0
        if cycles > 0:
            avg = block / cycles
            avg_hours = int(avg // 60)
            avg_minutes = int(avg % 60)
            prev_year_hours_per_cycle[f"Flight hours per cycle ({ac})"] = f"{str(avg_hours).zfill(2)}:{str(avg_minutes).zfill(2)}"
        else:
            prev_year_hours_per_cycle[f"Flight hours per cycle ({ac})"] = "00:00"

    # Passa le medie al template
    return render_template(
        'module_1.html',
        spi_names=spi_names,
        month_labels=month_labels,
        previous_month=previous_month,
        data=data,
        avg_fleet_cycles=avg_fleet_cycles,
        avg_fleet_block_time=avg_fleet_block_time,
        rolling_12m=rolling_12m,
        avg_hours_per_cycle=avg_hours_per_cycle,
        rolling_12m_hours_per_cycle=rolling_12m_hours_per_cycle,
        prev_year_hours_per_cycle=prev_year_hours_per_cycle
    )

def update_fleet_annual(cur, now):
    # --- FLEET BLOCK TIME ---
    block_time_children = ["Block time (I-MSCA)", "Block time (I-MSCB)", "Block time (I-MSCC)"]
    current_year = now.year
    start_month = datetime(current_year, 1, 1)
    months_to_consider = []
    m = start_month
    while m <= now:
        months_to_consider.append(m.strftime("%b-%y"))
        m += relativedelta(months=1)
    # Average Block time children
    cur.execute("""
        SELECT flight_hours, flight_minutes
        FROM occ_flight_data
        WHERE spi_name = ANY(%s) AND reference_month = ANY(%s) AND reference_year = %s
    """, (block_time_children, months_to_consider, current_year))
    times = cur.fetchall()
    total_minutes = 0
    count = 0
    for h, m in times:
        if h is not None and m is not None:
            total_minutes += int(h) * 60 + int(m)
            count += 1
    if count > 0:
        avg_minutes = total_minutes // count
        avg_hours = avg_minutes // 60
        avg_only_minutes = avg_minutes % 60
        cur.execute("""
            UPDATE occ_flight_data
            SET reference_month = %s, flight_hours = %s, flight_minutes = %s
            WHERE spi_name = %s AND reference_year = %s
        """, (now.strftime("%b-%y"), avg_hours, avg_only_minutes, "Fleet Block time (HH:MM) - COM flights only", current_year))
        if cur.rowcount == 0:
            cur.execute("""
                INSERT INTO occ_flight_data (spi_name, reference_month, reference_year, flight_hours, flight_minutes)
                VALUES (%s, %s, %s, %s, %s)
            """, ("Fleet Block time (HH:MM) - COM flights only", now.strftime("%b-%y"), current_year, avg_hours, avg_only_minutes))

    # --- FLEET FLIGHT CYCLES ---
    flight_cycle_children = ["Flight cycles (I-MSCA)", "Flight cycles (I-MSCB)", "Flight cycles (I-MSCC)"]
    cur.execute("""
        SELECT flight_cycle
        FROM occ_flight_data
        WHERE spi_name = ANY(%s) AND reference_month = ANY(%s) AND reference_year = %s
    """, (flight_cycle_children, months_to_consider, current_year))
    cycles = cur.fetchall()
    total_cycles = sum([c[0] for c in cycles if c[0] is not None])
    cur.execute("""
        UPDATE occ_flight_data
        SET reference_month = %s, flight_cycle = %s
        WHERE spi_name = %s AND reference_year = %s
    """, (now.strftime("%b-%y"), total_cycles, "Fleet Flight cycles - COM flights only", current_year))
    if cur.rowcount == 0:
        cur.execute("""
            INSERT INTO occ_flight_data (spi_name, reference_month, reference_year, flight_cycle)
            VALUES (%s, %s, %s, %s)
        """, ("Fleet Flight cycles - COM flights only", now.strftime("%b-%y"), current_year, total_cycles))

@app.route('/module/1/edit/<int:id>', methods=['GET', 'POST'])
def edit_flight_data(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        # Ottieni i nuovi dati dal modulo
        flight_cycle = int(request.form.get('flight_cycle'))
        flight_hours = int(request.form.get('flight_hours'))
        flight_minutes = int(request.form.get('flight_minutes'))
        reference_month = request.form.get('reference_month')

        # Aggiorna i dati nel database
        try:
            cur.execute("""
                UPDATE occ_flight_data
                SET flight_cycle = %s, flight_hours = %s, flight_minutes = %s, reference_month = %s
                WHERE id = %s
            """, (flight_cycle, flight_hours, flight_minutes, reference_month, id))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error updating data: {e}")
            return f"An error occurred: {e}", 500

        return redirect('/module/1')

    # Recupera i dati esistenti per precompilare il modulo
    cur.execute("SELECT flight_cycle, flight_hours, flight_minutes, reference_month FROM occ_flight_data WHERE id = %s", (id,))
    flight_data = cur.fetchone()
    cur.close()

    return render_template('edit_flight_data.html', flight_data=flight_data, id=id)

# Route for Module 2 (Safety Control Department)
@app.route('/module/2', methods=['GET', 'POST'])
def module_2():
    conn = get_db_connection()
    cur = conn.cursor()

    # Get current month and previous month
    now = datetime.now()
    previous_month_date = now - relativedelta(months=1)
    previous_month = previous_month_date.strftime("%b-%y")

    if request.method == 'POST':
        # Ottieni i dati dal modulo e aggiorna solo il mese precedente
        try:
            for spi_name in request.form:
                if spi_name.endswith('_percentage'):
                    spi = spi_name.replace('_percentage', '')
                    try:
                        percentage = float(request.form[spi_name])
                        if 0 <= percentage <= 100:
                            # Check if record exists
                            cur.execute("""
                                SELECT id FROM compliance_data 
                                WHERE spi = %s AND reference_month = %s
                            """, (spi, previous_month))
                            
                            existing_record = cur.fetchone()
                            
                            if existing_record:
                                # Update existing record
                                cur.execute("""
                                    UPDATE compliance_data 
                                    SET percentage = %s
                                    WHERE spi = %s AND reference_month = %s
                                """, (percentage, spi, previous_month))
                            else:
                                # Insert new record
                                cur.execute("""
                                    INSERT INTO compliance_data (spi, reference_month, percentage)
                                    VALUES (%s, %s, %s)
                                """, (spi, previous_month, percentage))
                    except ValueError:
                        continue
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error inserting data: {e}")
            return f"An error occurred: {e}", 500

        return redirect('/module/2')

    # Recupera i dati esistenti dal database
    try:
        cur.execute("""
            SELECT id, spi, reference_month, percentage
            FROM compliance_data
            ORDER BY reference_month DESC
        """)
        compliance_data = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data: {e}")
        compliance_data = []

    cur.close()
    return render_template('module_2.html', compliance_data=compliance_data)



# Route for Module 4 (CAMO Department)
@app.route('/module/4', methods=['GET', 'POST'])
def module_4():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        # Ottieni i dati dal modulo
        spi = request.form.get('spi')
        reference_month_abbr = request.form.get('reference_month')
        reference_year = request.form.get('reference_year')
        value = int(request.form.get('value'))

        # Mappa dei mesi abbreviati a numeri
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }

        # Combina anno e mese in formato YYYY-MM
        reference_month = f"{reference_year}-{month_map[reference_month_abbr]}"

        # Inserisci i dati nel database
        try:
            # Check if record exists for camo_data
            cur.execute("""
                SELECT id FROM camo_data WHERE spi = %s AND reference_month = %s AND reference_year = %s
            """, (spi, reference_month, reference_year))
            existing_record = cur.fetchone()
            if existing_record:
                cur.execute("""
                    UPDATE camo_data SET value = %s
                    WHERE spi = %s AND reference_month = %s AND reference_year = %s
                """, (value, spi, reference_month, reference_year))
            else:
                cur.execute("""
                    INSERT INTO camo_data (spi, reference_month, reference_year, value)
                    VALUES (%s, %s, %s, %s)
                """, (spi, reference_month, reference_year, value))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error inserting data: {e}")
            return f"An error occurred: {e}", 500

        return redirect('/module/4')

    # Recupera i dati esistenti dal database
    try:
        cur.execute("""
            SELECT id, spi, reference_month, reference_year, value, created_at
            FROM camo_data
            ORDER BY created_at DESC
        """)
        camo_data = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data: {e}")
        camo_data = []

    cur.close()
    return render_template('module_4.html', camo_data=camo_data)

# Route for Module 5 (Ground Operations Department)
@app.route('/module/5', methods=['GET', 'POST'])
def module_5():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        # Ottieni i dati dal modulo
        spi = request.form.get('spi')
        reference_month_abbr = request.form.get('reference_month')  # Es. "Jan"
        reference_year = request.form.get('reference_year')  # Es. "2032"
        value = int(request.form.get('value'))  # Accetta solo interi

        # Mappa dei mesi abbreviati a numeri
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }

        # Combina anno e mese in formato YYYY-MM
        reference_month = f"{reference_year}-{month_map[reference_month_abbr]}"

        # Inserisci i dati nel database
        try:
            # Check if record exists for ground_ops_data
            cur.execute("""
                SELECT id FROM ground_ops_data WHERE spi = %s AND reference_month = %s
            """, (spi, reference_month))
            existing_record = cur.fetchone()
            if existing_record:
                cur.execute("""
                    UPDATE ground_ops_data SET value = %s
                    WHERE spi = %s AND reference_month = %s
                """, (value, spi, reference_month))
            else:
                cur.execute("""
                    INSERT INTO ground_ops_data (spi, reference_month, value)
                    VALUES (%s, %s, %s)
                """, (spi, reference_month, value))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error inserting data: {e}")
            return f"An error occurred: {e}", 500

        return redirect('/module/5')

    # Recupera i dati esistenti
    try:
        cur.execute("""
            SELECT id, spi, reference_month, value
            FROM ground_ops_data
            ORDER BY reference_month DESC
        """)
        ground_ops_data = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data: {e}")
        ground_ops_data = []

    cur.close()
    return render_template('module_5.html', ground_ops_data=ground_ops_data)

# Route for Module 6 (Crew Department)
@app.route('/module/6', methods=['GET', 'POST'])
def module_6():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        # Ottieni i dati dal modulo
        spi = request.form.get('spi')
        reference_month_abbr = request.form.get('reference_month')  # Es. "Jan"
        reference_year = request.form.get('reference_year')  # Es. "2032"
        value = float(request.form.get('value'))  # Accetta valori in percentuale

        # Mappa dei mesi abbreviati a numeri
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }

        # Combina anno e mese in formato YYYY-MM
        reference_month = f"{reference_year}-{month_map[reference_month_abbr]}"

        # Inserisci i dati nel database
        try:
            # Check if record exists for crewtng_data
            cur.execute("""
                SELECT id FROM crewtng_data WHERE spi = %s AND reference_month = %s
            """, (spi, reference_month))
            existing_record = cur.fetchone()
            if existing_record:
                cur.execute("""
                    UPDATE crewtng_data SET value = %s
                    WHERE spi = %s AND reference_month = %s
                """, (value, spi, reference_month))
            else:
                cur.execute("""
                    INSERT INTO crewtng_data (spi, reference_month, value)
                    VALUES (%s, %s, %s)
                """, (spi, reference_month, value))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error inserting data: {e}")
            return f"An error occurred: {e}", 500

        return redirect('/module/6')

    # Recupera i dati esistenti
    try:
        cur.execute("""
            SELECT id, spi, reference_month, value
            FROM crewtng_data
            ORDER BY reference_month DESC
        """)
        crewtng_data = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data: {e}")
        crewtng_data = []

    cur.close()
    return render_template('module_6.html', crewtng_data=crewtng_data)

# Route for Module 7 (Flight Ops Department)
@app.route('/module/7', methods=['GET', 'POST'])
def module_7():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        # Ottieni i dati dal modulo
        spi = request.form.get('spi')
        reference_month_abbr = request.form.get('reference_month')  # Es. "Jan"
        reference_year = request.form.get('reference_year')  # Es. "2032"
        value = int(request.form.get('value'))  # Accetta solo interi

        # Mappa dei mesi abbreviati a numeri
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }

        # Combina anno e mese in formato YYYY-MM
        reference_month = f"{reference_year}-{month_map[reference_month_abbr]}"

        # Inserisci i dati nel database
        try:
            # Check if record exists for flight_ops_data
            cur.execute("""
                SELECT id FROM flight_ops_data WHERE spi = %s AND reference_month = %s
            """, (spi, reference_month))
            existing_record = cur.fetchone()
            if existing_record:
                cur.execute("""
                    UPDATE flight_ops_data SET value = %s
                    WHERE spi = %s AND reference_month = %s
                """, (value, spi, reference_month))
            else:
                cur.execute("""
                    INSERT INTO flight_ops_data (spi, reference_month, value)
                    VALUES (%s, %s, %s)
                """, (spi, reference_month, value))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error inserting data: {e}")
            return f"An error occurred: {e}", 500

        return redirect('/module/7')

    # Recupera i dati esistenti
    try:
        cur.execute("""
            SELECT id, spi, reference_month, value
            FROM flight_ops_data
            ORDER BY reference_month DESC
        """)
        flight_ops_data = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data: {e}")
        flight_ops_data = []

    cur.close()
    return render_template('module_7.html', flight_ops_data=flight_ops_data)

# Route for Module 8 (Cargo Department)
@app.route('/module/8', methods=['GET', 'POST'])
def module_8():
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        # Ottieni i dati dal modulo
        spi = request.form.get('spi')
        reference_month_abbr = request.form.get('reference_month')  # Es. "Jan"
        reference_year = request.form.get('reference_year')  # Es. "2032"
        value = int(request.form.get('value'))  # Accetta valori long

        # Mappa dei mesi abbreviati a numeri
        month_map = {
            "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
            "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
            "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
        }

        # Combina anno e mese in formato YYYY-MM
        reference_month = f"{reference_year}-{month_map[reference_month_abbr]}"

        # Inserisci i dati nel database
        try:
            # Check if record exists for cargo_data
            cur.execute("""
                SELECT id FROM cargo_data WHERE spi = %s AND reference_month = %s
            """, (spi, reference_month))
            existing_record = cur.fetchone()
            if existing_record:
                cur.execute("""
                    UPDATE cargo_data SET value = %s
                    WHERE spi = %s AND reference_month = %s
                """, (value, spi, reference_month))
            else:
                cur.execute("""
                    INSERT INTO cargo_data (spi, reference_month, value)
                    VALUES (%s, %s, %s)
                """, (spi, reference_month, value))
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error inserting data: {e}")
            return f"An error occurred: {e}", 500

        return redirect('/module/8')

    # Recupera i dati esistenti
    try:
        cur.execute("""
            SELECT id, spi, reference_month, value
            FROM cargo_data
            ORDER BY reference_month DESC
        """)
        cargo_data = cur.fetchall()
    except Exception as e:
        print(f"Error fetching data: {e}")
        cargo_data = []

    cur.close()
    return render_template('module_8.html', cargo_data=cargo_data)

# Route for Reporting
@app.route('/reporting', methods=['GET'])
def reporting():
    # Aggiungi qui la logica per generare e visualizzare i report
    return render_template('reporting.html')

# Success Page
@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/module/1/chart-data', methods=['GET'])
def get_chart_data():
    conn = get_db_connection()
    cur = conn.cursor()

    # Explicitly set months_to_fetch to 12
    months_to_fetch = 12

    # Calculate the date range for the last 'months_to_fetch' months
    now = datetime.now()
    month_labels = [(now - relativedelta(months=i)).strftime('%b-%y') for i in range(months_to_fetch)]

    # Create a predefined order for months
    month_order = {month: idx for idx, month in enumerate(month_labels[::-1])}  # Reverse to ensure chronological order

    # Query data for the chart
    cur.execute("""
        SELECT reference_month, flight_hours, flight_minutes, flight_cycle
        FROM occ_flight_data
        WHERE spi_name = 'Fleet Block time (HH:MM) - COM flights only'
          AND reference_month IN %s
        ORDER BY reference_month
    """, (tuple(month_labels),))
    rows = cur.fetchall()

    # Sort rows based on the predefined order
    rows.sort(key=lambda row: month_order.get(row[0], float('inf')))

    months = []
    flight_hours_values = []
    flight_cycles_values = []
    for month, hours, minutes, cycles in rows:
        months.append(month)
        total_minutes = safe_int(hours) * 60 + safe_int(minutes)
        flight_hours_values.append(total_minutes / 60)  # Convert to hours
        flight_cycles_values.append(safe_int(cycles))

    cur.close()
    conn.close()

    return jsonify({"months": months, "flight_hours_values": flight_hours_values, "flight_cycles_values": flight_cycles_values})

@app.route('/module/2/chart-data', methods=['GET'])
def get_compliance_chart_data():
    conn = get_db_connection()
    cur = conn.cursor()

    # Calculate the date range for the last 12 months
    now = datetime.now()
    month_labels = [(now - relativedelta(months=i)).strftime('%b-%y') for i in range(12)]
    month_labels.reverse()  # Ensure chronological order

    # Get all unique SPIs from the database
    cur.execute("""
        SELECT DISTINCT spi
        FROM compliance_data
        ORDER BY spi
    """)
    spi_names = [row[0] for row in cur.fetchall()]

    # Query data for each SPI
    datasets = []
    colors = [
        'rgba(75, 192, 192, 1)',   # teal
        'rgba(255, 99, 132, 1)',   # red
        'rgba(153, 102, 255, 1)',  # purple
        'rgba(255, 159, 64, 1)',   # orange
        'rgba(54, 162, 235, 1)',   # blue
        'rgba(255, 206, 86, 1)',   # yellow
    ]

    for idx, spi in enumerate(spi_names):
        cur.execute("""
            SELECT reference_month, percentage
            FROM compliance_data
            WHERE spi = %s AND reference_month = ANY(%s)
            ORDER BY reference_month
        """, (spi, month_labels))
        
        data = {month: 0 for month in month_labels}  # Initialize with zeros
        for row in cur.fetchall():
            data[row[0]] = float(row[1])

        color_idx = idx % len(colors)
        datasets.append({
            'label': spi,
            'data': list(data.values()),
            'borderColor': colors[color_idx],
            'backgroundColor': colors[color_idx].replace('1)', '0.2)'),
            'hidden': idx > 0  # Show only first dataset by default
        })

    cur.close()
    conn.close()

    return jsonify({
        "months": month_labels,
        "datasets": datasets
    })

if __name__ == '__main__':
    # Funzione per aprire il browser predefinito (opzionale per Render)
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000/")

    # Ottieni la porta dalla variabile di ambiente (default: 5000)
    port = int(os.environ.get("PORT", 5000))

    # Avvia il server Flask
    app.run(host="0.0.0.0", port=port, debug=False)