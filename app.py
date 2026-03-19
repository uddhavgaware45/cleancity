<<<<<<< HEAD
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime

# -----------------------
# App Config
# -----------------------
app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'cleancity.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

# Create uploads folder if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# -----------------------
# Database Model
# -----------------------
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    upvotes = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# -----------------------
# Routes
# -----------------------

@app.route("/")
def home():
    return jsonify({"message": "CleanCity API is running 🚀"})


# 👉 Submit Report
@app.route("/report", methods=["POST"])
def report_issue():
    try:
        category = request.form.get("category")
        description = request.form.get("description")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        image = request.files.get("image")

        # Validation
        if not all([category, description, latitude, longitude, image]):
            return jsonify({"error": "All fields are required"}), 400

        # Secure filename
        filename = secure_filename(image.filename)

        # Unique filename (important)
        filename = f"{int(datetime.utcnow().timestamp())}_{filename}"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        # Save to DB
        report = Report(
            category=category,
            description=description,
            image_filename=filename,
            latitude=float(latitude),
            longitude=float(longitude)
        )

        db.session.add(report)
        db.session.commit()

        return jsonify({"message": "Report submitted successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 👉 Get All Issues (for map)
@app.route("/api/issues", methods=["GET"])
def get_issues():
    try:
        reports = Report.query.order_by(Report.created_at.desc()).all()

        data = []
        for r in reports:
            data.append({
                "id": r.id,
                "category": r.category,
                "description": r.description,
                "image": f"/uploads/{r.image_filename}",
                "latitude": r.latitude,
                "longitude": r.longitude,
                "upvotes": r.upvotes,
                "status": r.status,
                "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
            })

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 👉 Upvote
@app.route("/upvote/<int:id>", methods=["POST"])
def upvote(id):
    try:
        report = Report.query.get_or_404(id)
        report.upvotes += 1
        db.session.commit()
        return jsonify({"message": "Upvoted successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 👉 Update Status
@app.route("/status/<int:id>", methods=["POST"])
def update_status(id):
    try:
        status = request.json.get("status")

        if status not in ["pending", "resolved"]:
            return jsonify({"error": "Invalid status"}), 400

        report = Report.query.get_or_404(id)
        report.status = status
        db.session.commit()

        return jsonify({"message": "Status updated"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 👉 Serve Uploaded Images
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# -----------------------
# Run App (Render Ready)
# -----------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
=======
from flask import Flask, request, jsonify, render_template, redirect, session, send_from_directory
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "secret123"
app.config['UPLOAD_FOLDER'] = 'uploads'

# -------- DATABASE --------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        password TEXT
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY,
        category TEXT,
        description TEXT,
        lat REAL,
        lng REAL,
        image TEXT,
        votes INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending'
    )''')

    conn.commit()
    conn.close()

init_db()

# -------- ROUTES --------
@app.route('/')
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/do_login', methods=['POST'])
def do_login():
    u = request.form['username']
    p = request.form['password']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (u,p))
    user = c.fetchone()
    conn.close()

    if user:
        session["user"] = u
        return redirect("/")
    return "Login Failed"

@app.route('/do_register', methods=['POST'])
def do_register():
    u = request.form['username']
    p = request.form['password']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
    conn.commit()
    conn.close()

    return redirect("/login")

# -------- ISSUE SYSTEM --------
@app.route('/report', methods=['POST'])
def report():
    category = request.form['category']
    description = request.form['description']
    lat = request.form['lat']
    lng = request.form['lng']

    file = request.files['image']
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO issues (category,description,lat,lng,image) VALUES (?,?,?,?,?)",
              (category,description,lat,lng,filename))
    conn.commit()
    conn.close()

    return jsonify({"msg":"done"})

@app.route('/issues')
def issues():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM issues ORDER BY votes DESC")
    data = c.fetchall()
    conn.close()

    result=[]
    for i in data:
        result.append({
            "id":i[0],
            "category":i[1],
            "description":i[2],
            "lat":i[3],
            "lng":i[4],
            "image":i[5],
            "votes":i[6],
            "status":i[7]
        })
    return jsonify(result)

@app.route('/upvote/<int:id>', methods=['POST'])
def upvote(id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE issues SET votes=votes+1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"msg":"ok"})

@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    status = request.json['status']

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE issues SET status=? WHERE id=?", (status,id))
    conn.commit()
    conn.close()

    return jsonify({"msg":"updated"})

@app.route('/admin')
def admin():
    return render_template("admin.html")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# -------- RUN --------
if __name__ == "__main__":
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.run(host="0.0.0.0", port=5000)
>>>>>>> 20a623f (first commit)
