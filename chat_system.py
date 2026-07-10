import streamlit as st
from database import get_messages, send_message, get_users_by_trip
from datetime import datetime

def render_chat_interface(trip_id, current_user_id, current_user_role, other_user_id=None):
    """Rend l'interface de chat"""
    
    st.markdown("""
    <style>
    .chat-message {
        padding: 12px 16px;
        border-radius: 16px;
        margin: 8px 0;
        max-width: 75%;
        word-wrap: break-word;
    }
    .chat-message.sent {
        background: linear-gradient(135deg, #FF6B35, #FF8F5C);
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 4px;
    }
    .chat-message.received {
        background: #1E293B;
        color: #F1F5F9;
        margin-right: auto;
        border-bottom-left-radius: 4px;
        border: 1px solid #334155;
    }
    .chat-container {
        height: 400px;
        overflow-y: auto;
        padding: 20px;
        background: #0F172A;
        border-radius: 16px;
        border: 1px solid #1E293B;
    }
    .chat-input {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 24px;
        padding: 12px 20px;
        color: white;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    if current_user_role == 'admin':
        st.subheader("💬 Chat avec les voyageurs")
        
        # Sélectionner un client
        clients = get_users_by_trip(trip_id, 'client')
        if not clients.empty:
            client_options = {f"{row['first_name']} {row['last_name']}": row['id'] 
                            for _, row in clients.iterrows()}
            selected_client = st.selectbox("Choisir un voyageur", list(client_options.keys()))
            other_user_id = client_options[selected_client]
        else:
            st.info("Aucun client dans ce voyage")
            return
    else:
        # Client - chat avec admin uniquement
        admins = get_users_by_trip(trip_id, 'admin')
        if not admins.empty:
            other_user_id = admins.iloc[0]['id']
            st.subheader("💬 Chat avec l'organisateur")
        else:
            st.error("Admin non disponible")
            return
    
    # Afficher messages
    messages = get_messages(trip_id, current_user_id, other_user_id)
    
    chat_html = '<div class="chat-container">'
    for _, msg in messages.iterrows():
        is_sent = msg['sender_id'] == current_user_id
        msg_class = "sent" if is_sent else "received"
        sender_name = "Vous" if is_sent else msg['sender_name']
        time_str = msg['created_at'][:16] if pd.notna(msg['created_at']) else ""
        
        chat_html += f"""
        <div class="chat-message {msg_class}">
            <div style="font-size: 0.75em; opacity: 0.8; margin-bottom: 4px;">
                {sender_name} • {time_str}
            </div>
            <div>{msg['message']}</div>
        </div>
        """
    chat_html += '</div>'
    
    st.markdown(chat_html, unsafe_allow_html=True)
    
    # Input
    with st.form(key=f"chat_form_{other_user_id}", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        with col1:
            new_message = st.text_input("Votre message...", key=f"msg_input_{other_user_id}", 
                                       label_visibility="collapsed")
        with col2:
            submitted = st.form_submit_button("Envoyer 🚀", use_container_width=True)
        
        if submitted and new_message.strip():
            send_message(trip_id, current_user_id, other_user_id, new_message.strip())
            st.rerun()
                              
