import streamlit as st
from database import add_points, get_user_by_id

LOYALTY_THRESHOLD = 10  # 10 voyages = 1 gratuit

def render_loyalty_card(user_id):
    """Affiche la carte de fidélité du client"""
    user = get_user_by_id(user_id)
    if not user:
        return
    
    points = user.get('points', 0)
    trips_count = user.get('trips_count', 0)
    progress = min(trips_count / LOYALTY_THRESHOLD * 100, 100)
    
    # Calculer voyages restants
    remaining = max(0, LOYALTY_THRESHOLD - trips_count)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
                border-radius: 20px; padding: 24px; border: 2px solid #FF6B35;
                margin: 20px 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div>
                <h3 style="color: #FF6B35; margin: 0;">🎁 Programme Fidélité</h3>
                <p style="color: #94A3B8; margin: 4px 0 0 0;">Voyage {trips_count} / {LOYALTY_THRESHOLD}</p>
            </div>
            <div style="background: #FF6B35; color: white; padding: 8px 16px; 
                        border-radius: 20px; font-weight: bold;">
                {points} pts
            </div>
        </div>
        
        <div style="background: #334155; height: 12px; border-radius: 6px; overflow: hidden;">
            <div style="background: linear-gradient(90deg, #FF6B35, #FF8F5C); 
                        width: {progress}%; height: 100%; border-radius: 6px;
                        transition: width 0.5s ease;"></div>
        </div>
        
        <p style="color: #64748B; margin-top: 12px; font-size: 0.9em;">
            {"🎉 Félicitations ! Votre prochain voyage est GRATUIT !" if remaining == 0 else f"Encore {remaining} voyage(s) pour un voyage gratuit !"}
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    return trips_count >= LOYALTY_THRESHOLD

def award_trip_points(user_id, trip_id):
    """Attribue des points pour un voyage"""
    add_points(user_id, 1, trip_id, f"Points pour le voyage #{trip_id}")
