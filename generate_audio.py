# File: generate_audio.py
import os
from gtts import gTTS

# 1. Define all the phrases you need
# Standard commands
commands = {
    "welcome": "Welcome. Get in the start pose.",
    "rest_start": "Rest is over. Get ready.",
    "attempt_match": "Try to match the pose.",
    "good_job": "Good job! Pose completed.",
    "rest": "Take a break.",
    "too_far": "You are too far. Move closer.",
    "too_close": "You are too close. Move back.",
    "no_user": "No user detected. Skipping in 5 seconds.",
    "session_complete": "Session complete. Thank you.",
    "countdown_1": "One",
    "countdown_2": "Two",
    "countdown_3": "Three",
    "countdown_4": "Four",
    "countdown_5": "Five",
}

# 2. Load poses from your sequence file to ensure we have names for them
poses = []
try:
    with open('sequence.txt', 'r') as f:
        for line in f:
            name = line.strip()
            if name and not name.startswith("#"):
                poses.append(name)
except FileNotFoundError:
    print("sequence.txt not found. Using default list.")
    poses = ["warrior_left", "warrior_right", "tree_pose", "start"]

# 3. Create the directory
output_dir = "audio_assets"
os.makedirs(output_dir, exist_ok=True)

print(f"Generating audio files in '{output_dir}'...")

# 4. Generate Command Audio
for key, text in commands.items():
    filename = os.path.join(output_dir, f"{key}.mp3")
    if not os.path.exists(filename):
        print(f"Generating: {filename} -> '{text}'")
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filename)

# 5. Generate Pose-Specific Audio (e.g., "Now do the warrior pose")
seen_poses = set()
for pose in poses:
    if pose in seen_poses: continue
    seen_poses.add(pose)
    
    # Clean name: "warrior_left" -> "warrior left"
    clean_name = pose.replace("_", " ")
    
    text = f"Now, do the {clean_name} pose."
    filename = os.path.join(output_dir, f"pose_{pose}.mp3")
    
    if not os.path.exists(filename):
        print(f"Generating: {filename} -> '{text}'")
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filename)

print("Done! All audio files generated.")