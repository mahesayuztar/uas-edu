from flask import Flask, render_template, flash, request, redirect, url_for
from models import db, User, DimSiswa, DimBuku, FactAktivitasBaca
from datetime import datetime
from sqlalchemy import func

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
    # --- 1. KPI CARDS (Query Real-time ke Database) ---
    total_siswa = DimSiswa.query.count()
    total_buku = DimBuku.query.count()
    
    # Menghitung Total Durasi (Sum)
    # Menggunakan func.sum dari SQLAlchemy untuk menjumlahkan kolom
    total_durasi_query = db.session.query(func.sum(FactAktivitasBaca.durasi_menit)).scalar()
    total_durasi_jam = round(total_durasi_query / 60, 1) if total_durasi_query else 0
    
    # Menghitung Total Halaman
    total_halaman = db.session.query(func.sum(FactAktivitasBaca.halaman_selesai)).scalar() or 0

    # --- 2. QUERY UNTUK GRAFIK ---

    # A. Top 5 Buku Terpopuler
    # Logic: Join Buku & Fact -> Group By Judul -> Count Fact -> Urutkan Terbanyak -> Ambil 5
    top_buku_query = db.session.query(
        DimBuku.judul_buku, 
        func.count(FactAktivitasBaca.id_fact).label('jumlah_baca')
    ).join(FactAktivitasBaca, DimBuku.id_buku == FactAktivitasBaca.id_buku)\
    .group_by(DimBuku.judul_buku)\
    .order_by(func.count(FactAktivitasBaca.id_fact).desc())\
    .limit(5).all()

    # Pisahkan hasil query menjadi dua list (Label dan Data) untuk Chart.js
    chart_buku_labels = [b.judul_buku for b in top_buku_query]
    chart_buku_data = [b.jumlah_baca for b in top_buku_query]

    # B. Partisipasi per Kelas
    # Logic: Join Siswa & Fact -> Group By Kelas -> Sum Durasi
    kelas_query = db.session.query(
        DimSiswa.kelas,
        func.sum(FactAktivitasBaca.durasi_menit)
    ).join(FactAktivitasBaca, DimSiswa.id_siswa == FactAktivitasBaca.id_siswa)\
    .group_by(DimSiswa.kelas)\
    .order_by(DimSiswa.kelas).all()

    chart_kelas_labels = [f"Kelas {k.kelas}" for k in kelas_query]
    chart_kelas_data = [int(k[1]) for k in kelas_query]

    # C. Trend Aktivitas Harian
    # Logic: Group By Tanggal Baca -> Sum Durasi
    trend_query = db.session.query(
        FactAktivitasBaca.tanggal_baca,
        func.sum(FactAktivitasBaca.durasi_menit)
    ).group_by(FactAktivitasBaca.tanggal_baca)\
    .order_by(FactAktivitasBaca.tanggal_baca).all()

    # Format tanggal menjadi string 'YYYY-MM-DD' agar bisa dibaca grafik
    chart_trend_labels = [t.tanggal_baca.strftime('%Y-%m-%d') for t in trend_query]
    chart_trend_data = [int(t[1]) for t in trend_query]

    # Kirim semua data ke dashboard.html
    return render_template('dashboard_real.html', 
                        kpi={
                            'siswa': total_siswa, 
                            'buku': total_buku, 
                            'durasi': total_durasi_jam,
                            'halaman': total_halaman
                        },
                        chart_buku={'labels': chart_buku_labels, 'data': chart_buku_data},
                        chart_kelas={'labels': chart_kelas_labels, 'data': chart_kelas_data},
                        chart_trend={'labels': chart_trend_labels, 'data': chart_trend_data}
                        )

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