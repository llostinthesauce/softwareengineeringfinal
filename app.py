from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
import random
import string

# =============================
# SETUP
# =============================

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'reservations.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =============================
# MODELS
# =============================

class Reservation(db.Model):
    __tablename__ = 'reservations'
    id = db.Column(db.Integer, primary_key=True)
    passengerName = db.Column(db.String(100), nullable=False)
    seatRow = db.Column(db.Integer, nullable=False)
    seatColumn = db.Column(db.Integer, nullable=False)
    eTicketNumber = db.Column(db.String(100), nullable=False)
    created = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

class Admin(db.Model):
    __tablename__ = 'admins'
    username = db.Column(db.String(100), primary_key=True)
    password = db.Column(db.String(100), nullable=False)

# =============================
# HELPER FUNCTIONS
# =============================

def get_cost_matrix():
    """Generate the 12x4 seat cost matrix."""
    return [[100, 75, 50, 100] for _ in range(12)]

def generate_eticket(first_name, last_name):
    """Generate a random e-ticket number."""
    initials = first_name[0].upper() + last_name[0].upper()
    random_letters = ''.join(random.choice(string.ascii_letters) for _ in range(6))
    suffix = "OTC4320"
    return f"{initials}{random_letters}{suffix}"

def build_seating_chart(reservations):
    """Create a 12x4 seating chart with 'O' for available and 'X' for reserved seats."""
    seating_chart = [['O' for _ in range(4)] for _ in range(12)]
    for res in reservations:
        if 0 <= res.seatRow < 12 and 0 <= res.seatColumn < 4:
            seating_chart[res.seatRow][res.seatColumn] = 'X'
    return seating_chart

# =============================
# ROUTES
# =============================

@app.route("/", methods=["GET"])
def index():
    """Splash home page."""
    return render_template("index.html")

@app.route("/reserve", methods=["GET", "POST"])
def reserve_seat():
    """Seat reservation page."""
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        seat_row = request.form.get("seat_row")
        seat_column = request.form.get("seat_column")

        # Validate seat row and column input
        try:
            seat_row = int(seat_row)
            seat_column = int(seat_column)
            if not (0 <= seat_row < 12 and 0 <= seat_column < 4):
                flash("Invalid seat selection. Row must be 0-11 and column must be 0-3.", "error")
                return redirect(url_for("reserve_seat"))
        except (ValueError, TypeError):
            flash("Please enter valid numeric values for seat row and column.", "error")
            return redirect(url_for("reserve_seat"))

        # Check if seat is already taken
        if Reservation.query.filter_by(seatRow=seat_row, seatColumn=seat_column).first():
            flash("Seat is already taken. Please choose another seat.", "error")
            return redirect(url_for("reserve_seat"))

        # Create reservation
        e_ticket = generate_eticket(first_name, last_name)
        passenger_name = f"{first_name} {last_name}"
        new_reservation = Reservation(
            passengerName=passenger_name,
            seatRow=seat_row,
            seatColumn=seat_column,
            eTicketNumber=e_ticket
        )
        db.session.add(new_reservation)
        db.session.commit()

        flash(f"Reservation successful! Your e-ticket code is {e_ticket}", "success")
        return redirect(url_for("reserve_seat"))

    # Build seating chart for display
    reservations = Reservation.query.all()
    seating_chart = build_seating_chart(reservations)

    return render_template("reserve.html", seating_chart=seating_chart)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    """Admin login and dashboard."""
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            return render_template("admin.html", error="Please enter both username and password.")

        if Admin.query.filter_by(username=username, password=password).first():
            session['admin_logged_in'] = True
        else:
            return render_template("admin.html", error="Invalid username/password combination.")

    if session.get('admin_logged_in'):
        reservations = Reservation.query.all()
        seating_chart = build_seating_chart(reservations)
        total_sales = sum(get_cost_matrix()[res.seatRow][res.seatColumn] for res in reservations)

        return render_template("admin.html",
                               reservations=reservations,
                               total_sales=total_sales,
                               seating_chart=seating_chart)

    return render_template("admin.html")

@app.route("/delete_reservation/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    """Delete a reservation."""
    reservation = Reservation.query.get_or_404(reservation_id)
    db.session.delete(reservation)
    db.session.commit()
    flash("Reservation successfully deleted.", "admin")
    return redirect(url_for('admin'))

@app.route("/logout", methods=["POST"])
def logout():
    """Log out the admin."""
    session.pop("admin_logged_in", None)
    flash("You have been logged out.", "admin")
    return redirect(url_for("admin"))

# =============================
# MAIN
# =============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)