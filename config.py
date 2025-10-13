import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kunci-rahasia-yang-kuat'
    
    # --- KONFIGURASI MONGO_URI ---
    
    # Pilihan A: Gunakan MongoDB Lokal (pastikan server 27017 berjalan)
    MONGO_URI_LOKAL = "mongodb://localhost:27017/tani_analyzer_db" 

    # Pilihan B: Gunakan MongoDB Atlas (Cloud)
    # PENTING: GANTI sepenuhnya string di bawah ini dengan URI yang Anda dapatkan dari Atlas!
    # PASTIKAN <username>, <password>, dan <cluster-name> SUDAH DIGANTI DENGAN BENAR.
    MONGO_URI_ATLAS = "mongodb+srv://nurcahyawulan06_db_user:M4rZrM87E0L0ZCZs@autterpadja.2elnrrl.mongodb.net/?retryWrites=true&w=majority&appName=AUTTERPADJA"
    
    # Pilih salah satu (saat development, mari kita gunakan Atlas untuk menghindari error koneksi lokal)
    # KAMI MENGGANTI MONGO_URI_LOKAL menjadi MONGO_URI_ATLAS di sini:
    MONGO_URI = os.environ.get('mongodb://localhost:27017/tani_analyzer_db') or MONGO_URI_ATLAS 
    # Jika Anda sudah menyiapkan variabel lingkungan MONGO_URI di sistem Anda, maka variabel itu akan digunakan.
