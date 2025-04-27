import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import logging
import cv2
import time
import numpy as np
from main import FaceAccessSystem
from hardware import OV5647Controller
from face_detector import FaceDetector
from face_recognitiona import FaceRecognizer


class ControlPanel:
    def __init__(self, master):
        self.master = master
        master.title("zhineng menjin xitong")
        master.geometry("800x600")
        
        self.is_running = True
        
        self.system_running = threading.Event()
        self.register_running = False
        self.register_complete = tk.BooleanVar(value=False)
        
        self.system = FaceAccessSystem()
        self.system.disable_native_window = True
        
        
        self.preview_thread = threading.Thread(target=self.update_preview)
        self.preview_thread.daemon = True
        self.preview_thread.start()
        
        #self.system.log_callback = self.add_event_log
        
        self.registration_preview_label = ttk.Label(self.master)
        self.registration_preview_label.pack_forget()
        
        master.protocol("WM_DELETE_WINDOW", self.on_close)
        #self.master.bind("<Return>", self._on_return_pressed)
        
#         self.failed_attempts = 0
#         self.max_attempts = 3
        self.password = "1234"
        self.input_buffer = "" 

        self.main_container = ttk.Frame(master)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.create_widgets()
        self.create_password_ui()
        self.system.set_auth_failed_callback(self.show_password_auth)
    
        
        
        self.preview_thread = threading.Thread(target=self.update_preview, daemon=True)
        self.preview_thread.start()
        
    def create_password_ui(self):
        self.auth_frame = ttk.Frame(self.main_container)

        self.pwd_display = ttk.Label(self.auth_frame, text="",
                                     font=('Arial', 16))
        self.pwd_display.grid(row=0, column=0, columnspan=4, pady=10)
        buttons = [
            ('1', 1, 0), ('2', 1, 1), ('3', 1, 2), ('<--', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('C', 2, 3),
            ('7', 3, 0), ('8', 3, 1), ('9', 3, 2), ('L', 3, 3),
            ('*', 4, 0), ('0', 4, 1), ('#', 4, 2), ('Y', 4, 3)
        ]
        for (text, row, col) in buttons:
            if text == '':
                continue
            btn = ttk.Button(
                self.auth_frame,
                text=text,
                width=4,
                command=lambda t=text: self._on_key_pressed(t)
            )
            btn.grid(row=row, column=col, padx=5, pady=5)
        
        #self.auth_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.auth_frame.pack(expand=True, pady=20, anchor=tk.CENTER) 
        self.auth_frame.pack_forget()
        

    def _on_key_pressed(self, key):
        if key == 'Y':
            self.verify_password()
        elif key =='C':
            self.input_buffer = ""
        elif key == '<--':
            self.input_buffer = self.input_buffer[:-1]
        else:
            if key in {'*', '#', 'L'} or key.isdigit():
                if len(self.input_buffer) < 6:
                    self.input_buffer += key
        display = '*' * len(self.input_buffer)
        self.pwd_display.config(text=display)
    
    def show_password_auth(self):
        def reset_and_show_auth():
            self.input_buffer = ""
            self.pwd_display.config(text="")
            self.preview_label.pack_forget()
            self.auth_frame.pack(pady=20)
            #self.auth_frame.pack(pady=20)
            self.auth_frame.lift()
            #self.pwd_entry.focus_set(),
            self.main_container.update_idletasks()
            #self.master.update()
        self.master.after(0, reset_and_show_auth)
      
    
    def verify_password(self):
        #input_pwd = self.pwd_entry.get()
        if self.input_buffer == self.password:
            self.system.hardware.led_success()
            messagebox.showinfo("yanzheng chenggong","mima zhengque!",
                                parent=self.master)
            self.reset_interface()
        else:
            self.system.hardware.buzzer_alert()
            messagebox.showinfo("yanzheng shibai","mima cuowu!",
                                parent=self.master)
#             self.pwd_entry.delete(0, tk.END)
            self.input_buffer = ""
            self.pwd_display.config(text="")
            
    def reset_interface(self):
        self.auth_frame.pack_forget()
        self.preview_label.pack(pady=10, fill=tk.BOTH, expand=True)
        
        #self.main_container.pack_propagate(True)
        self.main_container.update_idletasks()
        self.master.update()
    
    def create_widgets(self):
        #status_frame = ttk.Frame(self.master)
        status_frame = ttk.Frame(self.main_container)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(
            status_frame,
            text="xitongzhuangtai: daiji",
            font=('helvetica',12))
        self.status_label.pack(side=tk.LEFT)
        
        
        self.preview_label = ttk.Label(self.master)
        self.preview_label.pack(pady=10, fill=tk.BOTH,
                                anchor=tk.CENTER)

        
        control_frame = ttk.Frame(self.master)
        #control_frame = ttk.Frame(self.main_container)
        control_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(
            control_frame,
            text="qidong xitong",
            command=self.toggle_system)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="shoudong zhuce",
            command=self.show_register_dialog
        ).pack(side=tk.LEFT, padx=5)
        
        preview_container = ttk.Frame(self.master, width=640, height=480)
        preview_container.pack(pady=10, anchor=tk.CENTER)
        preview_container.pack_propagate(False)
        self.preview_label = ttk.Label(preview_container)
        self.preview_label.pack(fill=tk.BOTH, expand=True)
#         preview_container = ttk.Frame(self.main_container)
#         preview_container.pack(pady=10, fill=tk.BOTH, expand=True)
#         self.preview_label = ttk.Label(preview_container)
#         self.preview_label.pack(fill=tk.BOTH, expand=True)
        
    
        
    def toggle_system(self):
        if not self.system_running.is_set():
            self.system_running.set()
            self.start_btn.config(text="tingzhi xitong")
            self.status_label.config(text="xitong zhuangtai: yunxingzhong")
            self.system_thread = threading.Thread(target=self.start_system)
            self.system_thread.start()
        else:
            self.system.shutdown()

    def start_system(self):
        self.system.running = True
        try:
            #self.master.bind("<Return>", self._on_return_pressed)
            self.system.run_without_window()
        except Exception as e:
            logging.error(f"xitong yunxing yichang: {str(e)}")
    
    
    
#     def _reset_interface(self):
#         self.password_frame.pack_forget()
#         self.preview_label.pack(pady=10, fill=tk.BOTH, expand=True)
#         self.failed_attempts = 0
#         self.system.processing = False
    
#     def _on_return_pressed(self, event):
#         if not self.system.processing:
#             self.system.processing = True
#             self.failed_attempts = 0
#             self.system.executor.submit(self.system._async_recognize)
    
    def shutdown_system(self):
        try:
            #self.master.unbind("<space>")
            self.is_running = False
            self.system.running = False
            self.system_running.clear()
            
            if self.preview_thread.is_alive():
                self.preview_thread.join(timeout=1)
            self.system.running = False
            
            if hasattr(self, 'system_thread') and self.system_thread.is_alive():
                self.system_thread.join(timeout=2)
            
            self.system.hardware.cleanup()
            
        except Exception as e:
            logging.error(f"guanbi xingyichang:{str(e)}")
    
    
    def update_preview(self):
        try:
            while self.is_running and self.master.winfo_exists():
                default_img = np.zeros((480, 640, 3), dtype=np.uint8)
                img = Image.fromarray(default_img)
                imgtk = ImageTk.PhotoImage(image=img)
                
                if self.is_running and self.system.running and hasattr(self.system, 'frame_buffer'):
                    if len(self.system.frame_buffer) > 0:
                        frame = self.system.frame_buffer[-1]
                        #img = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        #display_frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        
                        
                        resized_frame = cv2.resize(frame, (640, 480))
                        #resized_frame = cv2.resize(frame, (label_width, label_height))
                        resized_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
                        
                        img = Image.fromarray(resized_frame)
                        imgtk = ImageTk.PhotoImage(image=img)
                if self.master.winfo_exists():
                    self.preview_label.config(image=imgtk)
                    setattr(self.preview_label, 'image', imgtk)
                    self.master.update_idletasks()
                time.sleep(0.1)
        except Exception as e:
            logging.error(f"liulan chuangkou yichang: {str(e)}")
            
                
    def show_register_dialog(self):
        def start_register():
            try:
                self._prepare_registration()
                user_id = self._get_user_id_dialog()
                if user_id:
                    self._start_face_capture(user_id)
            except Exception as e:
                messagebox.showerror("zhuce cuowu",str(e))
            finally:
                self._cleanup_registration()
        self.master.after(0, start_register)
        
    def _prepare_registration(self):
        self.system.running = False
        self.master.after(0, lambda: (
            self.preview_label.pack_forget(),
            self.registration_preview_label.pack(pady=10, fill=tk.BOTH, expand=True)
            #self.registration_preview_label.pack(pady=10)
        ))
        self.register_running = True
        self.registration_preview_label.update_idletasks()
        threading.Thread(
            target=self.update_register_preview,
            args=(self.system.hardware, FaceDetector()),
            daemon=True
        ).start()
                
    def _get_user_id_dialog(self):
        dialog = tk.Toplevel(self.master)
        dialog.title("yonghu zhuce")
        dialog.transient(self.master)
        dialog.grab_set()
        
        entry = ttk.Entry(dialog, width=20)
        entry.pack(padx=20, pady=10)
        entry.focus_force()
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=5)
        
        user_id = None
        
        def on_confirm():
            nonlocal user_id
            user_id = entry.get().strip()
            if not user_id:
                messagebox.showwarning("shuru cuowu","yonghu id buneng weikong")
                return
            dialog.destroy()
        
        ttk.Button(btn_frame, text="que ren",command=on_confirm).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="qu xiao",command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        
        dialog.bind("<Return>", lambda e: on_confirm())
        
        self._center_window(dialog)
        dialog.wait_window()
        return user_id
    
    def _center_window(self, window):
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'+{x}+{y}')
    
    def update_register_preview(self, hardware, detector):
        try:
            while self.is_running and self.register_running and self.master.winfo_exists():
                frame = hardware.capture_frame()
                if frame is not None and self.is_running:

                    
                    display_frame = frame.copy()
                    faces = detector.detect_faces(display_frame, return_coords=True)
                    if faces:
                        x1, y1, x2, y2 = faces[0]
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), (0,255,0), 2)
                        cv2.putText(display_frame, "Ready to Register", (x1, y1-10),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 2)
                    img = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(cv2.resize(img, (640, 480)))
                    imgtk = ImageTk.PhotoImage(image=img)
                    
                    if self.master.winfo_exists():
                        self.master.after(0, lambda:[
                            self.registration_preview_label.configure(image=imgtk),
                            setattr(self.registration_preview_label, 'image', imgtk)
                        ])
                time.sleep(0.1)
        except Exception as e:
            logging.error(f"zhuce yulan gengxin shibai:{str(e)}")
    
    
    def _start_face_capture(self, user_id):
        self.master.bind("<Return>", lambda e: self._capture_face(user_id))
        self.register_complete.set(False)
        self.master.wait_variable(self.register_complete)
        self.master.unbind("<Return>")
    
    def _capture_face(self, user_id):
        try:
            hardware = self.system.hardware
            detector = FaceDetector()
            recognizer = FaceRecognizer()
            
            frame = hardware.capture_frame()
            faces = detector.detect_faces(frame, return_coords=True)
            
            if faces:
                x1, y1, x2, y2 = faces[0]
                face_roi = frame[y1:y2, x1:x2]
                
                if recognizer.register(user_id, face_roi):
                    messagebox.showinfo("zhuce chenggong",f"yonghu {user_id} zhuce wancheng"
                                        ,parent=self.master)
                else:
                    messagebox.showerror("zhuce shibai","cuowu!"
                                         ,parent=self.master)
            else:
                messagebox.showwarning("jianggao","weijian cedaorenlian"
                                       ,parent=self.master)
        except Exception as e:
            messagebox.showerror("zhuce shibai",f"cuowu: {str(e)}"
                                 ,parent=self.master)          
        finally:
            self.register_complete.set(True)
            self.register_running = False
            for widget in self.master.winfo_children():
                if isinstance(widget, tk.Toplevel):
                    widget.destroy()
    
    
#     def start_sensor_monitor(self):
#         while self.is_running:
#             current_state = self.presence_detector.hardware.ir_sensor.is_active
#             if current_state and not self.system.processing:
#                 self.master.after(0, self.trigger_recognition)
#             time.sleep(0.2)
#             
#     def trigger_recognition(self):
#         if self.system.running and not self.system.processing:
#             self.system.processing = True
#             self.system.executor.submit(self.system._async_recognize)
#

    def _cleanup_registration(self):
        self.master.after(0, lambda: (
            self.registration_preview_label.pack_forget(),
            self.preview_label.pack(pady=10, fill=tk.BOTH, expand=True)
            #self.preview_label.pack(pady=10)
        ))
        self.system.running = True

        
    def on_close(self):
        self.is_running = False
        self.shutdown_system()
        self.master.destroy()  
        
if __name__ == "__main__":
    root = tk.Tk()
    app = ControlPanel(root)
    root.mainloop()
    