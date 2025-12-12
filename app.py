from flask import Flask, render_template, flash, request, redirect, url_for
from models import db, User, DimSiswa, DimBuku, FactAktivitasBaca
from datetime import datetime

app = Flask(__name__)

# --- CONFIGURATION ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost:5432/literasi_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'kunci_rahasia_literasi_2024'

# --- CONNECTING DB WITH APP ---
db.init_app(app)

# --- ROUTE ---
@app.route('/')
def home():
    return render_template('dashboard.html')

@app.route('/input_data', methods=['GET', 'POST'])
def input_data():
    # --- POST METHOD --- 
    if request.method == 'POST':
        try:
            id_siswa_input = request.form['id_siswa']
            id_buku_input = request.form['id_buku']
            tanggal_input = request.form['tanggal_baca']
            durasi_input = request.form['durasi_menit']
            halaman_input = request.form['halaman_selesai']
            
            aktivitas_baru = FactAktivitasBaca(
                id_siswa=id_siswa_input,
                id_buku=id_buku_input,
                tanggal_baca=datetime.strptime(tanggal_input, '%Y-%m-%d'), 
                durasi_menit=durasi_input,
                halaman_selesai=halaman_input
            )
            
            db.session.add(aktivitas_baru)
            db.session.commit()
            
            flash('Data aktivitas berhasil disimpan!', 'success')
            return redirect(url_for('input_data'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Terjadi kesalahan: {str(e)}', 'danger')
            
    # --- GET METHOD ---
    list_siswa = DimSiswa.query.order_by(DimSiswa.nama_lengkap).all()
    list_buku = DimBuku.query.order_by(DimBuku.judul_buku).all()

    return render_template('input.html', 
                        students=list_siswa, 
                        books=list_buku)

@app.route('/buku_table')
def buku_table():
    books = DimBuku.query.all()
    return render_template('buku_table.html', books = books)

@app.route('/siswa_table')
def siswa_table():
    students = DimSiswa.query.all()
    return render_template('siswa_table.html', students = students)

@app.route('/aktivitasbaca_table')
def aktivitasbaca_table():
    activity = FactAktivitasBaca.query.all()
    return render_template('aktivitasbaca_table.html', activity = activity)

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/login')
def login():
    return render_template('login.html')

# --- MAIN ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)