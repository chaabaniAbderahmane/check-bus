import streamlit as st
import pandas as pd
from database import *
from bus_seating import BusSeatingAlgorithm
from qr_system import display_qr_card, generate_client_qr
from chat_system import render_chat_interface
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import speech_recognition as sr
from io import BytesIO

def render_admin_dashboard():
    """Interface principale admin"""
    
    # CSS personnalisé
    st.markdown("""
    <style>
    .admin-header {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8F5C 100%);
        padding: 20px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
    }
    .stat-card {
        background: #1E293B;
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #FF6B35;
    }
    .passenger-row {
        background: #1E293B;
        padding: 12px;
        border-radius: 8px;
        margin: 4px 0;
        border: 1px solid #334155;
    }
    .checked-in {
        border-left: 4px solid #22C55E;
    }
    .not-checked-in {
        border-left: 4px solid #EF4444;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="admin-header">
        <h1>🚌 Tableau de Bord Administrateur</h1>
        <p>Gérez vos voyages et voyageurs en toute simplicité</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/bus.png", width=80)
        st.title("Navigation")
        
        page = st.radio("", [
            "🏠 Accueil",
            "✈️ Créer un Voyage", 
            "👥 Gestion Voyageurs",
            "🪑 Placement Bus",
            "📊 Présence",
            "💬 Messages",
            "🎁 Fidélité"
        ])
        
        st.divider()
        if st.button("🚪 Déconnexion", use_container_width=True):
            for key in ['authenticated', 'user_role', 'user_id', 'user_name', 'trip_id']:
                st.session_state[key] = None if key != 'authenticated' else False
            st.rerun()
    
    # Routing
    if page == "🏠 Accueil":
        show_admin_home()
    elif page == "✈️ Créer un Voyage":
        show_create_trip()
    elif page == "👥 Gestion Voyageurs":
        show_manage_passengers()
    elif page == "🪑 Placement Bus":
        show_bus_seating()
    elif page == "📊 Présence":
        show_attendance()
    elif page == "💬 Messages":
        show_admin_chat()
    elif page == "🎁 Fidélité":
        show_loyalty_admin()

def show_admin_home():
    """Page d'accueil admin avec stats"""
    trips = get_trips()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="stat-card">
            <h3 style="color: #FF6B35; margin: 0;">✈️ Voyages</h3>
            <h2 style="color: white; margin: 8px 0;">{}</h2>
        </div>
        """.format(len(trips)), unsafe_allow_html=True)
    
    with col2:
        total_clients = 0
        for _, trip in trips.iterrows():
            clients = get_users_by_trip(trip['id'], 'client')
            total_clients += len(clients)
        st.markdown("""
        <div class="stat-card">
            <h3 style="color: #FF6B35; margin: 0;">👥 Voyageurs</h3>
            <h2 style="color: white; margin: 8px 0;">{}</h2>
        </div>
        """.format(total_clients), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card">
            <h3 style="color: #FF6B35; margin: 0;">🚌 Bus Actifs</h3>
            <h2 style="color: white; margin: 8px 0;">{}</h2>
        </div>
        """.format(len(trips)), unsafe_allow_html=True)
    
    # Liste des voyages
    st.subheader("Vos Voyages")
    if not trips.empty:
        for _, trip in trips.iterrows():
            with st.expander(f"🚌 {trip['trip_name']} → {trip['destination']} ({trip['departure_date']})"):
                clients = get_users_by_trip(trip['id'], 'client')
                checked = clients[clients['checked_in'] == 1] if not clients.empty else pd.DataFrame()
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Voyageurs", len(clients))
                col2.metric("Présents", len(checked))
                col3.metric("Bus", trip['bus_number'])
                
                if st.button("Sélectionner ce voyage", key=f"select_trip_{trip['id']}"):
                    st.session_state['trip_id'] = trip['id']
                    st.success(f"Voyage '{trip['trip_name']}' sélectionné !")
    else:
        st.info("Aucun voyage créé. Commencez par en créer un !")

def show_create_trip():
    """Créer un nouveau voyage"""
    st.subheader("✈️ Créer un Nouveau Voyage")
    
    with st.form("create_trip_form"):
        trip_name = st.text_input("Nom du voyage", placeholder="Ex: Sortie Annuelle 2026")
        destination = st.text_input("Destination", placeholder="Ex: Marrakech")
        departure_date = st.date_input("Date de départ")
        bus_number = st.text_input("Numéro du bus", placeholder="Ex: BUS-001")
        
        submitted = st.form_submit_button("🚀 Créer le Voyage", use_container_width=True)
        
        if submitted:
            if all([trip_name, destination, bus_number]):
                trip_id = create_trip(trip_name, destination, departure_date.isoformat(), bus_number)
                
                # Créer l'admin pour ce voyage
                st.session_state['trip_id'] = trip_id
                
                st.success(f"✅ Voyage créé avec succès ! ID: {trip_id}")
                st.info("Maintenant, ajoutez des voyageurs dans la section 'Gestion Voyageurs'")
            else:
                st.error("Veuillez remplir tous les champs")

def show_manage_passengers():
    """Gérer les voyageurs - avec saisie vocale et manuelle"""
    if not st.session_state.get('trip_id'):
        st.warning("Veuillez d'abord sélectionner un voyage dans l'accueil")
        return
    
    trip_id = st.session_state['trip_id']
    trip = get_trips()
    trip = trip[trip['id'] == trip_id].iloc[0] if not trip.empty else None
    
    st.subheader(f"👥 Gestion des Voyageurs - {trip['trip_name'] if trip is not None else ''}")
    
    # Onglets pour différentes méthodes d'ajout
    tab1, tab2, tab3 = st.tabs(["✍️ Saisie Manuelle", "🎤 Saisie Vocale", "📋 Liste & QR Codes"])
    
    with tab1:
        with st.form("add_passenger_form"):
            col1, col2 = st.columns(2)
            with col1:
                first_name = st.text_input("Prénom")
                category = st.selectbox("Catégorie", [
                    "standard", "famille", "amis", "fille", "garçon", "elder", "enfant"
                ])
                phone = st.text_input("Téléphone")
            
            with col2:
                last_name = st.text_input("Nom")
                group_id = st.number_input("ID Groupe (famille/amis ensemble)", min_value=0, value=0, step=1)
                email = st.text_input("Email")
            
            notes = st.text_area("Notes spéciales", placeholder="Ex: Allergies, besoins spéciaux...")
            
            submitted = st.form_submit_button("➕ Ajouter le Voyageur", use_container_width=True)
            
            if submitted:
                if first_name and last_name:
                    user_id, username, password, access_code = create_client(
                        trip_id, first_name, last_name, category, 
                        group_id if group_id > 0 else None, phone, email
                    )
                    
                    st.success(f"""
                    ✅ Voyageur ajouté !
                    - **Username**: `{username}`
                    - **Password**: `{password}`
                    - **Code QR**: `{access_code}`
                    """)
                else:
                    st.error("Prénom et Nom obligatoires")
    
    with tab2:
        st.info("🎤 Cliquez sur le micro et dites les informations du voyageur")
        st.write("**Format attendu**: 'Prénom Nom, catégorie, téléphone'")
        st.write("**Exemple**: 'Ahmed Benali, famille, 0661234567'")
        
        # Simulation de saisie vocale (Streamlit ne supporte pas directement le micro)
        # Dans un vrai déploiement, vous utiliseriez st.audio_input() (Streamlit 1.35+)
        
        vocal_input = st.text_area("🎤 Transcription vocale (simulation)", 
                                  placeholder="Collez ici la transcription...",
                                  help="Dans la version finale, ce sera remplacé par une vraie entrée micro")
        
        if st.button("🔄 Traiter la saisie vocale"):
            if vocal_input:
                # Parser la saisie vocale
                parts = [p.strip() for p in vocal_input.split(',')]
                if len(parts) >= 2:
                    names = parts[0].split()
                    if len(names) >= 2:
                        first_name, last_name = names[0], ' '.join(names[1:])
                        category = parts[1] if len(parts) > 1 else 'standard'
                        phone = parts[2] if len(parts) > 2 else None
                        
                        user_id, username, password, access_code = create_client(
                            trip_id, first_name, last_name, category, None, phone
                        )
                        st.success(f"✅ Ajouté: {first_name} {last_name} | Code: {access_code}")
                    else:
                        st.error("Format incorrect. Dites: 'Prénom Nom, catégorie'")
                else:
                    st.error("Format incorrect")
    
    with tab3:
        clients = get_users_by_trip(trip_id, 'client')
        if not clients.empty:
            st.write(f"**{len(clients)} voyageurs enregistrés**")
            
            # Tableau des voyageurs
            display_df = clients[['first_name', 'last_name', 'username', 'access_code', 
                                 'category', 'seat_number', 'checked_in', 'points']].copy()
            display_df.columns = ['Prénom', 'Nom', 'Username', 'Code QR', 'Catégorie', 'Siège', 'Présent', 'Points']
            st.dataframe(display_df, use_container_width=True)
            
            # Générer QR codes
            st.subheader("🎫 QR Codes des Voyageurs")
            selected_client = st.selectbox("Sélectionner un voyageur", 
                                          [f"{row['first_name']} {row['last_name']}" for _, row in clients.iterrows()])
            
            if selected_client:
                client_row = clients[clients['first_name'] + ' ' + clients['last_name'] == selected_client].iloc[0]
                display_qr_card(client_row.to_dict(), trip['trip_name'] if trip is not None else "Voyage")
                
                # Télécharger le QR
                qr_img = generate_client_qr(client_row.to_dict(), trip['trip_name'] if trip is not None else "Voyage")
                buf = BytesIO()
                qr_img.save(buf, format='PNG')
                st.download_button("📥 Télécharger le QR Code", buf.getvalue(), 
                                 f"qr_{client_row['first_name']}_{client_row['last_name']}.png", 
                                 "image/png")
        else:
            st.info("Aucun voyageur enregistré")

def show_bus_seating():
    """Placement intelligent dans le bus"""
    if not st.session_state.get('trip_id'):
        st.warning("Sélectionnez un voyage d'abord")
        return
    
    trip_id = st.session_state['trip_id']
    clients = get_users_by_trip(trip_id, 'client')
    
    if clients.empty:
        st.warning("Ajoutez des voyageurs d'abord")
        return
    
    st.subheader("🪑 Placement Intelligent dans le Bus")
    
    # Algorithme de placement
    bus = BusSeatingAlgorithm()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("""
        **Règles de placement:**
        - 👨‍👩‍👧 Familles ensemble
        - 👭 Filles ensemble / 👬 Garçons ensemble  
        - 👴 Personnes âgées devant
        - 🪟 Sièges fenêtres prioritaires
        """)
        
        if st.button("🎯 Lancer l'Algorithmique de Placement", use_container_width=True):
            assignments = bus.assign_seats(clients)
            
            # Mettre à jour la base de données
            for assignment in assignments:
                update_seat(assignment['user_id'], assignment['seat_number'],
                          assignment['seat_row'], assignment['seat_col'])
            
            st.success(f"✅ {len(assignments)} sièges attribués !")
            st.balloons()
    
    with col2:
        # Visualisation du bus
        st.subheader("Plan du Bus")
        
        # Créer une grille visuelle
        seat_data = []
        for row in range(10):
            for col in range(4):
                seat_num = row * 4 + col + 1
                client = clients[clients['seat_number'] == seat_num]
                if not client.empty:
                    client = client.iloc[0]
                    status = " Occupé"
                    name = f"{client['first_name'][:8]}"
                    color = "#22C55E" if client['checked_in'] else "#FF6B35"
                else:
                    status = " Libre"
                    name = ""
                    color = "#334155"
                
                seat_data.append({
                    'row': row + 1,
                    'col': ['A', 'B', 'C', 'D'][col],
                    'status': status,
                    'name': name,
                    'color': color
                })
        
        # Afficher comme tableau stylisé
        seat_df = pd.DataFrame(seat_data)
        pivot = seat_df.pivot(index='row', columns='col', values='name')
        st.table(pivot)

def show_attendance():
    """Gestion de la présence"""
    if not st.session_state.get('trip_id'):
        st.warning("Sélectionnez un voyage d'abord")
        return
    
    trip_id = st.session_state['trip_id']
    clients = get_users_by_trip(trip_id, 'client')
    
    st.subheader("📊 Pointage des Présences")
    
    # Stats
    total = len(clients)
    checked = len(clients[clients['checked_in'] == 1]) if not clients.empty else 0
    missing = total - checked
    
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Total", total)
    col2.metric("✅ Présents", checked, f"{checked/total*100:.1f}%" if total > 0 else "0%")
    col3.metric("❌ Absents", missing)
    
    # Barre de progression
    progress = checked / total if total > 0 else 0
    st.progress(progress, text=f"Remplissage: {progress*100:.1f}%")
    
    # Liste avec possibilité de check-in manuel
    st.subheader("Liste des Voyageurs")
    
    for _, client in clients.iterrows():
        status_class = "checked-in" if client['checked_in'] else "not-checked-in"
        status_icon = "✅" if client['checked_in'] else "⏳"
        seat_info = f" | 🪑 Siège {client['seat_label']}" if pd.notna(client.get('seat_number')) else ""
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"""
            <div class="passenger-row {status_class}">
                <strong>{status_icon} {client['first_name']} {client['last_name']}</strong>
                <span style="color: #94A3B8;">{seat_info}</span>
                <br><small style="color: #64748B;">Cat: {client['category']} | Code: {client['access_code']}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if not client['checked_in']:
                if st.button("✅ Check-in", key=f"checkin_{client['id']}"):
                    admin_check_in_user(client['id'])
                    st.rerun()
        
        with col3:
            if st.button("💬 Message", key=f"msg_{client['id']}"):
                st.session_state['chat_with'] = client['id']
                st.session_state['current_page'] = 'chat'
                st.rerun()

def show_admin_chat():
    """Interface chat admin"""
    if not st.session_state.get('trip_id'):
        st.warning("Sélectionnez un voyage d'abord")
        return
    
    render_chat_interface(
        st.session_state['trip_id'],
        st.session_state['user_id'],
        'admin'
    )

def show_loyalty_admin():
    """Gestion du programme de fidélité"""
    if not st.session_state.get('trip_id'):
        st.warning("Sélectionnez un voyage d'abord")
        return
    
    trip_id = st.session_state['trip_id']
    clients = get_users_by_trip(trip_id, 'client')
    
    st.subheader("🎁 Programme de Fidélité")
    
    if not clients.empty:
        # Tableau des points
        loyalty_df = clients[['first_name', 'last_name', 'trips_count', 'points']].copy()
        loyalty_df.columns = ['Prénom', 'Nom', 'Voyages', 'Points']
        
        # Highlight ceux qui ont droit à un voyage gratuit
        def highlight_free(row):
            if row['Voyages'] >= 10:
                return ['background-color: #FF6B35; color: white'] * len(row)
            return [''] * len(row)
        
        st.dataframe(loyalty_df.style.apply(highlight_free, axis=1), use_container_width=True)
        
        # Graphique
        fig = px.bar(loyalty_df, x='Nom', y='Voyages', 
                    title="Progression vers le voyage gratuit (10 voyages)",
                    color='Voyages', color_continuous_scale='oranges')
        fig.update_layout(
            paper_bgcolor='#0F172A',
            plot_bgcolor='#1E293B',
            font_color='#F1F5F9'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Aucun client enregistré")
