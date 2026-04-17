# File: main.py
# Description: Main Program using Pre-Recorded Audio Assets
# (Make sure you have run generate_audio.py first!)

# --- 1. IMPORTS ---
import cv2
import time
import os
import numpy as np
import tensorflow as tf
from sklearn.metrics.pairwise import cosine_similarity

from instructions import PoseInstructions
from visualization import draw_prediction_on_image
from model import movenet, input_size

# --- CAMERA CONFIGURATION ---
# Change this to switch cameras (0=default, 1=USB camera, etc.)
CAMERA_INDEX = 0

# --- 2. HELPER FUNCTIONS ---

def load_reference_poses(image_database_dir):
    reference_poses = {}
    if not os.path.isdir(image_database_dir):
        print(f"Error: Image database directory not found at: {image_database_dir}")
        return None

    print(f"Loading all reference images from: {image_database_dir}")
    for pose_name in os.listdir(image_database_dir):
        pose_dir = os.path.join(image_database_dir, pose_name)
        if os.path.isdir(pose_dir):
            image_files = [f for f in os.listdir(pose_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
            if not image_files: continue

            print(f"  Loaded class: {pose_name} ({len(image_files)} images)")
            for i, image_file in enumerate(image_files):
                image_path = os.path.join(pose_dir, image_file)
                reference_key = f"{pose_name}|{i}" 
                try:
                    image = tf.io.read_file(image_path)
                    image = tf.image.decode_jpeg(image)
                    keypoints = get_keypoints(image)
                    flat_keypoints = flatten_keypoints(keypoints)
                    reference_poses[reference_key] = flat_keypoints.reshape(1, -1)
                except Exception as e:
                    print(f"Error loading {image_path}: {e}")
            
    return reference_poses

def get_keypoints(image):
    if not isinstance(image, tf.Tensor):
        image = tf.convert_to_tensor(image, dtype=tf.uint8)
    if image.shape[-1] != 3:
        image = tf.image.grayscale_to_rgb(image)
    input_image = tf.expand_dims(image, axis=0)
    input_image = tf.image.resize_with_pad(input_image, input_size, input_size)
    keypoints_with_scores = movenet(input_image)
    return keypoints_with_scores

def flatten_keypoints(keypoints_with_scores):
    keypoints = np.squeeze(keypoints_with_scores)[:, :2]
    return keypoints.flatten()

# --- 3. MAIN PROGRAM CLASS ---

class GuidedPoseProgram:
    def __init__(self):
        print("Initializing program variables...")
        self.instructor = PoseInstructions()
        self.reference_poses = None
        self.cap = None
        
        self.similarity_thresholds = {
            "default": 0.85, 
            "start": 0.90,
        }

        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.image_database_dir = os.path.join(base_dir, 'imagedatabase')

        # Load Sequence
        self.poses_sequence = []
        sequence_file_path = os.path.join(base_dir, 'sequence.txt')
        try:
            with open(sequence_file_path, 'r') as f:
                for line in f:
                    pose_name = line.strip()
                    if pose_name and not pose_name.startswith('#'):
                        self.poses_sequence.append(pose_name)
        except FileNotFoundError:
            print("Sequence file not found.")

        self.current_pose_index = 0
        self.pose_start_time = None
        self.required_hold_time = 3.0
        self.last_feedback_time = 0
        self.feedback_cooldown = 4.0 
        self.rest_start_time = 0
        self.rest_duration = 8.0 
        
        self.optimal_pose_height_range = (0.4, 0.9)  
        self.last_distance_feedback_time = 0
        self.distance_feedback_cooldown = 4.0 
        
        self.no_user_start_time = None
        self.no_user_skip_time = 5.0 
        self.no_user_countdown_spoken = {5: False, 4: False, 3: False, 2: False, 1: False}

        self.program_started = False

    def initialize(self):
        self.reference_poses = load_reference_poses(self.image_database_dir)
        if not self.reference_poses: return False

        # Webcam initialization - try multiple backends for compatibility
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened() and os.name == 'nt':
            # Fallback to DSHOW on Windows if default fails
            self.cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
            
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        if not self.cap.isOpened(): return False
        print(f"Camera initialized with index: {CAMERA_INDEX}")
        self.program_started = True
        return True

    def get_best_match(self, live_keypoints):
        live_vector = flatten_keypoints(live_keypoints).reshape(1, -1)
        best_match_pose = "None"
        best_match_score = 0.0

        for reference_key, ref_vector in self.reference_poses.items():
            score = cosine_similarity(ref_vector, live_vector)[0][0]
            if score > best_match_score:
                best_match_score = score
                best_match_pose = reference_key.split('|')[0]
        return best_match_pose, best_match_score

    def give_corrective_feedback(self, target_pose, current_pose, score):
        current_time = time.time()
        if current_time - self.last_feedback_time > self.feedback_cooldown:
            threshold = self.similarity_thresholds.get(target_pose, self.similarity_thresholds["default"])
            
            if current_pose == target_pose and score > (threshold - 0.1):
                self.instructor.guide_pose(target_pose, "almost")
            else:
                self.instructor.guide_pose(target_pose, "not_quite")
            self.last_feedback_time = current_time

    def get_pose_size(self, keypoints_with_scores, min_confidence=0.2):
        keypoints = np.squeeze(keypoints_with_scores)
        y_coords = keypoints[:, 0]
        scores = keypoints[:, 2]
        
        visible_y_coords = y_coords[scores > min_confidence]
        if visible_y_coords.size < 2: return 0.0, False 

        min_y = np.min(visible_y_coords)
        max_y = np.max(visible_y_coords)
        pose_height = max_y - min_y
        all_keypoints_visible = np.sum(scores > min_confidence) > 5
        return pose_height, all_keypoints_visible

    def give_distance_feedback(self, pose_height, all_keypoints_visible):
        current_time = time.time()
        if current_time - self.last_distance_feedback_time < self.distance_feedback_cooldown:
            return  

        min_height, max_height = self.optimal_pose_height_range
        if pose_height == 0.0: return 

        if pose_height < min_height:
            self.instructor.speak_misc("too_far")
            self.last_distance_feedback_time = current_time
        elif pose_height > max_height:
            self.instructor.speak_misc("too_close")
            self.last_distance_feedback_time = current_time

    def run_program(self):
        if not self.program_started: return
        print("Starting program. Press 'q' to quit.")
        
        # CHANGED: Uses speak_misc instead of speak
        self.instructor.speak_misc("welcome")

        while True:
            # --- CHECK IF PROGRAM FINISHED ---
            if self.current_pose_index >= len(self.poses_sequence):
                break
            
            target_pose = self.poses_sequence[self.current_pose_index]

            # --- REST LOGIC ---
            if self.rest_start_time > 0:
                rest_elapsed = time.time() - self.rest_start_time
                remaining_rest = int(self.rest_duration - rest_elapsed)
                
                if rest_elapsed < self.rest_duration:
                    ret, frame = self.cap.read()
                    if not ret: break
                    
                    cv2.putText(frame, f"REST: {remaining_rest}", (220, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 4)
                    cv2.imshow('Guided Pose Program', frame)
                    if cv2.waitKey(1) == ord('q'): break
                    continue
                else:
                    self.rest_start_time = 0
                    if self.current_pose_index < len(self.poses_sequence):
                        # Trigger the specific pose audio "Now do Warrior..."
                        self.instructor.guide_pose(self.poses_sequence[self.current_pose_index], "start")
                    
                    self.last_feedback_time = time.time()
                    self.last_distance_feedback_time = time.time()

            # --- MAIN LOOP ---
            ret, frame = self.cap.read()
            if not ret: break

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            live_keypoints = get_keypoints(frame_rgb)
            output_overlay = draw_prediction_on_image(frame, live_keypoints)

            pose_height, visible = self.get_pose_size(live_keypoints)
            self.give_distance_feedback(pose_height, visible)

            # --- No User Logic ---
            if pose_height == 0.0:
                if self.no_user_start_time is None:
                    self.no_user_start_time = time.time()
                    self.instructor.speak_misc("no_user")
                    self.no_user_countdown_spoken = {5: True, 4: False, 3: False, 2: False, 1: False}
                else:
                    elapsed_no_user = time.time() - self.no_user_start_time
                    rem = self.no_user_skip_time - elapsed_no_user
                    
                    for i in range(4, 0, -1):
                        if rem <= i and not self.no_user_countdown_spoken[i]:
                            self.instructor.speak_misc(f"countdown_{i}")
                            self.no_user_countdown_spoken[i] = True
                            break
                    
                    if rem <= 0:
                        # Fallback console print since we don't have specific "Skipping [PoseName]" audio
                        print(f"Skipping {target_pose}")
                        self.current_pose_index += 1
                        self.pose_start_time = None
                        self.no_user_start_time = None
                        if self.current_pose_index < len(self.poses_sequence):
                            self.instructor.guide_pose(self.poses_sequence[self.current_pose_index], "start")
                        continue
            else:
                if self.no_user_start_time is not None:
                    self.instructor.speak_misc("welcome") # "Welcome back"
                    self.no_user_start_time = None

            # --- Pose Matching ---
            if pose_height > 0.0:
                current_pose, score = self.get_best_match(live_keypoints)
                threshold = self.similarity_thresholds.get(target_pose, self.similarity_thresholds["default"])

                if current_pose == target_pose and score > threshold:
                    if self.pose_start_time is None:
                        self.pose_start_time = time.time()
                    else:
                        elapsed = time.time() - self.pose_start_time
                        if elapsed >= self.required_hold_time:
                            self.instructor.guide_pose(target_pose, "good")
                            
                            self.current_pose_index += 1
                            self.pose_start_time = None
                            
                            if self.current_pose_index == len(self.poses_sequence):
                                self.instructor.speak_misc("session_complete")
                                time.sleep(4)
                                break 
                            elif self.current_pose_index < len(self.poses_sequence):
                                self.instructor.guide_pose(self.poses_sequence[self.current_pose_index], "rest")
                                self.rest_start_time = time.time()
                else:
                    if self.pose_start_time is not None:
                        self.pose_start_time = None
                    self.give_corrective_feedback(target_pose, current_pose, score)

            cv2.imshow('Guided Pose Program', output_overlay)
            if cv2.waitKey(1) == ord('q'): break

        self.cleanup()

    def cleanup(self):
        self.instructor.cleanup()
        if self.cap: self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    program = GuidedPoseProgram()
    if program.initialize():
        program.run_program()