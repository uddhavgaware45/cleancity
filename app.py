import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)

# ================= CONFIG =================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(BASE_DIR, 'issues.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= MODEL ==================
class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    image = db.Column(db.String(200))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    upvotes = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="pending")

# ================= INIT DB =================
@app.before_first_request
def create_tables():
    db.create_all()

# ================= ROUTES =================

@app.route('/')
def index():
    issues = Issue.query.order_by(Issue.upvotes.desc()).all()
    return render_template('index.html', issues=issues)

@app.route('/report', methods=['GET', 'POST'])
def report():
    if request.method == 'POST':
        try:
            category = request.form['category']
            description = request.form['description']
            lat = float(request.form['lat'])
            lng = float(request.form['lng'])

            file = request.files.get('image')
            filename = None

            if file and file.filename != "":
                filename = secure_filename(file.filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            issue = Issue(
                category=category,
                description=description,
                image=filename,
                lat=lat,
                lng=lng
            )

            db.session.add(issue)
            db.session.commit()

            return redirect(url_for('index'))

        except Exception as e:
            return f"Error: {str(e)}"

    return render_template('report.html')

# Serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# API for map
@app.route('/api/issues')
def get_issues():
    issues = Issue.query.all()
    return jsonify([
        {
            "id": i.id,
            "category": i.category,
            "description": i.description,
            "image": i.image,
            "lat": i.lat,
            "lng": i.lng,
            "upvotes": i.upvotes,
            "status": i.status
        } for i in issues
    ])

# Upvote
@app.route('/upvote/<int:id>', methods=['POST'])
def upvote(id):
    issue = Issue.query.get_or_404(id)
    issue.upvotes += 1
    db.session.commit()
    return redirect(url_for('index'))

# Change status (optional)
@app.route('/status/<int:id>/<new_status>')
def change_status(id, new_status):
    issue = Issue.query.get_or_404(id)
    issue.status = new_status
    db.session.commit()
    return redirect(url_for('index'))

# ================= IMPORTANT =================
# ❌ DO NOT ADD app.run()
# Render uses gunicorn, so no main block needed