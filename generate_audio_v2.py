# File: generate_audio_v2.py
import os
from gtts import gTTS

# New corrective commands
commands = {
    # --- General Interface ---
    "welcome": "Welcome. Get in the start pose.",
    "rest_start": "Rest is over. Get ready.",
    "good_job": "Good job! Pose completed.",
    "rest": "Take a break.",
    "session_complete": "Session complete. Thank you.",
    "no_user": "No user detected. Skipping in 5 seconds.",
    "too_far": "You are too far. Move closer.",
    "too_close": "You are too close. Move back.",

    # --- Specific Corrections (New) ---
    "lift_left_arm": "Lift your left arm higher.",
    "lower_left_arm": "Lower your left arm.",
    "lift_right_arm": "Lift your right arm higher.",
    "lower_right_arm": "Lower your right arm.",
    "straighten_back": "Straighten your back.",
    "lower_hips": "Lower your hips.",
    "check_legs": "Check your leg position.",
    "hold_steady": "Hold steady, you are almost there.",
    
    # --- Countdowns ---
    "countdown_1": "One",
    "countdown_2": "Two",
    "countdown_3": "Three",
    "countdown_4": "Four",
    "countdown_5": "Five",
}

output_dir = "audio_assets"
os.makedirs(output_dir, exist_ok=True)

print(f"Generating extended audio files in '{output_dir}'...")

for key, text in commands.items():
    filename = os.path.join(output_dir, f"{key}.mp3")
    # Only generate if it doesn't exist to save time
    if not os.path.exists(filename):
        print(f"Generating: {filename}")
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filename)

print("Audio update complete.")