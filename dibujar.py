import cv2
import mediapipe as mp
import numpy as np
import datetime
from supabase import create_client, Client

# --- 1. CONFIGURACIÓN DE SUPABASE ---
# Reemplaza con tus credenciales de la consola de Supabase (Settings -> API)
SUPABASE_URL = "https://bfnarvhyskmsotmoncqy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJmbmFydmh5c2ttc290bW9uY3F5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMxOTk3NjYsImV4cCI6MjA4ODc3NTc2Nn0.D58bwiR7_-zBmICD4zSHPO554tq4RrI4g_-qHCX2keE"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def upload_to_supabase(canvas_img):
    """Sube la imagen al bucket 'dibujos' y registra la URL en una tabla"""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"dibujo_{timestamp}.png"

    # Convertir la imagen de OpenCV (numpy array) a bytes PNG
    _, buffer = cv2.imencode('.png', canvas_img)
    file_bytes = buffer.tobytes()

    try:
        print(f"Subiendo {file_name} a Supabase...")
        
        # A. Subir al Storage (Asegúrate de que el bucket 'dibujos' sea PÚBLICO)
        supabase.storage.from_("dibujos").upload(
            path=file_name,
            file=file_bytes,
            file_options={"content-type": "image/png"}
        )

        # B. Obtener la URL pública
        url_data = supabase.storage.from_("dibujos").get_public_url(file_name)
        
        # C. (Opcional) Guardar registro en una tabla llamada 'galeria'
        # supabase.table("galeria").insert({"nombre": file_name, "url": url_data}).execute()
        
        print(f"✅ ¡Éxito! Imagen disponible en:\n{url_data}")
        
    except Exception as e:
        print(f"❌ Error en la subida: {e}")

# --- 2. CONFIGURACIÓN DE MEDIAPIPE Y VARIABLES ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.85, min_tracking_confidence=0.8)
mp_draw = mp.solutions.drawing_utils

# Colores (BGR): Azul, Verde, Rojo, Amarillo, Blanco, Negro, Naranja, Borrador
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (0, 255, 255), (255, 255, 255), (25, 25, 25), (0, 165, 255), (0, 0, 0)]
color_idx = 0
brush_thickness = 5
eraser_thickness = 50

canvas = None
px, py = 0, 0 # Coordenadas anteriores

# --- 3. BUCLE PRINCIPAL ---
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success: break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    if canvas is None:
        canvas = np.zeros((h, w, 3), np.uint8)

    # Procesar mano
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    # Dibujar Interfaz de Usuario (Menú de Colores)
    cv2.rectangle(frame, (0, 0), (w, 80), (30, 30, 30), -1)
    etiquetas = ["Azul", "Verde", "Rojo", "Amar.", "Blanco", "Negro", "Naran.", "Goma"]
    for i, col in enumerate(colors):
        cv2.rectangle(frame, (10 + i*80, 10), (80 + i*80, 70), col, -1)
        # Usar texto oscuro para colores claros (amarillo, blanco) y blanco para el resto
        text_color = (0, 0, 0) if i in [3, 4] else (255, 255, 255)
        cv2.putText(frame, etiquetas[i], (15 + i*80, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1)

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Puntos clave: Índice (8) y Corazón (12)
            idx_tip = hand_landmarks.landmark[8]
            mid_tip = hand_landmarks.landmark[12]
            
            ix, iy = int(idx_tip.x * w), int(idx_tip.y * h)
            mx, my = int(mid_tip.x * w), int(mid_tip.y * h)

            # Verificar si los dedos están levantados
            fingers = []
            fingers.append(1 if idx_tip.y < hand_landmarks.landmark[6].y else 0)
            fingers.append(1 if mid_tip.y < hand_landmarks.landmark[10].y else 0)

            # MODO SELECCIÓN: Índice y Corazón arriba (Para elegir color o mover sin pintar)
            if fingers[0] and fingers[1]:
                px, py = 0, 0
                cv2.circle(frame, (ix, iy), 15, colors[color_idx], cv2.FILLED)
                
                if iy < 80: # Si el dedo está en el área del menú
                    for c_i in range(len(colors)):
                        if 10 + c_i*80 < ix < 80 + c_i*80:
                            color_idx = c_i

            # MODO DIBUJO: Solo Índice arriba
            elif fingers[0] and not fingers[1]:
                if px == 0 and py == 0:
                    px, py = ix, iy

                thickness = eraser_thickness if color_idx == 7 else brush_thickness
                cv2.line(canvas, (px, py), (ix, iy), colors[color_idx], thickness)
                
                px, py = ix, iy
            else:
                px, py = 0, 0

    # Fusionar Canvas con Cámara
    img_gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, img_inv = cv2.threshold(img_gray, 20, 255, cv2.THRESH_BINARY_INV)
    img_inv = cv2.cvtColor(img_inv, cv2.COLOR_GRAY2BGR)
    frame = cv2.bitwise_and(frame, img_inv)
    frame = cv2.bitwise_or(frame, canvas)

    cv2.imshow("VisionCanvas + Supabase", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'): # Salir
        break
    elif key == ord('c'): # Limpiar lienzo
        canvas = np.zeros((h, w, 3), np.uint8)
        print("Pantalla limpia.")
    elif key == ord('s'): # Guardar en Supabase
        upload_to_supabase(canvas)

cap.release()
cv2.destroyAllWindows()