import streamlit as st
import hashlib
import secrets

# Configuration de l'application
APP_NAME = "🚌 VoyagePro - Gestion de Voyages"
APP_ICON = "🚌"

# Rôles
ROLE_ADMIN = "admin"
ROLE_CLIENT = "client"

# Configuration bus
BUS_ROWS = 10
BUS_COLS = 4  # 2 de chaque côté du couloir
TOTAL_SEATS = BUS_ROWS * BUS_COLS

# Programme fidélité
LOYALTY_FREE_TRIP_THRESHOLD = 10

def init_session_state():
    """Initialise les variables de session"""
    defaults = {
        'authenticated': False,
        'user_role': None,
        'user_id': None,
        'user_name': None,
        'trip_id': None,
        'current_page': 'login'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def generate_code(length=6):
    """Génère un code aléatoire sécurisé"""
    return secrets.token_hex(length//2).upper()[:length]

def hash_password(password):
    """Hash un mot de passe"""
    return hashlib.sha256(password.encode()).hexdigest()
