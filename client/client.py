import requests 
import time 
import io 
import os 
from datetime import datetime 

try: 
    from picamera2 import Picamera2 
    PI_CAMERA = True 
    print("Pi Camera module found.") 
except ImportError: 
    import cv2 
    PI_CAMERA = False 
    print("Pi Camera module not found, using webcam.") 

try: 
    import pyttsx3 
    TTS_AVAILABLE = True 
except ImportError: 
    TTS_AVAILABLE = False 
    print("pyttsx3 not found, audio output disabled.") 


class YellowPathClient: 
    def __init__(self, server_url="http://localhost:5000"): 
        self.server_url = server_url 
        self.running = False 
        self.last_command = None 
        self.repeat_threshold = 3  
        self.command_count = 0 
         
        if PI_CAMERA: 
            self.camera = Picamera2() 
            config = self.camera.create_still_configuration( 
                main={"size": (640, 480), "format": "RGB888"} 
            ) 
            self.camera.configure(config) 
            self.camera.start() 
            time.sleep(1)  
        else: 
            self.camera = cv2.VideoCapture(0) 
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640) 
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) 
         
        if TTS_AVAILABLE: 
            self.tts = pyttsx3.init() 
            self.tts.setProperty('rate', 150)  
            voices = self.tts.getProperty('voices') 
            for voice in voices: 
                if 'turkish' in voice.name.lower() or 'tr' in voice.id.lower(): 
                    self.tts.setProperty('voice', voice.id) 
                    break 
         
        print(f"Client started. Server: {self.server_url}") 
     
    def capture_image(self): 
        if PI_CAMERA: 
            image = self.camera.capture_array() 
            import cv2 
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) 
            return image 
        else: 
            ret, frame = self.camera.read() 
            if ret: 
                return frame 
            return None 
     
    def send_to_server(self, image): 
        try: 
            import cv2 
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 80]) 
             
            files = {'image': ('frame.jpg', buffer.tobytes(), 'image/jpeg')} 
            response = requests.post( 
                f"{self.server_url}/analyze", 
                files=files, 
                timeout=2 
            ) 
             
            if response.status_code == 200: 
                return response.json() 
            else: 
                print(f"Server error: {response.status_code}") 
                return None 
                 
        except requests.exceptions.Timeout: 
            print("Server did not respond (timeout)") 
            return None 
        except requests.exceptions.ConnectionError: 
            print("Could not connect to the server") 
            return None 
        except Exception as e: 
            print(f"Error: {e}") 
            return None 
     
    def speak(self, message): 
        if TTS_AVAILABLE: 
            print(f"{message}") 
            self.tts.say(message) 
            self.tts.runAndWait() 
        else: 
            print(f"[AUDIO] {message}") 
     
    def should_speak(self, command): 
        if command != self.last_command: 
            self.last_command = command 
            self.command_count = 1 
            return True 
        else: 
            self.command_count += 1 
            if self.command_count >= self.repeat_threshold: 
                self.command_count = 0 
                return True 
        return False 
     
    def process_response(self, response): 
        if not response or not response.get('success'): 
            return 
         
        navigation = response.get('navigation', {}) 
        command = navigation.get('command', '') 
        message = navigation.get('message', '') 
        severity = navigation.get('severity', 'info') 
         
        if severity == 'warning' or self.should_speak(command): 
            self.speak(message) 
     
    def run(self, interval=1.0): 
        self.running = True 
        print(f"\nSystem started. An image will be analyzed every {interval} seconds.") 
        print("Press Ctrl+C to stop\n") 
         
        self.speak("System ready. You can start walking.") 
         
        try: 
            while self.running: 
                start_time = time.time() 
                 
                image = self.capture_image() 
                if image is None: 
                    print("Failed to capture image!") 
                    time.sleep(interval) 
                    continue 
                 
                response = self.send_to_server(image) 
                 
                if response: 
                    self.process_response(response) 
                 
                elapsed = time.time() - start_time 
                if elapsed < interval: 
                    time.sleep(interval - elapsed) 
                     
        except KeyboardInterrupt: 
            print("\nStopped.") 
        finally: 
            self.cleanup() 
     
    def cleanup(self): 
        self.running = False 
        if PI_CAMERA: 
            self.camera.stop() 
        else: 
            self.camera.release() 
        print("Resources cleaned up.") 


def check_server(url): 
    try: 
        response = requests.get(f"{url}/health", timeout=3) 
        return response.status_code == 200 
    except: 
        return False 


if __name__ == '__main__': 
    import argparse 
     
    parser = argparse.ArgumentParser(description='Yellow Path Guidance Client') 
    parser.add_argument('--server', type=str, default='http://localhost:5000', 
                        help='Server URL (default: http://localhost:5000)') 
    parser.add_argument('--interval', type=float, default=1.0, 
                        help='Image capture interval - seconds (default: 1.0)') 
     
    args = parser.parse_args() 
     
    print("=" * 50) 
    print("Yellow Path Guidance System - Client") 
    print("=" * 50) 
     
    print(f"Checking server: {args.server}") 
    if not check_server(args.server): 
        print("Could not connect to the server! Make sure the server is running.") 
        print(f"   Expected address: {args.server}") 
        exit(1) 
     
    print("Server connection successful\n") 
     
    client = YellowPathClient(server_url=args.server) 
    client.run(interval=args.interval)