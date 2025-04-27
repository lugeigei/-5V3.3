import threading
import logging
import cv2
import time
from hardware import OV5647Controller
from face_detector import FaceDetector
from face_recognitiona import FaceRecognizer
from concurrent.futures import ThreadPoolExecutor

class FaceAccessSystem:
    def __init__(self):
        self.hardware = OV5647Controller()
        self.detector = FaceDetector()
        self.recognizer = FaceRecognizer()
        self.running = True
        self.lock = threading.Lock()
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.frame_buffer = []
        
        self.buffer_size = 10
        
        self.processing = False
        self.last_update = 0
        
        self.log_callback = None
        
        self.disable_native_window = False
        
        self.hardware_lock = threading.Lock()
        
        self.failed_attempts = 0
        self.max_attempts = 3
        self.on_auth_failed_callback = None
        
        self.sensor_thread = threading.Thread(target=self._monitor_sensor, daemon=True)
        self.sensor_thread.start()
        
        logging.basicConfig(
            level=logging.INFO,
            format='[%(asctime)s] %(levelname)s: %(message)s',
            handlers=[
                logging.FileHandler('access.log'),
                logging.StreamHandler()
            ]
        )
    
    def _monitor_sensor(self):
        debounce_time = 2.0
        last_trigger = 0
        while self.running:
            current_state = self.hardware.ir_sensor.is_active
            current_time = time.time()
            
            if current_state and (current_time - last_trigger) > debounce_time:
                last_trigger = current_time
                if not self.processing:
                    self._trigger_recognition()
                    
            time.sleep(0.1)
    
    def _trigger_recognition(self):
        self.processing = True
        self.executor.submit(self._async_recognize)
    
    def set_auth_failed_callback(self, callback):
        self.on_auth_failed_callback = callback
    
    def capture_frame_safely(self):
        with self.hardware_lock:
            return self.hardware.capture_frame()
    
    def run_without_window(self):
        try:
            logging.info("xitong qidong...")
            while self.running:
#                 frame = self.hardware.capture_frame()
                frame = self.capture_frame_safely() 
                if frame is not None:
                    self.frame_buffer.append(frame.copy())
                    if len(self.frame_buffer) > self.buffer_size:
                        self.frame_buffer = self.frame_buffer[-self.buffer_size:]
                        #self.frame_buffer.pop(0)
                if not self.running:
                    break
                #
                key = cv2.waitKey(1)
                if key == ord('q'):
                    self.shutdown()
                    break
#                 elif key == 13 and not self.processing:
#                     self.processing = True
#                     logging.info("kaishishibei...")
#                     self.executor.submit(self._async_recognize)
                
                
        except Exception as e:
            logging.error(f"yunxing yichang: {str(e)}")
        finally:
            self.shutdown()
    
    def _async_recognize(self):
        try:
            
            if len(self.frame_buffer) < 3:
                logging.warning("huotijianc yao3zhen")
                return
            
#             liveness_result = self.recognizer.check_liveness(self.frame_buffer[-3:])
#             if not liveness_result:
#                 logging.warning("bushi huo ti")
#                 self.hardware.buzzer_alert()
#                 return
            current_frame = self.frame_buffer[-1]
            faces_coords = self.detector.detect_faces(current_frame, return_coords=True)
            if not faces_coords:
                logging.warning("wei jiance dao renlian")
                self.hardware.buzzer_alert()
                return

            x1, y1, x2, y2 = faces_coords[0]
            face_roi = current_frame[y1:y2, x1:x2]
            #user_id = self.recognizer.recognize(user_id)
            user_id = self.recognizer.recognize(face_roi)

            if user_id:
                logging.info(f"shibei chenggong :yonghu {user_id}")
                self.hardware.led_success()
                self.failed_attempts = 0 
            else:
                logging.warning("weizhi yonghu")
                self.failed_attempts += 1
                if self.failed_attempts >= self.max_attempts:
                    if self.on_auth_failed_callback:
                        self.on_auth_failed_callback()
                    self.failed_attempts = 0
                    
                self.hardware.buzzer_alert()
        except Exception as e:
            logging.error(f"chuli yichang: {str(e)}")
        finally:
            self.processing = False
            

        
        
    def run(self):
        try:
            logging.info("""
                -----------------------------------
                renlianshibiexitong qidong...
                anhuiche kaishi shibie...
                ---------------------------------------""")
            cv2.namedWindow('Camera Preview', cv2.WINDOW_NORMAL)
            while self.running:
                frame = self.hardware.capture_frame()
                if frame is not None:
                    display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    cv2.imshow('Camera Preview', frame)
                    #cv2.imshow('Camera Preview', display_frame)
                    
                    self.frame_buffer.append(frame.copy())
                    if len(self.frame_buffer) > 5:
                        self.frame_buffer.pop(0)
                        
                key = cv2.waitKey(1)
                if key == ord('q'):
                    self.shutdown()
                    break
                elif key == 13 and not self.processing:
                    self.processing = True
                    logging.info("kaishishibei...")
                    self.executor.submit(self._async_recognize)
    
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        self.running = False
        self.hardware.cleanup()
        cv2.destroyAllWindows()
        logging.info("xitong guanbi")
        
if __name__ == "__main__":
    system = FaceAccessSystem()
    system.run()
