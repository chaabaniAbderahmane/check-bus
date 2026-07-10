import streamlit as st
import pandas as pd
from database import *
from qr_system import display_qr_card
from chat_system import render_chat_interface
from loyalty_program import render_loyalty_card, award_trip_points
import time

def render_client_portal():
    """Interface client"""
    
    # CSS personnalisé
    st.markdown("""
    <style>
    .client-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 24px;
        border-radius: 20px;
        border: 2px solid #FF6B35;
        text-align: center;
        margin-bottom: 24px;
    }
    .info-card {
        background: #1E293B;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #334155;
        margin: 12px 0;
    }
    .seat-badge {
        background: linear-gradient(135deg, #FF6B35, #FF8F5C);
        color: white;
        padding: 12px 24px;
        border-radius: 12px;
        font-size: 1.5em;
        font-weight: bold;
        display: inline-block;
    }
    .success-check {
        background: linear-gradient(135deg, #22C55E, #4ADE80);
        color: white;
        padding: 16px;
        border-radius: 16px;
        text-align: center;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    </style>
    """, unsafe_allow_html=True)
    
    user = get_user_by_id(st.session_state['user_id'])
    if not user:
        st.error("Utilisateur non trouvé")
        return
    
    trip = get_trips()
    trip = trip[trip['id'] == user['trip_id']].iloc[0] if not trip.empty else None
    
    # Header
    st.markdown(f"""
    <div class="client-header">
        <h1 style="color: #FF6B35; margin: 0;">🚌 Bienvenue, {user['first_name']} !</h1>
        <p style="color: #94A3B8; margin: 8px 0 0 0;">{trip['trip_name'] if trip is not None else 'Voyage'} → {trip['destination'] if trip is not None else ''}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/passenger.png", width=60)
        st.title("Menu")
        
        page = st.radio("", [
            "🏠 Mon Profil",
            "✅ Ma Présence", 
            "🪑 Mon Siège",
            "💬 Contacter l'Organisateur",
            "🎁 Ma Fidélité"
        ])
        
        st.divider()
        st.info(f"Points: {user.get('points', 0)} ⭐")
        
        if st.button("🚪 Déconnexion", use_container_width=True):
            for key in ['authenticated', 'user_role', 'user_id', 'user_name', 'trip_id']:
                st.session_state[key] = None if key != 'authenticated' else False
            st.rerun()
    
    # Routing
    if page == "🏠 Mon Profil":
        show_client_profile(user, trip)
    elif page == "✅ Ma Présence":
        show_client_checkin(user)
    elif page == "🪑 Mon Siège":
        show_client_seat(user)
    elif page == "💬 Contacter l'Organisateur":
        show_client_chat(user)
    elif page == "🎁 Ma Fidélité":
        show_client_loyalty(user)

def show_client_profile(user, trip):
    """Profil du client"""
    st.subheader("👤 Mon Profil")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="info-card">
            <h4 style="color: #FF6B35;">📝 Informations</h4>
            <p><strong>Nom:</strong> {user['first_name']} {user['last_name']}</p>
            <p><strong>Username:</strong> <code>{user['username']}</code></p>
            <p><strong>Catégorie:</strong> {user.get('category', 'Standard')}</p>
            <p><strong>Voyage:</strong> {trip['trip_name'] if trip is not None else 'N/A'}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="info-card">
            <h4 style="color: #FF6B35;">📞 Contact</h4>
            <p><strong>Téléphone:</strong> {user.get('phone', 'Non renseigné')}</p>
            <p><strong>Email:</strong> {user.get('email', 'Non renseigné')}</p>
            <p><strong>Code QR:</strong> <code>{user['access_code']}</code></p>
        </div>
        """, unsafe_allow_html=True)
    
    # QR Code
    st.subheader("🎫 Mon QR Code")
    display_qr_card(user, trip['trip_name'] if trip is not None else "Voyage")

def show_client_checkin(user):
    """Page de check-in du client"""
    st.subheader("✅ Confirmer ma Présence")
    
    if user.get('checked_in'):
        st.markdown("""
        <div class="success-check">
            <h2>🎉 Vous êtes confirmé !</h2>
            <p>Bon voyage et profitez bien de la sortie !</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.balloons()
        
        # Afficher l'heure de check-in
        if user.get('checked_in_at'):
            st.info(f"✅ Check-in effectué le: {user['checked_in_at'][:16]}")
    else:
        st.warning("⏳ Vous n'avez pas encore confirmé votre présence")
        
        st.markdown("""
        <div style="text-align: center; padding: 40px;">
            <h3 style="color: #F1F5F9;">Cliquez ci-dessous pour confirmer</h3>
            <p style="color: #94A3B8;">Cela informera l'organisateur que vous êtes là</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("✅ JE SUIS LÀ !", use_container_width=True, type="primary"):
            check_in_user(user['id'])
            
            # Award points
            award_trip_points(user['id'], user['trip_id'])
            
            st.success("🎉 Présence confirmée ! Points ajoutés !")
            time.sleep(1)
            st.rerun()

def show_client_seat(user):
    """Afficher le siège du client"""
    st.subheader("🪑 Mon Siège dans le Bus")
    
    if user.get('seat_number'):
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown(f"""
            <div style="text-align: center; padding: 40px;">
                <p style="color: #94A3B8; margin-bottom: 16px;">Votre place assignée</p>
                <div class="seat-badge">
                    🪑 {user.get('seat_label', f"R{user['seat_row']}C{user['seat_col']}")}
                </div>
                <p style="color: #64748B; margin-top: 16px;">
                    Rangée {user.get('seat_row', '?')} | Colonne {user.get('seat_col', '?')}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Visualisation simple du bus
            st.subheader("Plan du Bus")
            bus_visual = []
            for row in range(10):
                row_seats = []
                for col in range(4):
                    seat_num = row * 4 + col + 1
                    if seat_num == user.get('seat_number'):
                        row_seats.append("🟠")  # Siège du client
                    else:
                        row_seats.append("⬜")
                bus_visual.append(f"R{row+1}: {' '.join(row_seats[:2])}  ⬛  {' '.join(row_seats[2:])}")
            
            for line in bus_visual:
                st.text(line)
    else:
        st.info("🔄 Votre siège n'a pas encore été assigné. L'organisateur le fera bientôt.")

def show_client_chat(user):
    """Chat client vers admin"""
    render_chat_interface(
        user['trip_id'],
        user['id'],
        'client'
    )

def show_client_loyalty(user):
    """Programme de fidélité du client"""
    render_loyalty_card(user['id'])
    
    # Historique
    st.subheader("📜 Historique")
    conn = get_connection()
    history = pd.read_sql_query('''
        SELECT * FROM loyalty_history 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', conn, params=(user['id'],))
    conn.close()
    
    if not history.empty:
        st.dataframe(history[['points_earned', 'description', 'created_at']], use_container_width=True)
    else:
        st.info("Aucun historique pour le moment")
