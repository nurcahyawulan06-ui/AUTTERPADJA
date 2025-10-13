# config.py

import os

class Config:
    # Menggunakan SQLite untuk database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Kunci rahasia untuk sesi Flask dan keamanan
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'kunci-rahasia-yang-kuat'