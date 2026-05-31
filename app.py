import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO
import time
import os
import sys

# Set up page configurations
st.set_page_config(
    page_title="Egyptian Currency Counter",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Robust path resolver for PyInstaller frozen mode vs developer local mode
def get_model_path():
    if os.path.exists("best.pt"):
        return "best.pt"
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        local_path = os.path.join(exe_dir, "best.pt")
        if os.path.exists(local_path):
            return local_path
        meipass_path = os.path.join(sys._MEIPASS, "best.pt")
        if os.path.exists(meipass_path):
            return meipass_path
    return "best.pt"

# Cache the YOLO model to prevent loading on every frame or slider rerun
@st.cache_resource
def load_yolo_model(path):
    try:
        model = YOLO(path)
        return model, True, "Model loaded successfully."
    except Exception as e:
        return None, False, str(e)

# Denomination RGB Color Palette (Fixed for direct RGB Drawing)
def get_denomination_color(val):
    colors = {
        5: (255, 193, 0),      # Gold-Yellow
        10: (255, 0, 180),     # Pink/Red
        20: (50, 205, 50),     # Vibrant Green
        50: (148, 0, 211),     # Deep Purple
        100: (0, 255, 255),    # Cyan/Teal
        200: (255, 140, 0),    # Gold-Orange
    }
    return colors.get(val, (255, 255, 255)) # Default white

# Inject custom Google Font and advanced UI styles
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"], .stApp {
        font-family: 'Outfit', sans-serif;
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    section[data-testid="stSidebar"] {
        background-color: rgba(17, 24, 39, 0.95);
        border-right: 1px solid rgba(255, 215, 0, 0.15);
    }
    
    .title-gradient {
        background: linear-gradient(135deg, #FFE066 0%, #D4AF37 50%, #AA7C11 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        text-shadow: 0 4px 10px rgba(212, 175, 55, 0.15);
        margin-bottom: 5px;
    }
    
    .subtitle {
        color: #a0aec0;
        font-size: 1.1rem;
        margin-bottom: 25px;
        font-weight: 300;
    }
    
    .counter-card {
        background: linear-gradient(145deg, #151c2e, #0e1320);
        border: 2px solid rgba(212, 175, 55, 0.35);
        border-radius: 16px;
        padding: 25px;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(212, 175, 55, 0.1);
        margin-top: 15px;
        transition: all 0.3s ease;
    }
    
    .counter-card:hover {
        box-shadow: 0 8px 40px 0 rgba(212, 175, 55, 0.2);
        border-color: rgba(212, 175, 55, 0.55);
    }
    
    .counter-title {
        color: #cbd5e1;
        font-size: 1.2rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    
    .counter-value {
        color: #ffd700;
        font-size: 3.5rem;
        font-weight: 800;
        text-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
    }
    
    .status-container {
        display: flex;
        align-items: center;
        gap: 10px;
        background: rgba(255, 255, 255, 0.05);
        padding: 10px 15px;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
    }
    
    .dot-active {
        height: 10px;
        width: 10px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 10px #10B981;
        animation: pulse 1.5s infinite alternate;
    }
    
    .dot-inactive {
        height: 10px;
        width: 10px;
        background-color: #6B7280;
        border-radius: 50%;
        display: inline-block;
    }
    
    @keyframes pulse {
        0% { transform: scale(0.9); opacity: 0.5; }
        100% { transform: scale(1.2); opacity: 1; box-shadow: 0 0 15px #10B981; }
    }
    </style>
""", unsafe_allow_html=True)

# Settings Panel
st.sidebar.markdown("<h2 style='color:#ffd700; font-weight:600; margin-bottom: 0px;'>Settings</h2>", unsafe_allow_html=True)
st.sidebar.write("---")

conf_slider = st.sidebar.slider("Confidence Threshold", min_value=0.0, max_value=1.0, value=0.60, step=0.05)
iou_slider = st.sidebar.slider("IoU Threshold", min_value=0.0, max_value=1.0, value=0.45, step=0.05)

st.sidebar.write("")
st.sidebar.markdown("<h3 style='color:#ffd700; font-weight:600;'>System Status</h3>", unsafe_allow_html=True)

if "camera_running" not in st.session_state:
    st.session_state.camera_running = False

if st.session_state.camera_running:
    status_html = '<div class="status-container"><span class="dot-active"></span><span style="font-weight:600; color:#10B981;">Active Feed (Scanning)</span></div>'
else:
    status_html = '<div class="status-container"><span class="dot-inactive"></span><span style="font-weight:600; color:#9CA3AF;">System Standby</span></div>'

st.sidebar.markdown(status_html, unsafe_allow_html=True)

st.sidebar.write("")
st.sidebar.markdown("<h3 style='color:#ffd700; font-weight:600;'>About</h3>", unsafe_allow_html=True)
st.sidebar.markdown("""
This system leverages **YOLO11n** computer vision technology to detect and count Egyptian currency bills in real-time.

* **Supported Bills**: 5, 10, 20, 50, 100, 200 EGP.
* **Dual-Side Capture**: Mapped for front and back faces.
* **Engineered by**: Senior AI Systems Engineer.
""")

# Main Content
st.markdown('<div class="title-gradient">Egyptian Currency Counter</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Real-time object detection and valuation system leveraging YOLO11</div>', unsafe_allow_html=True)

# Exact true currency mapping dictionary
currency_mapping = {
    4: 100,  # 100 EGP (Face Front) 
    11: 100, # 100 EGP (Face Back) 
    8: 50,   # 50 EGP (Face Front) 
    2: 50,   # 50 EGP (Face Back) 
    6: 200,  # 200 EGP (Face Front) 
    7: 200,  # 200 EGP (Face Back) 
    9: 20,   # 20 EGP (Face Front) 
    5: 20,   # 20 EGP (Face Back) 
    10: 5,   # 5 EGP (Face Front) 
    1: 5,    # 5 EGP (Face Back) 
    0: 10,   # 10 EGP (Face Front)
    3: 10,   # 10 EGP (Face Back)
}

model_path = get_model_path()
model, load_success, load_message = load_yolo_model(model_path)

if not load_success:
    st.error(f"Failed to load weights: {load_message}")
else:
    st.write("")
    btn_col1, btn_col2 = st.columns([1, 4])
    with btn_col1:
        if st.session_state.camera_running:
            stop_btn = st.button("🔴 Stop Camera Feed", use_container_width=True)
            if stop_btn:
                st.session_state.camera_running = False
                st.rerun()
        else:
            start_btn = st.button("🟢 Start Camera Feed", use_container_width=True)
            if start_btn:
                st.session_state.camera_running = True
                st.rerun()

    frame_placeholder = st.empty()
    counter_placeholder = st.empty()
    
    counter_placeholder.markdown("""
        <div class="counter-card">
            <div class="counter-title">Total Detected Amount</div>
            <div class="counter-value">0 EGP</div>
        </div>
    """, unsafe_allow_html=True)

    if st.session_state.camera_running:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not cap.isOpened():
            st.error("Error: Could not open camera.")
            st.session_state.camera_running = False
            st.rerun()
            
        try:
            while st.session_state.camera_running:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # التعديل الجوهري: تحويل الفريم لـ RGB أولاً قبل تمريره للموديل وللرسم 🎯
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # تمرير الفريم الـ RGB المصلح للموديل
                results = model(frame_rgb, conf=conf_slider, iou=iou_slider, verbose=False)
                
                total_amount = 0
                
                for box in results[0].boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    coin_value = currency_mapping.get(class_id, 0)
                    total_amount += coin_value
                    
                    box_color = get_denomination_color(coin_value)
                    
                    # الرسم مباشرة على فريم الـ RGB المصلح الألوان
                    cv2.rectangle(frame_rgb, (x1, y1), (x2, y2), box_color, 2)
                    
                    display_text = f"{coin_value} EGP ({confidence:.2f})"
                    label_size, base_line = cv2.getTextSize(display_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    y1_top = max(y1, label_size[1] + 10)
                    
                    cv2.rectangle(frame_rgb, (x1, y1_top - label_size[1] - 4), (x1 + label_size[0] + 4, y1_top + base_line - 4), box_color, -1)
                    cv2.putText(frame_rgb, display_text, (x1 + 2, y1_top - 4),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0) if sum(box_color) > 380 else (255, 255, 255), 1, cv2.LINE_AA)
                
                # عرض الفريم الـ RGB مباشرة بدون لف ودوران
                frame_placeholder.image(frame_rgb, channels="RGB", use_column_width=True)
                
                # تحديث المجموع
                counter_placeholder.markdown(f"""
                    <div class="counter-card">
                        <div class="counter-title">Total Detected Amount</div>
                        <div class="counter-value">{total_amount} EGP</div>
                    </div>
                """, unsafe_allow_html=True)
                
                time.sleep(0.01)
                
        except Exception as loop_err:
            st.error(f"Inference Loop Error: {str(loop_err)}")
        finally:
            cap.release()
    else:
        frame_placeholder.info("Camera feed stopped. Click the 'Start Camera Feed' button above to initialize.")