# File: gui_manager_v2.py
import cv2
import numpy as np
import os

class PoseGUI_V2:
    def __init__(self, image_database_dir):
        self.db_dir = image_database_dir
        self.current_ref_image = None
        self.current_pose_name = ""
        self.image_cache = {}
        
        # --- COLOR PALETTE (Blue & White Theme) ---
        # OpenCV uses BGR format (Blue, Green, Red)
        
        # Background Panel: Deep Navy Blue
        self.COLOR_BG_PANEL = (100, 30, 0)      
        
        # Accents: Bright Electric Blue
        self.COLOR_ACCENT = (255, 200, 0)       
        
        # Text: Pure White
        self.COLOR_TEXT_MAIN = (255, 255, 255)  
        self.COLOR_TEXT_DIM = (220, 220, 220)   
        
        # Success: Bright Green
        self.COLOR_SUCCESS = (0, 255, 0)    
        # Warning: Bright Red
        self.COLOR_WARNING = (0, 0, 255)    
        
        self.FONT = cv2.FONT_HERSHEY_SIMPLEX

    def set_target_pose(self, pose_name):
        if pose_name == self.current_pose_name: return
        self.current_pose_name = pose_name
        
        if pose_name in self.image_cache:
            self.current_ref_image = self.image_cache[pose_name]
            return

        self.current_ref_image = None 
        pose_dir = os.path.join(self.db_dir, pose_name)
        
        if os.path.isdir(pose_dir):
            images = [f for f in os.listdir(pose_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
            if images:
                img_path = os.path.join(pose_dir, images[0])
                img = cv2.imread(img_path)
                if img is not None:
                    self.current_ref_image = img
                    self.image_cache[pose_name] = img

    def draw_overlay_rect(self, img, x, y, w, h, color, alpha=0.7):
        img_h, img_w = img.shape[:2]
        x = max(0, min(x, img_w))
        y = max(0, min(y, img_h))
        w = min(w, img_w - x)
        h = min(h, img_h - y)
        if w <= 0 or h <= 0: return

        sub_img = img[y:y+h, x:x+w]
        rect = np.full(sub_img.shape, color, dtype=np.uint8)
        res = cv2.addWeighted(sub_img, 1 - alpha, rect, alpha, 0)
        img[y:y+h, x:x+w] = res

    def draw_centered_text(self, img, text, center_x, center_y, font_scale, color, thickness):
        """Helper to perfectly center text."""
        size = cv2.getTextSize(text, self.FONT, font_scale, thickness)[0]
        text_x = int(center_x - (size[0] / 2))
        text_y = int(center_y + (size[1] / 2))
        cv2.putText(img, text, (text_x, text_y), self.FONT, font_scale, color, thickness)

    def draw_interface(self, frame, current_index, total_poses, hold_progress=0.0, is_holding=False, time_left=None):
        h, w = frame.shape[:2]
        
        # --- 1. SESSION PROGRESS (TOP) ---
        bar_height = 15
        progress_pct = (current_index) / max(1, total_poses)
        # Draw Dark Blue Background Strip
        self.draw_overlay_rect(frame, 0, 0, w, bar_height, (50, 20, 0), 0.9) 
        
        # Draw Bright Blue Fill
        fill_width = int(w * progress_pct)
        if fill_width > 0:
            cv2.rectangle(frame, (0, 0), (fill_width, bar_height), self.COLOR_ACCENT, -1)

        # --- 2. LEFT INFO PANEL (UPDATED SIZE & FONTS) ---
        panel_w = 450   # INCREASED from 320
        panel_h = 200   # INCREASED from 160
        panel_x = 30
        panel_y = 50
        
        # Draw Blue Background Panel
        self.draw_overlay_rect(frame, panel_x, panel_y, panel_w, panel_h, self.COLOR_BG_PANEL, 0.85)
        # Draw Accent Border (Thicker)
        cv2.rectangle(frame, (panel_x, panel_y), (panel_x+panel_w, panel_y+panel_h), self.COLOR_ACCENT, 3) 
        
        # Pose Name (BIGGER & BOLDER)
        display_name = self.current_pose_name.replace("_", " ").upper()
        cv2.putText(frame, display_name, (panel_x + 20, panel_y + 60), 
                    self.FONT, 1.3, self.COLOR_TEXT_MAIN, 3) # Font 1.3, Thick 3
        
        # Step Count (BIGGER)
        cv2.putText(frame, f"STEP {current_index + 1} / {total_poses}", (panel_x + 20, panel_y + 110), 
                    self.FONT, 0.9, self.COLOR_TEXT_DIM, 2) # Font 0.9, Thick 2

        # Timeout Timer (BIGGER)
        if time_left is not None and time_left < 999:
            cv2.putText(frame, f"SKIP IN: {int(time_left)}s", (panel_x + 20, panel_y + 160), 
                        self.FONT, 1.0, self.COLOR_WARNING, 3) # Font 1.0, Thick 3

        # --- 3. REFERENCE IMAGE (BOTTOM RIGHT) ---
        if self.current_ref_image is not None:
            target_h = int(h * 0.35)
            rh, rw = self.current_ref_image.shape[:2]
            aspect = rw / rh
            new_w = int(target_h * aspect)
            
            if new_w > 0 and target_h > 0:
                ref_resized = cv2.resize(self.current_ref_image, (new_w, target_h))
                x_pos = w - new_w - 40
                y_pos = h - target_h - 40
                
                # Blue Border Background
                border = 4
                cv2.rectangle(frame, (x_pos-border, y_pos-border), (x_pos+new_w+border, y_pos+target_h+border), self.COLOR_ACCENT, -1)
                frame[y_pos:y_pos+target_h, x_pos:x_pos+new_w] = ref_resized
                
                # Label
                cv2.putText(frame, "TARGET", (x_pos, y_pos - 10), self.FONT, 0.8, self.COLOR_ACCENT, 2)

        # --- 4. HOLD PROGRESS (CENTER) ---
        if is_holding:
            center_x = w // 2
            center_y = h - 150
            
            self.draw_centered_text(frame, "HOLD POSITION!", center_x, center_y, 1.5, self.COLOR_SUCCESS, 4)
            
            bar_w = 500 # Made wider
            bar_h = 30
            bar_x = center_x - (bar_w // 2)
            bar_y = center_y + 30
            
            # Draw Bar Background
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (50,50,50), -1)
            cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), self.COLOR_SUCCESS, 2)
            
            # Draw Fill
            fill_w = int(bar_w * hold_progress)
            if fill_w > 0:
                cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), self.COLOR_SUCCESS, -1)
        
        return frame