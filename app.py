import cv2
import numpy as np
import serial  # Ajouter pySerial pour la communication série

# Ouvrir la connexion série avec l'Arduino
arduino_port = '/dev/ttyACM0'  # Modifier selon le port correct (ex: COM3 sous Windows)
baud_rate = 9600
ser = serial.Serial(arduino_port, baud_rate)

def send_to_arduino(data):
    ser.write(f"{data}\n".encode())  # Envoyer les données à l'Arduino

# Initialiser la caméra
cap = cv2.VideoCapture(2)
if not cap.isOpened():
    print("Impossible d'accéder à la caméra")
    exit()

def load_annotations(file_path, image_width, image_height):
    with open(file_path, 'r') as f:
        lines = f.readlines()
    annotations = []
    for line in lines:
        class_id, x_center, y_center, width, height = map(float, line.split())
        # Convertir les coordonnées normalisées en pixels
        x_center *= image_width
        y_center *= image_height
        width *= image_width
        height *= image_height
        annotations.append((x_center, y_center, width, height))
    return annotations

def extract_pipes(contours):
    """Retourne une liste de tuyaux détectés sous forme de dicts (centre, longueur, angle, contour)."""
    pipes = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 200:
            rect = cv2.minAreaRect(contour)
            width, height = rect[1]
            aspect_ratio = min(width, height) / max(width, height)
            if width > 5 and height > 0 and aspect_ratio < 0.3:
                pipe = {
                    'center': rect[0],
                    'length': max(width, height),
                    'angle': rect[2],
                    'contour': contour,
                    'box': cv2.boxPoints(rect)
                }
                pipes.append(pipe)
    return pipes


cv2.namedWindow('Caméra - Tuyau détecté', cv2.WINDOW_NORMAL)

# Charger les annotations
annotation_file = '/home/mcrai/Desktop/CAM/datasets/labels/Capture du 2024-09-06 10-23-16.txt'
ret, frame = cap.read()
image_height, image_width = frame.shape[:2]
annotations = load_annotations(annotation_file, image_width, image_height)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Erreur lors de la capture de l'image")
        break

    # Traitement d'image pour la détection des contours
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY_INV)
    
    kernel = np.ones((5, 5), np.uint8)
    cleaned_thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(cleaned_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pipes = extract_pipes(contours)
    
    if pipes:
        # Trier par longueur décroissante (ou autre critère)
        pipes.sort(key=lambda p: p['length'], reverse=True)
        main_pipe = pipes[0]
        x_center, y_center = map(int, main_pipe['center'])
        length = main_pipe['length']
        angle = main_pipe['angle']
        box = np.int0(main_pipe['box'])
        cv2.drawContours(frame, [box], 0, (0, 255, 0), 2)
        cv2.putText(frame, f"Longueur: {length:.1f} px", (x_center, y_center - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.circle(frame, (x_center, y_center), 5, (255, 0, 0), -1)
        cv2.putText(frame, f"X:{x_center} Y:{y_center} Angle:{angle:.1f}", (x_center, y_center + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        print(f"Tuyau détecté - Longueur: {length:.1f} px, X: {x_center}, Y: {y_center}, Angle: {angle:.1f}")
        # Envoyer toutes les infos à l'Arduino au format attendu
        send_to_arduino(f"X:{x_center},Y:{y_center},Length:{length:.1f},Angle:{angle:.1f}")
        # Lecture du retour d'état de l'Arduino
        try:
            status_line = ser.readline().decode().strip()
            if status_line.startswith("STATUS:"):
                print(f"[Arduino] {status_line}")
        except Exception as e:
            print(f"Erreur lecture retour Arduino : {e}")
    else:
        print("Aucun tuyau détecté")
    
    # Dessiner les annotations chargées depuis le fichier
    for (x_center, y_center, width, height) in annotations:
        x1 = int(x_center - width / 2)
        y1 = int(y_center - height / 2)
        x2 = int(x_center + width / 2)
        y2 = int(y_center + height / 2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
    
    # Afficher le résultat dans la fenêtre
    cv2.imshow('Caméra - Tuyau détecté', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Libérer les ressources
cap.release()
cv2.destroyAllWindows()
ser.close()  # Fermer la connexion série
