"""
Entrypoint script used inside the copied build folder or by PyInstaller.
It sets working directory and logs unhandled exceptions so crashes don't silently close the console.
This launcher never modifies your original program — it runs the copy.
"""
import os
import sys
import traceback
import logging
import time

# Windows MessageBox helper
def _show_error_message(msg, title="Application Error"):
    try:
        if os.name == 'nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, msg, title, 0x00000010)  # MB_ICONERROR
        else:
            print(msg)
    except Exception:
        print(msg)

# Determine base directory (bundled _MEIPASS or script dir)
if getattr(sys, "frozen", False):
    base_dir = sys._MEIPASS  # type: ignore[attr-defined]
else:
    base_dir = os.path.abspath(os.path.dirname(__file__))

# Change working directory to base dir so relative assets resolve
try:
    os.chdir(base_dir)
except Exception:
    pass

# Setup logging to a file inside base_dir
log_path = os.path.join(base_dir, 'run_app.log')
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s:%(message)s',
                    handlers=[logging.FileHandler(log_path, encoding='utf-8'),
                              logging.StreamHandler()])
logger = logging.getLogger(__name__)
logger.info('Launcher started. Base dir: %s', base_dir)

try:
    import importlib
    try:
        main_mod = importlib.import_module('main_v3_finalfix')
    except Exception as e:
        logger.exception('Failed to import main_v3_finalfix')
        _show_error_message(f'Failed to start application. Details written to:\n{log_path}\n\nError: {e}')
        raise

    try:
        if hasattr(main_mod, 'GuidedPoseProgram_UI'):
            program = main_mod.GuidedPoseProgram_UI()
            initialized = False
            try:
                initialized = program.initialize()
            except Exception:
                logger.exception('Exception during program.initialize()')
                _show_error_message(f'Initialization error. See log: {log_path}')
                raise

            if not initialized:
                logger.error('program.initialize() returned False — aborting')
                _show_error_message(f'Initialization failed. See log: {log_path}')
            else:
                try:
                    program.run_program()
                except Exception:
                    logger.exception('Exception while running program')
                    _show_error_message(f'Runtime error. See log: {log_path}')
                    raise

        else:
            if hasattr(main_mod, 'main'):
                try:
                    main_mod.main()
                except Exception:
                    logger.exception('Exception in main()')
                    _show_error_message(f'Runtime error in main(). See log: {log_path}')
                    raise
            else:
                raise RuntimeError('Could not locate entrypoint in main_v3_finalfix.py')

except Exception:
    tb = traceback.format_exc()
    try:
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write('\n' + tb)
    except Exception:
        pass

    # Ensure user sees the error before the console closes
    _show_error_message(f'Application has crashed. Details written to:\n{log_path}')
    # Wait briefly so the messagebox remains visible when double-clicked
    try:
        time.sleep(6)
    except Exception:
        pass
    # Re-raise so that debugging tools (if attached) get the exception
    raise
