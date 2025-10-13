# app.py

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from sqlalchemy import func # Import func untuk aggregate

app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi Ekstensi
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Halaman yang dituju jika belum login

# --- Models Database ---

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    # Role: 'user' atau 'admin'
    role = db.Column(db.String(10), default='user') 
    
    # Relasi ke tabel analisis
    analyses_tebu = db.relationship('TebuAnalysis', backref='user', lazy='dynamic')
    analyses_jagung = db.relationship('JagungAnalysis', backref='user', lazy='dynamic')
    analyses_padi = db.relationship('PadiAnalysis', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Model untuk Analisis Tebu
class TebuAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=db.func.now())
    lokasi_sawah = db.Column(db.String(100))
    # Biaya
    harga_perawatan_total = db.Column(db.Float)
    # Kalkulasi
    luas_kebun = db.Column(db.Float)
    luas_1_hektar = db.Column(db.Float)
    luas_efektif = db.Column(db.Float)
    pkp = db.Column(db.Integer)
    panjang_leng = db.Column(db.Float)
    jml_leng = db.Column(db.Float)
    jml_btng_10m = db.Column(db.Float)
    tinggi_btng = db.Column(db.Float)
    berat_btng_m = db.Column(db.Float)
    harga_tebu_kg = db.Column(db.Float)
    # Hasil
    protas_tebu_hektar = db.Column(db.Float)
    protas_tebu_kebun = db.Column(db.Float)
    nilai_tebu = db.Column(db.Float)
    nilai_netto = db.Column(db.Float)

# Model untuk Analisis Jagung
class JagungAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=db.func.now())
    lokasi_sawah = db.Column(db.String(100))
    varietas = db.Column(db.String(100))
    # Biaya (disederhanakan untuk contoh)
    biaya_kebun = db.Column(db.Float) # Total Biaya Produksi
    # Kalkulasi
    kg_jagung_glondong_ubinan = db.Column(db.Float)
    kg_jagung_glondong_m2 = db.Column(db.Float)
    rapaksi = db.Column(db.Float)
    kg_jagung_pipil_m2 = db.Column(db.Float)
    luas_baku = db.Column(db.Float)
    luas_efektif = db.Column(db.Float)
    harga_jagung_kg = db.Column(db.Float)
    # Hasil
    protas_jagung_kering_kg = db.Column(db.Float)
    nilai_protas_bruto = db.Column(db.Float)
    nilai_protas_netto = db.Column(db.Float)

# Model untuk Analisis Padi
class PadiAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=db.func.now())
    lokasi_sawah = db.Column(db.String(100))
    varietas = db.Column(db.String(100))
    # Biaya
    biaya_kebun = db.Column(db.Float) # Harga Perawatan Total
    # Kalkulasi
    kg_gabah_ubinan = db.Column(db.Float)
    kg_gabah_m2 = db.Column(db.Float)
    luas_baku = db.Column(db.Float)
    luas_efektif = db.Column(db.Float)
    harga_padi_kg = db.Column(db.Float)
    # Hasil
    protas_padi_kg = db.Column(db.Float)
    nilai_protas_bruto = db.Column(db.Float)
    nilai_protas_netto = db.Column(db.Float)


# --- Routes Aplikasi ---

# @app.before_first_request dihapus dan logikanya dipindah ke blok if __name__ == '__main__':

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


# --- Autentikasi ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email sudah terdaftar.', 'danger')
            return redirect(url_for('register'))
        
        new_user = User(email=email, name=name, role='user') # Default role user
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('Pendaftaran berhasil! Silakan Login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Selamat datang, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Email atau Kata Sandi salah.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- Dashboard & Menu Analisis ---

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# --- Analisis Tebu ---

@app.route('/analisis/tebu', methods=['GET', 'POST'])
@login_required
def tebu_analisis():
    hasil = None
    if request.method == 'POST':
        try:
            # Ambil Input
            lokasi_sawah = request.form.get('lokasi_sawah')
            harga_perawatan_total = float(request.form.get('harga_perawatan_total', 0))
            luas_kebun = float(request.form.get('luas_kebun', 0))
            luas_1_hektar = float(request.form.get('luas_1_hektar', 10000)) # Default 10000 M2
            pkp = int(request.form.get('pkp', 0))
            jml_btng_10m = float(request.form.get('jml_btng_10m', 0))
            tinggi_btng = float(request.form.get('tinggi_btng', 0))
            berat_btng_m = float(request.form.get('berat_btng_m', 0))
            harga_tebu_kg = float(request.form.get('harga_tebu_kg', 0))

            # Kalkulasi
            luas_efektif = 0.99 * luas_1_hektar
            
            # Panjang Leng
            if pkp == 110:
                panjang_leng = 9000.0
            elif pkp == 85:
                panjang_leng = 11650.0 # Menggunakan 11650.0 sesuai asumsi di instruksi
            else:
                panjang_leng = 0.0 # Default jika PKP lain

            jml_leng = panjang_leng / 10.0
            
            # Protas Tebu per Hektar (kg)
            protas_tebu_hektar = berat_btng_m * tinggi_btng * jml_btng_10m * jml_leng
            
            # Protas Tebu Kebun (kg)
            if luas_1_hektar != 0:
                protas_tebu_kebun = (luas_kebun / luas_1_hektar) * protas_tebu_hektar
            else:
                protas_tebu_kebun = 0
                
            # Nilai Tebu (Rp)
            nilai_tebu = protas_tebu_kebun * harga_tebu_kg
            
            # Nilai Netto (Keuntungan Bersih)
            nilai_netto = nilai_tebu - harga_perawatan_total

            hasil = {
                'lokasi_sawah': lokasi_sawah,
                'luas_efektif': luas_efektif,
                'panjang_leng': panjang_leng,
                'jml_leng': jml_leng,
                'protas_tebu_hektar': protas_tebu_hektar,
                'protas_tebu_kebun': protas_tebu_kebun,
                'nilai_tebu': nilai_tebu,
                'nilai_netto': nilai_netto
            }
            
            # Simpan ke Database
            new_analysis = TebuAnalysis(
                user_id=current_user.id,
                lokasi_sawah=lokasi_sawah,
                harga_perawatan_total=harga_perawatan_total,
                luas_kebun=luas_kebun,
                luas_1_hektar=luas_1_hektar,
                luas_efektif=luas_efektif,
                pkp=pkp,
                panjang_leng=panjang_leng,
                jml_leng=jml_leng,
                jml_btng_10m=jml_btng_10m,
                tinggi_btng=tinggi_btng,
                berat_btng_m=berat_btng_m,
                harga_tebu_kg=harga_tebu_kg,
                protas_tebu_hektar=protas_tebu_hektar,
                protas_tebu_kebun=protas_tebu_kebun,
                nilai_tebu=nilai_tebu,
                nilai_netto=nilai_netto
            )
            db.session.add(new_analysis)
            db.session.commit()
            flash('Kalkulasi berhasil disimpan!', 'success')
            
        except ValueError:
            flash('Input harus berupa angka yang valid.', 'danger')
            
    # Tampilkan riwayat analisis pengguna saat ini
    riwayat = current_user.analyses_tebu.order_by(TebuAnalysis.timestamp.desc()).limit(10).all()
    
    return render_template('tebu_analisis.html', hasil=hasil, riwayat=riwayat)

# --- Analisis Jagung ---

@app.route('/analisis/jagung', methods=['GET', 'POST'])
@login_required
def jagung_analisis():
    hasil = None
    if request.method == 'POST':
        try:
            # Ambil Input
            lokasi_sawah = request.form.get('lokasi_sawah')
            varietas = request.form.get('varietas')
            biaya_kebun = float(request.form.get('biaya_kebun', 0)) # Diisi Total Biaya Produksi
            kg_jagung_glondong_ubinan = float(request.form.get('kg_jagung_glondong_ubinan', 0))
            rapaksi = float(request.form.get('rapaksi', 60)) / 100.0 # Input persen, diubah ke desimal
            luas_baku = float(request.form.get('luas_baku', 0))
            harga_jagung_kg = float(request.form.get('harga_jagung_kg', 0))

            # Kalkulasi
            kg_jagung_glondong_m2 = kg_jagung_glondong_ubinan / 6.25
            kg_jagung_pipil_m2 = (1.0 - rapaksi) * kg_jagung_glondong_m2
            luas_efektif = 0.92 * luas_baku
            
            protas_jagung_kering_kg = kg_jagung_pipil_m2 * luas_efektif
            nilai_protas_bruto = protas_jagung_kering_kg * harga_jagung_kg
            nilai_protas_netto = nilai_protas_bruto - biaya_kebun

            hasil = {
                'lokasi_sawah': lokasi_sawah,
                'varietas': varietas,
                'kg_jagung_glondong_m2': kg_jagung_glondong_m2,
                'kg_jagung_pipil_m2': kg_jagung_pipil_m2,
                'luas_efektif': luas_efektif,
                'protas_jagung_kering_kg': protas_jagung_kering_kg,
                'nilai_protas_bruto': nilai_protas_bruto,
                'nilai_protas_netto': nilai_protas_netto
            }

            # Simpan ke Database
            new_analysis = JagungAnalysis(
                user_id=current_user.id,
                lokasi_sawah=lokasi_sawah,
                varietas=varietas,
                biaya_kebun=biaya_kebun,
                kg_jagung_glondong_ubinan=kg_jagung_glondong_ubinan,
                kg_jagung_glondong_m2=kg_jagung_glondong_m2,
                rapaksi=rapaksi,
                kg_jagung_pipil_m2=kg_jagung_pipil_m2,
                luas_baku=luas_baku,
                luas_efektif=luas_efektif,
                harga_jagung_kg=harga_jagung_kg,
                protas_jagung_kering_kg=protas_jagung_kering_kg,
                nilai_protas_bruto=nilai_protas_bruto,
                nilai_protas_netto=nilai_protas_netto
            )
            db.session.add(new_analysis)
            db.session.commit()
            flash('Kalkulasi berhasil disimpan!', 'success')

        except ValueError:
            flash('Input harus berupa angka yang valid.', 'danger')

    riwayat = current_user.analyses_jagung.order_by(JagungAnalysis.timestamp.desc()).limit(10).all()

    return render_template('jagung_analisis.html', hasil=hasil, riwayat=riwayat)

# --- Analisis Padi ---

@app.route('/analisis/padi', methods=['GET', 'POST'])
@login_required
def padi_analisis():
    hasil = None
    if request.method == 'POST':
        try:
            # Ambil Input
            lokasi_sawah = request.form.get('lokasi_sawah')
            varietas = request.form.get('varietas')
            biaya_kebun = float(request.form.get('biaya_kebun', 0)) # Harga Perawatan Total
            kg_gabah_ubinan = float(request.form.get('kg_gabah_ubinan', 0))
            luas_baku = float(request.form.get('luas_baku', 0))
            harga_padi_kg = float(request.form.get('harga_padi_kg', 0))

            # Kalkulasi
            kg_gabah_m2 = kg_gabah_ubinan / 6.25
            luas_efektif = 0.92 * luas_baku
            
            protas_padi_kg = kg_gabah_m2 * luas_efektif
            nilai_protas_bruto = protas_padi_kg * harga_padi_kg
            nilai_protas_netto = nilai_protas_bruto - biaya_kebun

            hasil = {
                'lokasi_sawah': lokasi_sawah,
                'varietas': varietas,
                'kg_gabah_m2': kg_gabah_m2,
                'luas_efektif': luas_efektif,
                'protas_padi_kg': protas_padi_kg,
                'nilai_protas_bruto': nilai_protas_bruto,
                'nilai_protas_netto': nilai_protas_netto
            }

            # Simpan ke Database
            new_analysis = PadiAnalysis(
                user_id=current_user.id,
                lokasi_sawah=lokasi_sawah,
                varietas=varietas,
                biaya_kebun=biaya_kebun,
                kg_gabah_ubinan=kg_gabah_ubinan,
                kg_gabah_m2=kg_gabah_m2,
                luas_baku=luas_baku,
                luas_efektif=luas_efektif,
                harga_padi_kg=harga_padi_kg,
                protas_padi_kg=protas_padi_kg,
                nilai_protas_bruto=nilai_protas_bruto,
                nilai_protas_netto=nilai_protas_netto
            )
            db.session.add(new_analysis)
            db.session.commit()
            flash('Kalkulasi berhasil disimpan!', 'success')

        except ValueError:
            flash('Input harus berupa angka yang valid.', 'danger')
            
    riwayat = current_user.analyses_padi.order_by(PadiAnalysis.timestamp.desc()).limit(10).all()

    return render_template('padi_analisis.html', hasil=hasil, riwayat=riwayat)

# --- Admin Data Access (Hanya untuk Admin) ---

@app.route('/admin/data')
@login_required
def admin_data():
    if current_user.role != 'admin':
        flash('Akses ditolak. Hanya Admin yang dapat mengakses.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Ambil semua data dari semua analisis
    all_tebu = TebuAnalysis.query.all()
    all_jagung = JagungAnalysis.query.all()
    all_padi = PadiAnalysis.query.all()
    
    # Contoh data agregat (total keuntungan)
    total_netto_tebu = db.session.query(func.sum(TebuAnalysis.nilai_netto)).scalar() or 0
    total_netto_jagung = db.session.query(func.sum(JagungAnalysis.nilai_protas_netto)).scalar() or 0
    total_netto_padi = db.session.query(func.sum(PadiAnalysis.nilai_protas_netto)).scalar() or 0
    
    return render_template('admin_data.html', 
                           tebu=all_tebu, jagung=all_jagung, padi=all_padi,
                           total_tebu=total_netto_tebu, total_jagung=total_netto_jagung, total_padi=total_netto_padi)

# --- PENYIAPAN APLIKASI AWAL (Memperbaiki AttributeError) ---

def create_tables_and_admin():
    """Membuat tabel database dan user admin jika belum ada, dalam konteks aplikasi."""
    with app.app_context():
        # 1. Buat semua tabel (database.db)
        db.create_all()
        
        # 2. Buat user Admin pertama jika belum ada
        if not User.query.filter_by(role='admin').first():
            admin_user = User(email='admin@app.com', name='Administrator', role='admin')
            admin_user.set_password('adminpass123') 
            db.session.add(admin_user)
            db.session.commit()
            print("INFO: Admin user created (admin@app.com / adminpass123)")

if __name__ == '__main__':
    # Panggil fungsi setup di sini
    create_tables_and_admin() 
    
    # Jalankan server Flask
    app.run(debug=True)