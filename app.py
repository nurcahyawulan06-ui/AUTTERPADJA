# app.py

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_pymongo import PyMongo # BARU: Mengganti Flask-SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId # BARU: Untuk mengelola ID MongoDB
from config import Config
from datetime import datetime
import os

app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi MongoDB (akan mengambil MONGO_URI dari config.py)
mongo = PyMongo(app) 
# Koleksi utama
USERS = mongo.db.users
TEBU = mongo.db.tebu_analyses
JAGUNG = mongo.db.jagung_analyses
PADI = mongo.db.padi_analyses

# Inisialisasi LoginManager
login_manager = LoginManager(app)
login_manager.login_view = 'login' 

# --- Model & User Loader (Disesuaikan untuk MongoDB) ---

# Class User harus tetap ada, tetapi sekarang hanya berfungsi sebagai wrapper data
class User(UserMixin):
    def __init__(self, user_data):
        # ID MongoDB adalah ObjectId, disimpan sebagai atribut id
        self.id = user_data.get('_id') 
        self.email = user_data.get('email')
        self.name = user_data.get('name')
        self.password_hash = user_data.get('password_hash')
        self.role = user_data.get('role', 'user')

    def get_id(self):
        # Harus mengembalikan ID dalam bentuk string untuk Flask-Login
        return str(self.id)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    # Mencari user berdasarkan ObjectId
    try:
        user_data = USERS.find_one({"_id": ObjectId(user_id)})
        if user_data:
            return User(user_data)
    except Exception:
        # Menangani kasus jika user_id tidak valid
        pass
    return None

def get_user_by_email(email):
    """Mencari user berdasarkan email."""
    user_data = USERS.find_one({"email": email})
    if user_data:
        return User(user_data)
    return None

# --- Routes Aplikasi ---

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
        
        # GANTI: User.query.filter_by
        if get_user_by_email(email): 
            flash('Email sudah terdaftar.', 'danger')
            return redirect(url_for('register'))
        
        # Simpan ke MongoDB (users collection)
        user_data = {
            "email": email,
            "name": name,
            "password_hash": generate_password_hash(password),
            "role": "user",
            "created_at": datetime.utcnow()
        }
        USERS.insert_one(user_data)
        
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
        
        user = get_user_by_email(email)
        
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
            # Ambil Input (sama dengan versi SQLAlchemy)
            lokasi_sawah = request.form.get('lokasi_sawah')
            harga_perawatan_total = float(request.form.get('harga_perawatan_total', 0))
            luas_kebun = float(request.form.get('luas_kebun', 0))
            luas_1_hektar = float(request.form.get('luas_1_hektar', 10000)) # Default 10000 M2
            pkp = int(request.form.get('pkp', 0))
            jml_btng_10m = float(request.form.get('jml_btng_10m', 0))
            tinggi_btng = float(request.form.get('tinggi_btng', 0))
            berat_btng_m = float(request.form.get('berat_btng_m', 0))
            harga_tebu_kg = float(request.form.get('harga_tebu_kg', 0))

            # Kalkulasi (Logika tetap sama)
            luas_efektif = 0.99 * luas_1_hektar
            
            if pkp == 110:
                panjang_leng = 9000.0
            elif pkp == 85:
                panjang_leng = 11650.0 
            else:
                panjang_leng = 0.0 

            jml_leng = panjang_leng / 10.0
            protas_tebu_hektar = berat_btng_m * tinggi_btng * jml_btng_10m * jml_leng
            
            if luas_1_hektar != 0:
                protas_tebu_kebun = (luas_kebun / luas_1_hektar) * protas_tebu_hektar
            else:
                protas_tebu_kebun = 0
                
            nilai_tebu = protas_tebu_kebun * harga_tebu_kg
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
            
            # Simpan ke Database MongoDB (Tebu Collection)
            analysis_data = {
                "user_id": current_user.id, # Menyimpan ObjectId user
                "timestamp": datetime.utcnow(),
                "lokasi_sawah": lokasi_sawah,
                "harga_perawatan_total": harga_perawatan_total,
                "luas_kebun": luas_kebun,
                "luas_1_hektar": luas_1_hektar,
                "luas_efektif": luas_efektif,
                "pkp": pkp,
                "panjang_leng": panjang_leng,
                "jml_leng": jml_leng,
                "jml_btng_10m": jml_btng_10m,
                "tinggi_btng": tinggi_btng,
                "berat_btng_m": berat_btng_m,
                "harga_tebu_kg": harga_tebu_kg,
                "protas_tebu_hektar": protas_tebu_hektar,
                "protas_tebu_kebun": protas_tebu_kebun,
                "nilai_tebu": nilai_tebu,
                "nilai_netto": nilai_netto
            }
            TEBU.insert_one(analysis_data) # GANTI: db.session.add/commit
            flash('Kalkulasi berhasil disimpan!', 'success')
            
        except ValueError:
            flash('Input harus berupa angka yang valid.', 'danger')
            
    # Tampilkan riwayat analisis pengguna saat ini
    # GANTI: current_user.analyses_tebu.order_by(...).limit(10).all()
    # Mencari data dengan user_id yang sama dan mengurutkannya
    riwayat = list(TEBU.find({"user_id": current_user.id}).sort("timestamp", -1).limit(10))
    
    return render_template('tebu_analisis.html', hasil=hasil, riwayat=riwayat)

# --- Analisis Jagung (Diubah untuk MongoDB) ---

@app.route('/analisis/jagung', methods=['GET', 'POST'])
@login_required
def jagung_analisis():
    hasil = None
    if request.method == 'POST':
        try:
            # Ambil Input
            lokasi_sawah = request.form.get('lokasi_sawah')
            varietas = request.form.get('varietas')
            biaya_kebun = float(request.form.get('biaya_kebun', 0)) 
            kg_jagung_glondong_ubinan = float(request.form.get('kg_jagung_glondong_ubinan', 0))
            rapaksi = float(request.form.get('rapaksi', 60)) / 100.0 
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
                'protas_jagung_kering_kg': protas_jagung_kering_kg,
                'nilai_protas_netto': nilai_protas_netto
            }

            # Simpan ke Database MongoDB (Jagung Collection)
            analysis_data = {
                "user_id": current_user.id,
                "timestamp": datetime.utcnow(),
                "lokasi_sawah": lokasi_sawah,
                "varietas": varietas,
                "biaya_kebun": biaya_kebun,
                "kg_jagung_glondong_ubinan": kg_jagung_glondong_ubinan,
                "kg_jagung_glondong_m2": kg_jagung_glondong_m2,
                "rapaksi": rapaksi,
                "kg_jagung_pipil_m2": kg_jagung_pipil_m2,
                "luas_baku": luas_baku,
                "luas_efektif": luas_efektif,
                "harga_jagung_kg": harga_jagung_kg,
                "protas_jagung_kering_kg": protas_jagung_kering_kg,
                "nilai_protas_bruto": nilai_protas_bruto,
                "nilai_protas_netto": nilai_protas_netto
            }
            JAGUNG.insert_one(analysis_data)
            flash('Kalkulasi berhasil disimpan!', 'success')

        except ValueError:
            flash('Input harus berupa angka yang valid.', 'danger')

    riwayat = list(JAGUNG.find({"user_id": current_user.id}).sort("timestamp", -1).limit(10))

    return render_template('jagung_analisis.html', hasil=hasil, riwayat=riwayat)

# --- Analisis Padi (Diubah untuk MongoDB) ---

@app.route('/analisis/padi', methods=['GET', 'POST'])
@login_required
def padi_analisis():
    hasil = None
    if request.method == 'POST':
        try:
            # Ambil Input
            lokasi_sawah = request.form.get('lokasi_sawah')
            varietas = request.form.get('varietas')
            biaya_kebun = float(request.form.get('biaya_kebun', 0)) 
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
                'protas_padi_kg': protas_padi_kg,
                'nilai_protas_netto': nilai_protas_netto
            }

            # Simpan ke Database MongoDB (Padi Collection)
            analysis_data = {
                "user_id": current_user.id,
                "timestamp": datetime.utcnow(),
                "lokasi_sawah": lokasi_sawah,
                "varietas": varietas,
                "biaya_kebun": biaya_kebun,
                "kg_gabah_ubinan": kg_gabah_ubinan,
                "kg_gabah_m2": kg_gabah_m2,
                "luas_baku": luas_baku,
                "luas_efektif": luas_efektif,
                "harga_padi_kg": harga_padi_kg,
                "protas_padi_kg": protas_padi_kg,
                "nilai_protas_bruto": nilai_protas_bruto,
                "nilai_protas_netto": nilai_protas_netto
            }
            PADI.insert_one(analysis_data)
            flash('Kalkulasi berhasil disimpan!', 'success')

        except ValueError:
            flash('Input harus berupa angka yang valid.', 'danger')
            
    riwayat = list(PADI.find({"user_id": current_user.id}).sort("timestamp", -1).limit(10))

    return render_template('padi_analisis.html', hasil=hasil, riwayat=riwayat)

# --- Admin Data Access (Hanya untuk Admin) ---

@app.route('/admin/data')
@login_required
def admin_data():
    if current_user.role != 'admin':
        flash('Akses ditolak. Hanya Admin yang dapat mengakses.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Ambil semua data (menggunakan list untuk hasil cursor MongoDB)
    all_tebu = list(TEBU.find({}))
    all_jagung = list(JAGUNG.find({}))
    all_padi = list(PADI.find({}))
    
    # Hitung data agregat (menggunakan Aggregation Pipeline di MongoDB atau di Python)
    # Aggregation Pipeline lebih efisien, tapi kita gunakan Python sederhana untuk total:
    total_netto_tebu = sum(doc.get('nilai_netto', 0) for doc in all_tebu)
    total_netto_jagung = sum(doc.get('nilai_protas_netto', 0) for doc in all_jagung)
    total_netto_padi = sum(doc.get('nilai_protas_netto', 0) for doc in all_padi)
    
    return render_template('admin_data.html', 
                           tebu=all_tebu, jagung=all_jagung, padi=all_padi,
                           total_tebu=total_netto_tebu, total_jagung=total_netto_jagung, total_padi=total_netto_padi)

# --- PENYIAPAN APLIKASI AWAL (Membuat Admin) ---

def create_admin_user():
    """Membuat user admin pertama jika belum ada (MongoDB tidak memerlukan db.create_all())."""
    with app.app_context():
        # Cek apakah ada user dengan role 'admin'
        if not USERS.find_one({"role": "admin"}):
            admin_data = {
                "email": "admin@app.com",
                "name": "Administrator",
                "password_hash": generate_password_hash("adminpass123"),
                "role": "admin",
                "created_at": datetime.utcnow()
            }
            USERS.insert_one(admin_data)
            print("INFO: Admin user created (admin@app.com / adminpass123)")

if __name__ == '__main__':
    # Panggil fungsi setup di sini
    create_admin_user() 
    
    # Jalankan server Flask
    app.run(debug=True)
