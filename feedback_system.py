# File: feedback_system.py
import numpy as np
import time

class PoseFeedback:   # <--- THIS LINE IS CRITICAL
    def __init__(self, instructor):
        self.instructor = instructor
        self.last_correction_time = 0
        self.correction_cooldown = 4.0
        
        # Keypoint Indices (MoveNet Lightning)
        self.KP = {
            'nose': 0, 'l_eye': 1, 'r_eye': 2, 'l_ear': 3, 'r_ear': 4,
            'l_shldr': 5, 'r_shldr': 6, 'l_elbow': 7, 'r_elbow': 8,
            'l_wrist': 9, 'r_wrist': 10, 'l_hip': 11, 'r_hip': 12,
            'l_knee': 13, 'r_knee': 14, 'l_ankle': 15, 'r_ankle': 16
        }

    def process_feedback(self, live_kpts, ref_kpts):
        if time.time() - self.last_correction_time < self.correction_cooldown:
            return

        live = live_kpts.reshape(-1, 2)
        ref = ref_kpts.reshape(-1, 2)

        # Left Arm Analysis
        live_l_arm_y = live[self.KP['l_wrist']][0] - live[self.KP['l_shldr']][0]
        ref_l_arm_y = ref[self.KP['l_wrist']][0] - ref[self.KP['l_shldr']][0]
        diff_left = live_l_arm_y - ref_l_arm_y
        
        if diff_left > 0.15: 
            self.instructor.speak_misc("lift_left_arm")
            self.last_correction_time = time.time()
            return
        elif diff_left < -0.15:
            self.instructor.speak_misc("lower_left_arm")
            self.last_correction_time = time.time()
            return

        # Right Arm Analysis
        live_r_arm_y = live[self.KP['r_wrist']][0] - live[self.KP['r_shldr']][0]
        ref_r_arm_y = ref[self.KP['r_wrist']][0] - ref[self.KP['r_shldr']][0]
        diff_right = live_r_arm_y - ref_r_arm_y

        if diff_right > 0.15:
            self.instructor.speak_misc("lift_right_arm")
            self.last_correction_time = time.time()
            return
        elif diff_right < -0.15:
            self.instructor.speak_misc("lower_right_arm")
            self.last_correction_time = time.time()
            return
            
        self.instructor.speak_misc("hold_steady")
        self.last_correction_time = time.time()