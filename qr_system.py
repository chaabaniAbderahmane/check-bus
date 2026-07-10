import qrcode
import io
import base64
from PIL import Image, ImageDraw, ImageFont
import streamlit as st

def generate_qr_code(data, size=10, border=2):
    """Génère un QR code à partir des données"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="#FF6B35", back_color="#0F172A")
    return img

def generate_client_qr(client_data, trip_name):
    """Génère un QR code personnalisé pour un client"""
    # Données encodées dans le QR
    qr_data = f"VOYAGEPRO:{client_data['access_code']}"
    
    # Générer le QR
    qr_img = generate_qr_code(qr_data, size=15, border=3)
    
    # Créer une image composite avec infos
    width, height = qr_img.size
    new_height = height + 150
    composite = Image.new('RGB', (width, new_height), '#0F172A')
    composite.paste(qr_img, (0, 0))
    
    # Ajouter texte
    draw = ImageDraw.Draw(composite)
    
    # Utiliser une police par défaut
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Texte
    text_y = height + 20
    draw.text((width//2, text_y), f"{client_data['first_name']} {client_data['last_name']}", 
              fill='#F1F5F9', font=font_large, anchor='mm')
    draw.text((width//2, text_y + 40), f"Voyage: {trip_name}", 
              fill='#94A3B8', font=font_small, anchor='mm')
    draw.text((width//2, text_y + 70), f"Code: {client_data['access_code']}", 
              fill='#FF6B35', font=font_small, anchor='mm')
    draw.text((width//2, text_y + 100), "Scannez pour accéder", 
              fill='#64748B', font=font_small, anchor='mm')
    
    return composite

def get_image_base64(img):
    """Convertit une image PIL en base64 pour Streamlit"""
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

def display_qr_card(client_data, trip_name):
    """Affiche une carte QR stylisée"""
    qr_img = generate_client_qr(client_data, trip_name)
    img_base64 = get_image_base64(qr_img)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%); 
                padding: 20px; border-radius: 20px; border: 2px solid #FF6B35;
                text-align: center; max-width: 400px; margin: 0 auto;">
        <img src="data:image/png;base64,{img_base64}" style="width: 100%; border-radius: 10px;">
    </div>
    """, unsafe_allow_html=True)
  
