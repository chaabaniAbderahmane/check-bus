import streamlit as st
import sqlite3
from config import *
from database import *
from admin_dashboard import render_admin_dashboard
from client_portal import render_client_portal
from qr_system import generate_qr_code, get_image_base64
import base64
from PIL import Image

# Configuration de la page
st.set_page_config(
    page_title="VoyagePro - Gestion de Voyages",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Global
st.markdown("""
<style>
    /* Reset et base */
    .stApp {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    }
    
    /* Login container */
    .login-container {
        max-width: 450px;
        margin: 0 auto;
        padding: 40px;
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border-radius: 24px;
        border: 1px solid #334155;
        box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    
    /* Titre principal */
    .main-title {
        text-align: center;
        color: #FF6B35;
        font-size: 2.5em;
        font-weight: 800;
        margin-bottom: 8px;
        text-shadow: 0 2px 10px rgba(255,107,53,0.3);
    }
    
    .subtitle {
        text-align: center;
        color: #94A3B8;
        font-size: 1.1em;
        margin-bottom: 32px;
    }
    
    /* Boutons */
    .stButton>button {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8F5C 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(255,107,53,0.4) !important;
    }
    
    /* Inputs */
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background: #0F172A !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        color: #F1F5F9 !important;
        padding: 12px 16px !important;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #FF6B35 !important;
        box-shadow: 0 0 0 2px rgba(255,107,53,0.2) !important;
    }
    
    /* Selectbox */
    .stSelectbox>div>div>div {
        background: #0F172A !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #1E293B;
        padding: 8px;
        border-radius: 16px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 12px;
        padding: 12px 24px;
        color: #94A3B8;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #FF6B35, #FF8F5C) !important;
        color: white !important;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #FF6B35 !important;
        font-weight: 700 !important;
    }
    
    /* Dataframes */
    .stDataFrame {
        background: #1E293B;
        border-radius: 12px;
        border: 1px solid #334155;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0F172A;
    }
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #FF6B35;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.6s ease-out;
    }
    
    /* QR Scanner simulation */
    .qr-scanner {
        border: 3px dashed #FF6B35;
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        background: rgba(255,107,53,0.05);
    }
</style>
""", unsafe_allow_html=True)

def show_landing_page():
    """Page d'accueil avec choix du mode d'accès"""
    
    # Animation d'entrée
    st.markdown("""
    <div class="animate-fade-in">
        <div style="text-align: center; padding: 60px 20px;">
            <div style="font-size: 5em; margin-bottom: 20px;">🚌</div>
            <h1 class="main-title">VoyagePro</h1>
            <p class="subtitle">Gestion intelligente de vos voyages organisés</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Mode d'accès
        access_mode = st.segmented_control(
            "Mode d'accès",
            options=["🔐 Admin / Organisateur", "👤 Voyageur (Client)", "📱 Scanner QR Code"],
            default="🔐 Admin / Organisateur"
        )
        
        if access_mode == "🔐 Admin / Organisateur":
            show_admin_login()
        elif access_mode == "👤 Voyageur (Client)":
            show_client_login()
        elif access_mode == "📱 Scanner QR Code":
            show_qr_scanner()

def show_admin_login():
    """Formulaire de connexion admin"""
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    st.subheader("🔐 Espace Organisateur")
    
    with st.form("admin_login"):
        username = st.text_input("Nom d'utilisateur", placeholder="admin")
        password = st.text_input("Mot de passe", type="password", placeholder="••••••")
        trip_code = st.text_input("Code du voyage (optionnel)", placeholder="Laissez vide pour voir tous les voyages")
        
        submitted = st.form_submit_button("Se Connecter", use_container_width=True)
        
        if submitted:
            user = authenticate_user(username, password)
            if user and user['role'] == ROLE_ADMIN:
                st.session_state.update({
                    'authenticated': True,
                    'user_role': ROLE_ADMIN,
                    'user_id': user['id'],
                    'user_name': f"{user['first_name']} {user['last_name']}",
                    'trip_id': user['trip_id']
                })
                st.success("✅ Connexion réussie !")
                st.rerun()
            else:
                st.error("❌ Identifiants incorrects")
    
    st.markdown("""
        <div style="text-align: center; margin-top: 20px; color: #64748B;">
            <p>Première visite ? Créez un voyage pour générer vos accès admin.</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Option créer premier voyage
    with st.expander("➕ Créer mon premier voyage"):
        with st.form("first_trip"):
            st.write("**Créer un voyage et un compte admin**")
            trip_name = st.text_input("Nom du voyage")
            destination = st.text_input("Destination")
            date = st.date_input("Date")
            bus = st.text_input("Numéro de bus")
            
            admin_first = st.text_input("Votre prénom")
            admin_last = st.text_input("Votre nom")
            admin_user = st.text_input("Nom d'utilisateur admin")
            admin_pass = st.text_input("Mot de passe admin", type="password")
            
            if st.form_submit_button("Créer", use_container_width=True):
                if all([trip_name, destination, bus, admin_first, admin_last, admin_user, admin_pass]):
                    trip_id = create_trip(trip_name, destination, date.isoformat(), bus)
                    admin_id = create_admin(trip_id, admin_first, admin_last, admin_user, admin_pass)
                    if admin_id:
                        st.success(f"✅ Voyage et admin créés ! Connectez-vous avec: {admin_user}")
                    else:
                        st.error("Username déjà utilisé")
                else:
                    st.error("Tous les champs sont obligatoires")

def show_client_login():
    """Connexion client avec username/password"""
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    st.subheader("👤 Espace Voyageur")
    
    with st.form("client_login"):
        username = st.text_input("Nom d'utilisateur", placeholder="prenom.nom")
        password = st.text_input("Mot de passe", placeholder="Votre prénom avec majuscule")
        
        submitted = st.form_submit_button("Se Connecter", use_container_width=True)
        
        if submitted:
            # Chercher dans tous les voyages
            conn = get_connection()
            c = conn.cursor()
            c.execute('SELECT * FROM users WHERE username = ? AND role = "client"', (username,))
            user = c.fetchone()
            conn.close()
            
            if user:
                columns = [description[0] for description in c.description]
                user_dict = dict(zip(columns, user))
                
                # Vérifier password
                import hashlib
                if user_dict['password'] == hashlib.sha256(password.encode()).hexdigest():
                    st.session_state.update({
                        'authenticated': True,
                        'user_role': ROLE_CLIENT,
                        'user_id': user_dict['id'],
                        'user_name': f"{user_dict['first_name']} {user_dict['last_name']}",
                        'trip_id': user_dict['trip_id']
                    })
                    st.success("✅ Connexion réussie !")
                    st.rerun()
                else:
                    st.error("❌ Mot de passe incorrect")
            else:
                st.error("❌ Utilisateur non trouvé")
    
    st.markdown("""
        <div style="text-align: center; margin-top: 20px; color: #64748B;">
            <p>💡 Vos identifiants vous ont été donnés par l'organisateur</p>
            <p>📱 Vous pouvez aussi scanner votre QR Code</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_qr_scanner():
    """Simulation de scan QR"""
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    st.subheader("📱 Scanner QR Code")
    
    st.markdown("""
    <div class="qr-scanner">
        <div style="font-size: 3em; margin-bottom: 16px;">📷</div>
        <p style="color: #94A3B8;">Dans l'application mobile, scannez le QR Code</p>
        <p style="color: #64748B; font-size: 0.9em;">Simulation web: entrez le code manuellement</p>
    </div>
    """, unsafe_allow_html=True)
    
    qr_code = st.text_input("Code QR du voyageur", placeholder="Ex: A3F9B2", max_chars=6)
    
    if st.button("🔍 Vérifier le Code", use_container_width=True):
        client = get_client_by_code(qr_code.upper())
        if client:
            # Auto-login le client
            st.session_state.update({
                'authenticated': True,
                'user_role': ROLE_CLIENT,
                'user_id': client['id'],
                'user_name': f"{client['first_name']} {client['last_name']}",
                'trip_id': client['trip_id']
            })
            st.success(f"✅ Bienvenue {client['first_name']} !")
            st.rerun()
        else:
            st.error("❌ Code QR invalide ou expiré")
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Point d'entrée principal"""
    init_session_state()
    
    if not st.session_state['authenticated']:
        show_landing_page()
    else:
        # Router vers le bon dashboard
        if st.session_state['user_role'] == ROLE_ADMIN:
            render_admin_dashboard()
        else:
            render_client_portal()

if __name__ == "__main__":
    main()
