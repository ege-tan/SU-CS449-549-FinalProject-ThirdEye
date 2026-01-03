from flask import Flask, request, jsonify 
import cv2 
import numpy as np 
import base64 
from datetime import datetime 
import pyttsx3 
import threading 

app = Flask(__name__) 

last_spoken_command = None 
speech_lock = threading.Lock() 

def speak_async(text): 
    def _speak(): 
        if speech_lock.acquire(blocking=False): 
            try: 
                engine = pyttsx3.init() 
                engine.setProperty('rate', 140)  
                engine.say(text) 
                engine.runAndWait() 
                engine.stop()  
            except Exception as e: 
                print(f"Voice Error: {e}") 
            finally: 
                speech_lock.release() 
             
    thread = threading.Thread(target=_speak) 
    thread.start() 

YELLOW_LOWER = np.array([20, 100, 100]) 
YELLOW_UPPER = np.array([35, 255, 255]) 

FRAME_WIDTH = 320 
FRAME_HEIGHT = 240 

def analyze_surface_pattern(mask, original_image): 
     
    masked_img = cv2.bitwise_and(original_image, original_image, mask=mask) 
    gray = cv2.cvtColor(masked_img, cv2.COLOR_BGR2GRAY) 
     
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)) 
    enhanced_gray = clahe.apply(gray) 
     
    blurred = cv2.GaussianBlur(enhanced_gray, (5, 5), 0) 
     
    edges = cv2.Canny(blurred, 40, 100) 
     
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 
     
    dot_count = 0 
     
    for cnt in contours: 
        x, y, w, h = cv2.boundingRect(cnt) 
         
        if 2 < w < 30 and 2 < h < 30: 
            aspect_ratio = float(w)/h 
            if 0.5 < aspect_ratio < 2.0:  
                dot_count += 1 

    total_yellow_area = cv2.countNonZero(mask) 
     
    print(f"DEBUG -> Detected Dot Count: {dot_count}") 
     
    if total_yellow_area == 0:  
        return 'none', np.zeros_like(gray) 
     
    if dot_count > 15: 
        return 'dots', edges 
         
    else: 
        return 'lines', edges 

def detect_yellow_path(image): 
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) 
    image = cv2.resize(image, (FRAME_WIDTH, FRAME_HEIGHT)) 
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV) 
     
    mask = cv2.inRange(hsv, YELLOW_LOWER, YELLOW_UPPER) 
     
    kernel = np.ones((5, 5), np.uint8) 
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel) 
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel) 
     
    yellow_pixels = cv2.countNonZero(mask) 
    total_pixels = FRAME_WIDTH * FRAME_HEIGHT 
    confidence = (yellow_pixels / total_pixels) * 100 
     
    empty_debug = np.zeros((FRAME_HEIGHT, FRAME_WIDTH), dtype=np.uint8) 

    if confidence < 1.0:  
        return {'found': False, 'position': 'unknown', 'type': 'none', 'offset': 0, 'debug_edges': empty_debug} 
     
    surface_type, edges_debug = analyze_surface_pattern(mask, image) 
     
    lower_half = mask[FRAME_HEIGHT // 2:, :]  
    moments = cv2.moments(lower_half) 
     
    offset = 0 
    position = 'center' 
     
    if moments['m00'] > 0: 
        cx = int(moments['m10'] / moments['m00']) 
        center_x = FRAME_WIDTH // 2 
        offset = (cx - center_x) / center_x 
         
        if offset < -0.25: position = 'left' 
        elif offset > 0.25: position = 'right' 
        else: position = 'center' 
         
    return { 
        'found': True,  
        'position': position,  
        'type': surface_type,  
        'offset': round(offset, 2),  
        'confidence': round(confidence, 2), 
        'debug_edges': edges_debug 
    } 

def get_navigation_command(detection_result): 
    if not detection_result['found']: 
        return {'command': 'stop', 'message': 'Path lost.', 'severity': 'warning'} 
     
    if detection_result['type'] == 'dots': 
        return {'command': 'intersection', 'message': 'Intersection detected.', 'severity': 'alert'} 
     
    position = detection_result['position'] 
    if position == 'center': 
        return {'command': 'straight', 'message': 'Go straight.', 'severity': 'info'} 
    elif position == 'left': 
        return {'command': 'left', 'message': 'Stay on left.', 'severity': 'info'} 
    else:  
        return {'command': 'right', 'message': 'Stay on right.', 'severity': 'info'} 

@app.route('/analyze', methods=['POST']) 
def analyze_image(): 
    global last_spoken_command 
    try: 
        image = None 
        if 'image' in request.files: 
            file = request.files['image'] 
            nparr = np.frombuffer(file.read(), np.uint8) 
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR) 
        elif request.is_json and 'image' in request.json: 
            img_data = base64.b64decode(request.json['image']) 
            nparr = np.frombuffer(img_data, np.uint8) 
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR) 
             
        if image is None: return jsonify({'error': 'No image received'}), 400 
         
        detection = detect_yellow_path(image) 
        navigation = get_navigation_command(detection) 
         
        if navigation['command'] != last_spoken_command or navigation['command'] == 'stop': 
            speak_async(navigation['message']) 
            last_spoken_command = navigation['command'] 
             
            if navigation['command'] != 'stop':  
                 print(f"{navigation['message']}") 
            elif navigation['command'] == 'stop': 
                 print(f"{navigation['message']}") 

        debug_img = cv2.resize(image, (FRAME_WIDTH, FRAME_HEIGHT)) 
        color = (0, 0, 255) if detection['type'] == 'dots' else (0, 255, 0) 
        cv2.putText(debug_img, f"TYPE: {detection['type'].upper()}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2) 
        cv2.putText(debug_img, f"DIR: {detection['position'].upper()}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2) 
        cv2.imwrite("debug1.jpg", debug_img) 

        if 'debug_edges' in detection: 
            edges_img = detection['debug_edges'] 
            edges_color = cv2.cvtColor(edges_img, cv2.COLOR_GRAY2BGR) 
             
            if detection['type'] == 'dots': 
                edges_color[edges_img > 0] = [0, 0, 255] 
            else: 
                edges_color[edges_img > 0] = [0, 255, 0] 

            cv2.imwrite("debug2.jpg", edges_color) 
         
        return jsonify({ 
            'success': True, 
            'detection': {k: v for k, v in detection.items() if k != 'debug_edges'}, 
            'navigation': navigation 
        }) 
     
    except Exception as e: 
        print(f"Error: {e}") 
        return jsonify({'success': False}), 500 

@app.route('/health', methods=['GET']) 
def health_check(): 
    return jsonify({'status': 'running'}) 

if __name__ == '__main__': 
    app.run(host='0.0.0.0', port=5000, debug=True)