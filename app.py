# FINAL STRUCTURED app.py

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os

# =============================
# SETUP
# =============================

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'reservations.db')
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
        # TODO: Handle reservation form submission (later) - note from maddie. Please make first name entry labeled 'first_name'
        pass

    reservations = Reservation.query.all()

    # Start with fresh 12x4 matrix (copy structure)
    base_matrix = get_cost_matrix()
    seating_chart = [['O' for _ in range(4)] for _ in range(12)]  # only showing O/X, not prices

    # Mark reserved seats
    for res in reservations:
        if 0 <= res.seatRow < 12 and 0 <= res.seatColumn < 4:
            seating_chart[res.seatRow][res.seatColumn] = 'X'

    return render_template("reserve.html", seating_chart=seating_chart)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"].strip()

        if not username or not password:
            return render_template("admin.html", error="Please enter both username and password.")

        admin = Admin.query.filter_by(username=username, password=password).first()

        if admin:
            session['admin_logged_in'] = True
        else:
            return render_template("admin.html", error="Invalid username/password com ")

    if session.get('admin_logged_in'):
        reservations = Reservation.query.all()
        cost_matrix = get_cost_matrix()
        seating_chart = [['O' for _ in range(4)] for _ in range(12)]
        total_sales = 0

        for res in reservations:
            row, col = res.seatRow, res.seatColumn
            seating_chart[row][col] = 'X'
            total_sales += cost_matrix[row][col]

        return render_template("admin.html",
                               reservations=reservations,
                               total_sales=total_sales,
                               seating_chart=seating_chart)

    return render_template("admin.html")

@app.route("/delete_reservation/<int:reservation_id>", methods=["POST"])
def delete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    db.session.delete(reservation)
    db.session.commit()
    flash("Success. The Reservation for {first_name} was successfully deleted.")
    return redirect(url_for('admin'))

# =============================
# MAIN
# =============================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)