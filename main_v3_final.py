# File: main_v3_final.py
import cv2
import time
import os
import numpy as np

# --- IMPORTS ---
# We import the logic from your existing main.py
from main import GuidedPoseProgram, get_keypoints, flatten_keypoints
from visualization import draw_prediction_on_image
from feedback_system import PoseFeedback
from gui_manager_v2 import PoseGUI_V2

# --- UTILITY: Letterbox (Colored Background) ---
def letterbox_frame(frame, target_width, target_height):
    h, w = frame.shape[:2]
    scale = min(target_width / w, target_height / h)
    
    new_w = int(w * scale)
    new_h = int(h * scale)
    
    resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
    
    # Canvas (Dark Navy Blue)
    canvas = np.full((target_height, target_width, 3), (80, 20, 10), dtype=np.uint8)
    
    x_off = (target_width - new_w) // 2
    y_off = (target_height - new_h) // 2
    
    canvas[y_off:y_off+new_h, x_off:x_off+new_w] = resized
    
    # White Border
    cv2.rectangle(canvas, 
                 (x_off - 4, y_off - 4), 
                 (x_off + new_w + 4, y_off + new_h + 4), 
                 (255, 255, 255), 2)
                 
    return canvas

class GuidedPoseProgram_UI(GuidedPoseProgram):
    def __init__(self):
        # 1. Setup Fullscreen Window FIRST
        self.window_name = 'Fitness Mirror V3 Final'
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        # Internal Log Storage
        self.boot_logs = []
        self.log_update("Initializing System Core...")
        
        # 2. Initialize GUI Assets
        self.log_update("Loading Graphical User Interface (GUI)...")
        self.gui = PoseGUI_V2("imagedatabase") 
        self.log_update("GUI Assets Loaded.")

        # 3. Camera Check
        self.log_update("Scanning for Video Input Devices...")
        time.sleep(0.5) 
        
        self.log_update("Attempting Connection: USB Camera (Index 1)...")
        self.cap = cv2.VideoCapture(1)
        
        if not self.cap.isOpened():
            self.log_update("[WARNING] USB Camera Not Found.")
            self.log_update("Switching to Default Integrated Camera (Index 0)...")
            self.cap = cv2.VideoCapture(0)
            if self.cap.isOpened():
                self.log_update("[SUCCESS] Default Camera Connected.")
            else:
                self.log_update("[CRITICAL ERROR] No Camera Detected!")
                time.sleep(3)
        else:
            self.log_update("[SUCCESS] USB Camera Connected.")

        # 4. Load AI Models
        self.log_update("Loading TensorFlow Lite Models...")
        self.log_update("Initializing MoveNet Lightning...")
        
        super().__init__() 
        
        self.log_update("AI Inference Engine: ONLINE.")
        self.log_update("Feedback Systems: ONLINE.")
        self.log_update("System Ready.")
        time.sleep(1.0) 
        
        # 5. Final Setup
        self.feedback_sys = PoseFeedback(self.instructor)
        
        # Config (Easier Leg Raises)
        self.similarity_thresholds["warrior_left"] = 0.85
        self.similarity_thresholds["warrior_right"] = 0.85
        self.similarity_thresholds["tree_pose"] = 0.85
        self.similarity_thresholds["leg_raise_left"] = 0.80 
        self.similarity_thresholds["leg_raise_right"] = 0.80 
        
        self.pose_attempt_start_time = None
        self.max_attempt_duration = 100.0 

    def log_update(self, message):
        """Adds a message to the boot screen and updates display immediately."""
        self.boot_logs.append(message)
        if len(self.boot_logs) > 14:
            self.boot_logs.pop(0)
            
        screen = np.full((1080, 1920, 3), (80, 20, 10), dtype=np.uint8)
        
        # Title
        cv2.putText(screen, "SYSTEM BOOT SEQUENCE", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 200, 0), 3)
        cv2.line(screen, (100, 120), (600, 120), (255, 255, 255), 2)
        
        # Draw Logs
        start_y = 200
        for i, log in enumerate(self.boot_logs):
            color = (255, 255, 255)
            if "[WARNING]" in log: color = (0, 165, 255) # Orange
            if "[SUCCESS]" in log: color = (0, 255, 0)   # Green
            if "[CRITICAL]" in log: color = (0, 0, 255)  # Red
            
            cv2.putText(screen, f"> {log}", (100, start_y + (i * 50)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            
        cv2.imshow(self.window_name, screen)
        cv2.waitKey(100) 

    def show_title_screen(self):
        """Displays the Title Screen and waits for Spacebar (Start) or Q (Quit)."""
        canvas_w, canvas_h = 1920, 1080
        cx, cy = canvas_w // 2, canvas_h // 2
        
        while True:
            screen = np.full((canvas_h, canvas_w, 3), (80, 20, 10), dtype=np.uint8)
            
            # Title
            self.gui.draw_centered_text(screen, "MICROCOMPUTER-BASED", cx, cy - 80, 1.5, (255, 255, 255), 4)
            self.gui.draw_centered_text(screen, "PHYSICAL EDUCATION GUIDE SYSTEM", cx, cy + 20, 1.5, (255, 255, 255), 4)
            
            # Blinking Prompt
            if int(time.time() * 1.5) % 2 == 0: 
                self.gui.draw_centered_text(screen, "[ PRESS SPACEBAR TO START ]", cx, cy + 180, 0.9, (255, 200, 0), 2)
            
            # Quit Prompt
            self.gui.draw_centered_text(screen, "Press Q to Exit Program", cx, cy + 300, 0.7, (150, 150, 150), 1)
            
            cv2.imshow(self.window_name, screen)
            
            key = cv2.waitKey(1)
            if key == 32: # Spacebar
                return True
            if key == ord('q') or key == ord('Q'):
                return False

    def show_summary_screen(self, total_poses, duration_str):
        """Shows the end-of-session statistics for 8 seconds then returns."""
        screen = np.full((1080, 1920, 3), (80, 20, 10), dtype=np.uint8)
        cx = 1920 // 2
        cy = 1080 // 2
        
        self.gui.draw_centered_text(screen, "SESSION COMPLETED", cx, cy - 150, 2.0, (255, 255, 255), 4)
        self.gui.draw_centered_text(screen, "Great Work!", cx, cy - 80, 1.2, (255, 200, 0), 2)
        
        # Stats Box
        cv2.rectangle(screen, (cx - 300, cy), (cx + 300, cy + 200), (50, 20, 0), -1)
        cv2.rectangle(screen, (cx - 300, cy), (cx + 300, cy + 200), (255, 200, 0), 2)
        
        self.gui.draw_centered_text(screen, f"Poses Completed: {total_poses}", cx, cy + 80, 1.0, (255, 255, 255), 2)
        self.gui.draw_centered_text(screen, f"Total Duration: {duration_str}", cx, cy + 150, 1.0, (255, 255, 255), 2)
        
        self.gui.draw_centered_text(screen, "Returning to Title Screen...", cx, cy + 300, 0.8, (150, 150, 150), 1)

        cv2.imshow(self.window_name, screen)
        cv2.waitKey(8000) # Wait 8 seconds then auto-return

    def run_program(self):
        if not self.program_started: return
        
        # --- MAIN APPLICATION LOOP ---
        while True:
            # 1. Title Screen Loop
            user_wants_to_start = self.show_title_screen()
            if not user_wants_to_start:
                break # User pressed Q on title screen -> Exit App

            # 2. Reset Session Variables (Critical for restarting)
            self.current_pose_index = 0
            self.pose_attempt_start_time = None
            self.pose_start_time = None
            self.rest_start_time = 0
            self.instructor.speak_misc("welcome")
            
            session_start_time = time.time()
            canvas_w, canvas_h = 1920, 1080
            
            # 3. Session Loop
            while True:
                ret, raw_frame = self.cap.read()
                if not ret: break

                # AI Processing
                frame_rgb = cv2.cvtColor(raw_frame, cv2.COLOR_BGR2RGB)
                live_keypoints_raw = get_keypoints(frame_rgb)
                processed_frame = draw_prediction_on_image(raw_frame, live_keypoints_raw)
                final_display = letterbox_frame(processed_frame, canvas_w, canvas_h)

                # Check Completion
                if self.current_pose_index >= len(self.poses_sequence):
                    self.instructor.speak_misc("session_complete")
                    break # End session -> Go to summary
                
                target_pose = self.poses_sequence[self.current_pose_index]
                if self.pose_attempt_start_time is None:
                    self.pose_attempt_start_time = time.time()
                
                self.gui.set_target_pose(target_pose)

                # --- REST MODE ---
                if self.rest_start_time > 0:
                    final_display = cv2.addWeighted(final_display, 0.3, np.zeros(final_display.shape, final_display.dtype), 0.7, 0)
                    rest_elapsed = time.time() - self.rest_start_time
                    remaining_rest = max(0, int(self.rest_duration - rest_elapsed))
                    
                    cx, cy = canvas_w // 2, canvas_h // 2
                    self.gui.draw_centered_text(final_display, "REST TIME", cx, cy - 80, 2.5, (255, 255, 255), 4)
                    self.gui.draw_centered_text(final_display, str(remaining_rest), cx, cy + 50, 4.0, (0, 255, 0), 5)
                    next_text = f"UP NEXT: {target_pose.replace('_', ' ').upper()}"
                    self.gui.draw_centered_text(final_display, next_text, cx, cy + 150, 1.0, (200, 200, 255), 2)
                    cv2.imshow(self.window_name, final_display)
                    
                    if rest_elapsed >= self.rest_duration:
                        self.rest_start_time = 0
                        self.pose_attempt_start_time = time.time()
                        if self.current_pose_index < len(self.poses_sequence):
                             self.instructor.guide_pose(self.poses_sequence[self.current_pose_index], "start")
                        self.last_feedback_time = time.time()
                    
                    if cv2.waitKey(1) == ord('q'): 
                        # 'Q' mid-rest skips to Summary/Title
                        self.current_pose_index = len(self.poses_sequence) # Force end
                        break
                    continue

                # --- ACTIVE MODE ---
                attempt_elapsed = time.time() - self.pose_attempt_start_time
                time_left = max(0, self.max_attempt_duration - attempt_elapsed)
                pose_height, visible = self.get_pose_size(live_keypoints_raw)
                is_holding = False
                hold_progress = 0.0

                if time_left <= 0:
                    self.instructor.speak_misc("rest_start")
                    self.current_pose_index += 1
                    self.pose_attempt_start_time = None
                    self.pose_start_time = None
                    if self.current_pose_index < len(self.poses_sequence):
                          self.rest_start_time = time.time()
                    continue

                if visible and pose_height > 0.0:
                    current_pose, score = self.get_best_match(live_keypoints_raw)
                    threshold = self.similarity_thresholds.get(target_pose, self.similarity_thresholds["default"])

                    if current_pose == target_pose and score > threshold:
                        is_holding = True
                        if self.pose_start_time is None:
                            self.pose_start_time = time.time()
                        else:
                            elapsed_hold = time.time() - self.pose_start_time
                            hold_progress = min(elapsed_hold / self.required_hold_time, 1.0)
                            
                            if elapsed_hold >= self.required_hold_time:
                                self.instructor.guide_pose(target_pose, "good")
                                self.current_pose_index += 1
                                self.pose_start_time = None
                                self.pose_attempt_start_time = None
                                
                                if self.current_pose_index < len(self.poses_sequence):
                                    self.instructor.guide_pose(self.poses_sequence[self.current_pose_index], "rest")
                                    self.rest_start_time = time.time()
                    else:
                        self.pose_start_time = None
                        is_holding = False
                        # Feedback Logic
                        ref_vector = None
                        for key, vec in self.reference_poses.items():
                            if key.startswith(target_pose + "|"):
                                ref_vector = vec
                                break
                        if ref_vector is not None:
                            flat_live = flatten_keypoints(live_keypoints_raw)
                            self.feedback_sys.process_feedback(flat_live, ref_vector)

                # Draw GUI
                final_display = self.gui.draw_interface(
                    final_display, self.current_pose_index, len(self.poses_sequence),
                    hold_progress=hold_progress, is_holding=is_holding, time_left=time_left
                )

                cv2.imshow(self.window_name, final_display)
                
                # Check for Q (Quit Session)
                if cv2.waitKey(1) == ord('q'): 
                    self.current_pose_index = len(self.poses_sequence) # Force end
                    break
            
            # 4. Show Summary (Then Loop back to Title)
            total_time = time.time() - session_start_time
            mins = int(total_time // 60)
            secs = int(total_time % 60)
            self.show_summary_screen(self.current_pose_index, f"{mins}m {secs}s")

        # Cleanup when outer loop breaks
        self.cleanup()

if __name__ == "__main__":
    program = GuidedPoseProgram_UI()
    if program.initialize():
        program.run_program()