import time
import logging
from hardware import OV5647Controller

class PresenceDetector:
    def __init__(self):
#         self.hardware = HardwareController()OV5647Controller
        self.hardware = OV5647Controller()
        self.is_present = False
        self.debounce_time = 0.5
        self.last_change = 0.0
        
    def _state_changed(self, state):
        current_time = time.time()
        if current_time - self.last_change > self.debounce_time:
            if state != self.is_present:
                self.is_present = state
                self.last_change = current_time
                self._update_led()
                self._log_state()

    def _update_led(self):
        self.hardware.status_led.value = int(self.is_present)
        
    def _log_state(self):
        status = "youren" if self.is_present else "renzou"
        logging.info(status)
        
    def monitor(self):
        try:
            while True:
                current_state = self.hardware.ir_sensor.is_active
                self._state_changed(current_state)
                time.sleep(0.1)
            
        except KeyboardInterrupt:
            self.hardware.cleanup()
            print("\n jiankong tingzhi")     
        