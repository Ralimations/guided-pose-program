# Packaging Guide — Create a standalone Windows app (no venv required at runtime)

This folder contains helper scripts and instructions to package the project into a Windows application without modifying the original source files. All changes and additions are made inside a separate build folder so your original program stays untouched.

Overview
- `build_app.ps1`: PowerShell script that copies necessary files into a timestamped `build/` directory, creates a small launcher (`run_app.py`) there, and invokes PyInstaller to produce a `dist/` folder with the app.
- `run_app.py`: Lightweight entrypoint used by PyInstaller to ensure resources are found correctly (handles bundled app and normal folder layout).

Before you begin
- Install Python 3.11+ and Windows build dependencies.
- Install PyInstaller in your environment (the script will prompt to install if missing).

How to use
1. Open PowerShell in this repo and run (you may need admin privileges for installing packages):
   .\packaging\build_app.ps1 -AppName "peguidenew" -OneDir

2. The script will create `build/<timestamp>/` copy of your project and then run PyInstaller.
3. After success, you'll find the application in `dist/<AppName>/` (when using --onedir) or `dist/<AppName>.exe` (when using --onefile).

Notes & Tips
- The script copies `model.tflite`, `imagedatabase/`, `audio_assets/`, `model_estimates/`, and `evaluation_results/` by default. Edit the script to include additional resources if needed.
- Choosing `-OneDir` is recommended for easier debugging and to avoid runtime extraction delays.
- The build process may need a short-lived venv or the system Python; this only affects the build machine, not the packaged runtime.

Safety
- This process never modifies files in the original repo. All modifications and launcher files are created inside the `build/` folder.

If you want, I can now run the build script locally (will prompt to install PyInstaller and create the copy) or tweak which folders to include. Let me know which option you prefer.