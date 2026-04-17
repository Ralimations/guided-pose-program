# File: gui_manager.py
import cv2
import os
import numpy as np

class PoseGUI:
    def __init__(self, image_database_dir):
        self.db_dir = image_database_dir
        self.current_ref_image = None
        self.current_pose_name = ""
        
        # Cache for loaded reference images to improve speed
        self.image_cache = {}

    def set_target_pose(self, pose_name):
        """Preloads the reference image for the target pose."""
        if pose_name == self.current_pose_name:
            return

        self.current_pose_name = pose_name
        
        # Check cache first
        if pose_name in self.image_cache:
            self.current_ref_image = self.image_cache[pose_name]
            return

        # Attempt to load image
        pose_dir = os.path.join(self.db_dir, pose_name)
        if os.path.isdir(pose_dir):
            images = [f for f in os.listdir(pose_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
            if images:
                # Load first image found
                img_path = os.path.join(pose_dir, images[0])
                img = cv2.imread(img_path)
                if img is not None:
                    # Resize for thumbnail (e.g., 150 pixels width)
                    scale = 150 / img.shape[1]
                    dim = (150, int(img.shape[0] * scale))
                    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
                    self.current_ref_image = resized
                    self.image_cache[pose_name] = resized
                else:
                    self.current_ref_image = None
            else:
                self.current_ref_image = None
        else:
            self.current_ref_image = None

    def draw_interface(self, frame, current_index, total_poses, status_message=""):
        """
        Draws the GUI overlay on the frame.
        """
        h, w, _ = frame.shape
        
        # 1. Top Right: Progress & Pose Name
        # Create a semi-transparent background for text
        overlay = frame.copy()
        cv2.rectangle(overlay, (w - 250, 0), (w, 80), (0, 0, 0), -1)
        alpha = 0.6
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        # Pose Name
        pose_display = self.current_pose_name.replace("_", " ").title()
        cv2.putText(frame, f"{pose_display}", (w - 240, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Progress (e.g., 1/16)
        # Using index + 1 for user friendly counting
        cv2.putText(frame, f"Pose: {current_index + 1}/{total_poses}", (w - 240, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        # 2. Bottom Right: Reference Image Overlay
        if self.current_ref_image is not None:
            rh, rw, _ = self.current_ref_image.shape
            
            # Position: Bottom Right with 10px padding
            y_offset = h - rh - 10
            x_offset = w - rw - 10
            
            # Ensure it fits
            if y_offset > 0 and x_offset > 0:
                # Draw white border around reference
                cv2.rectangle(frame, (x_offset-2, y_offset-2), 
                              (x_offset+rw+2, y_offset+rh+2), (255, 255, 255), 2)
                
                # Overlay image
                frame[y_offset:y_offset+rh, x_offset:x_offset+rw] = self.current_ref_image

        return frame