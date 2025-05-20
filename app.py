from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Konfigurasi Database SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trouble_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
db = SQLAlchemy(app)

app.secret_key = 'trouble_secret'

# Membuat model untuk tabel masalah mobil
class Problem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chassis = db.Column(db.String(100), nullable=False)
    engine = db.Column(db.String(100), nullable=False)
    deskripsi = db.Column(db.String(200), nullable=False)
    test_level = db.Column(db.String(100), nullable=False)
    actual_value = db.Column(db.String(100), nullable=False)
    solusi = db.Column(db.String(200), nullable=False)
    files = db.Column(db.String(300), nullable=True)  # Menyimpan nama file yang di-upload

    def __repr__(self):
        return f'<Problem {self.chassis} - {self.engine}>'

# Fungsi untuk memeriksa ekstensi file yang di-upload
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Rute untuk melayani file yang di-upload
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Route untuk logout
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('role', None)
    return redirect(url_for('login'))

# Route untuk menghapus data masalah
@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_problem(id):
    if session['role'] != 'admin':  # Hanya admin yang bisa menghapus data
        return redirect(url_for('dashboard'))

    # Menghapus data masalah dari database tanpa konfirmasi
    problem_to_delete = Problem.query.get_or_404(id)
    db.session.delete(problem_to_delete)
    db.session.commit()  # Simpan perubahan ke database

    return redirect(url_for('dashboard'))

# Route untuk konfirmasi penghapusan
@app.route('/confirm_delete/<int:id>', methods=['GET', 'POST'])
def confirm_delete(id):
    if session['role'] != 'admin':  # Hanya admin yang bisa menghapus data
        return redirect(url_for('dashboard'))

    problem_to_delete = Problem.query.get_or_404(id)

    if request.method == 'POST':
        if 'yes' in request.form:
            # Jika user klik 'Ya', hapus data
            db.session.delete(problem_to_delete)
            db.session.commit()  # Simpan perubahan ke database
            return redirect(url_for('dashboard'))
        else:
            # Jika user klik 'Tidak', kembali ke dashboard
            return redirect(url_for('dashboard'))

    return render_template('confirm_delete.html', problem=problem_to_delete)

# Login data untuk 2 role: admin dan guest
USER_CREDENTIALS = {
    'admin': {'username': 'admin', 'password': 'adminpass', 'role': 'admin'},
    'guest': {'username': 'guest', 'password': 'guestpass', 'role': 'guest'}
}

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Cek jika user terdaftar dan password benar
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username]['password'] == password:
            session['logged_in'] = True
            session['role'] = USER_CREDENTIALS[username]['role']
            return redirect(url_for('dashboard'))
        else:
            return "Login Failed! Invalid credentials."
    
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    chassis_search = request.args.get('chassis', '')
    engine_search = request.args.get('engine', '')
    problem_search = request.args.get('problem', '')

    problems = Problem.query.all()  # Mengambil semua data masalah dari database

    # Filter data berdasarkan pencarian
    if chassis_search:
        problems = [problem for problem in problems if chassis_search.lower() in problem.chassis.lower()]
    if engine_search:
        problems = [problem for problem in problems if engine_search.lower() in problem.engine.lower()]
    if problem_search:
        problems = [problem for problem in problems if problem_search.lower() in problem.deskripsi.lower()]

    if session['role'] == 'admin' and request.method == 'POST':
        # Ambil data form untuk menambah data
        chassis = request.form['chassis']
        engine = request.form['engine']
        deskripsi = request.form['deskripsi']
        test_level = request.form['test_level']
        actual_value = request.form['actual_value']
        solusi = request.form['solusi']
        uploaded_files = []

        # Simpan file yang di-upload
        for file in request.files.getlist('files'):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_files.append(filename)

        # Menambahkan data masalah baru ke database
        new_problem = Problem(
            chassis=chassis,
            engine=engine,
            deskripsi=deskripsi,
            test_level=test_level,
            actual_value=actual_value,
            solusi=solusi,
            files=",".join(uploaded_files)  # Menyimpan file yang di-upload
        )
        db.session.add(new_problem)
        db.session.commit()  # Simpan perubahan ke database

        # Redirect kembali ke dashboard setelah menambah data
        return redirect(url_for('dashboard'))

    return render_template('dashboard.html', problems=problems)

# Route untuk menambah data masalah
@app.route('/add_data', methods=['GET', 'POST'])
def add_data():
    if 'logged_in' not in session or session['role'] != 'admin':  # Hanya admin yang bisa menambah data
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Ambil data form untuk tambah data
        chassis = request.form['chassis']
        engine = request.form['engine']
        deskripsi = request.form['deskripsi']
        test_level = request.form['test_level']
        actual_value = request.form['actual_value']
        solusi = request.form['solusi']
        uploaded_files = []

        # Simpan file yang di-upload
        for file in request.files.getlist('files'):
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                uploaded_files.append(filename)

        # Menambahkan data masalah baru ke database
        new_problem = Problem(
            chassis=chassis,
            engine=engine,
            deskripsi=deskripsi,
            test_level=test_level,
            actual_value=actual_value,
            solusi=solusi,
            files=",".join(uploaded_files)  # Menyimpan file yang di-upload
        )
        db.session.add(new_problem)
        db.session.commit()  # Simpan perubahan ke database

        return redirect(url_for('dashboard'))

    return render_template('add_data.html')  # Halaman form tambah data

# Membuat tabel jika belum ada (dengan app context)
with app.app_context():
    db.create_all()  # Membuat tabel jika belum ada

if __name__ == '__main__':
    app.run(debug=True)
