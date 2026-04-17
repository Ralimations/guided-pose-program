# File: instructions.py
import pygame
import os
import threading
import time

class PoseInstructions:
    def __init__(self):
        # Initialize Pygame Mixer (low latency audio)
        try:
            pygame.mixer.init()
            self.has_audio = True
        except Exception as e:
            print(f"Audio Init Failed: {e}")
            self.has_audio = False

        self.asset_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_assets")
        
        # Track last played to prevent spamming "Not quite"
        self.last_played = None
        self.last_played_time = 0

    def play_audio(self, filename, force=False):
        """
        Plays an MP3 file from the assets folder.
        force: If True, stops current sound to play this one immediately.
        """
        if not self.has_audio:
            print(f"[SILENT]: {filename}")
            return

        path = os.path.join(self.asset_dir, filename + ".mp3")
        
        if not os.path.exists(path):
            print(f"Audio file missing: {path}")
            return

        # Anti-spam: Don't repeat "attempt_match" too fast
        current_time = time.time()
        if filename == "attempt_match" and (current_time - self.last_played_time < 3.0):
            return

        if force:
            pygame.mixer.music.stop()

        try:
            # Check if busy (unless forcing)
            if not force and pygame.mixer.music.get_busy():
                return 

            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            self.last_played = filename
            self.last_played_time = current_time
        except Exception as e:
            print(f"Playback Error: {e}")

    def play_beep(self):
        """Plays a generated beep sound using pygame or native."""
        # Ideally, have a 'ding.mp3' in assets. 
        # Fallback to generating a simple tone if possible, or silence.
        # For simplicity, we assume you generated 'good_job.mp3' which acts as the success sound.
        pass

    def guide_pose(self, pose_name, status):
        """
        Translates status into a filename and plays it.
        """
        if status == "start":
            # Play "pose_warrior_left" (Generated as: "Now, do the warrior left pose")
            self.play_audio(f"pose_{pose_name}", force=True)
            
        elif status == "almost":
            self.play_audio("attempt_match", force=False)
            
        elif status == "not_quite":
            self.play_audio("attempt_match", force=False)
            
        elif status == "good":
            self.play_audio("good_job", force=True)
            
        elif status == "rest":
            self.play_audio("rest", force=True)
    
    def speak_misc(self, command_key):
        """Helper for miscellaneous commands like 'too_far'"""
        self.play_audio(command_key, force=True)

    def cleanup(self):
        pygame.mixer.quit()

if __name__ == "__main__":
    inst = PoseInstructions()
    print("Testing Audio...")
    inst.speak_misc("welcome")
    time.sleep(3)
    inst.guide_pose("start", "start") # Should fail if you haven't run generate_audio.py or dont have 'pose_start.mp3'