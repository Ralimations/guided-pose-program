# File: model.py
# Description: Universal TFLite Loader with Debugging

import tensorflow as tf
import os
import numpy as np

print("DEBUG: Loading updated model.py with auto-convert...")

# 1. Define input size (Standard for MoveNet Lightning)
input_size = 192

# 2. Locate the model file
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "model.tflite")

if not os.path.exists(model_path):
    raise FileNotFoundError(f"CRITICAL ERROR: 'model.tflite' not found in {current_dir}")

# 3. Load the TFLite Model
interpreter = tf.lite.Interpreter(model_path=model_path)
interpreter.allocate_tensors()

# Get input details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
target_dtype = input_details[0]['dtype']

def movenet(input_image):
    """
    Runs pose detection using local TFLite model with auto-type conversion.
    """
    # Ensure input is a Tensor
    if not isinstance(input_image, tf.Tensor):
        input_image = tf.convert_to_tensor(input_image)

    # AUTO-FIX: Scale data if needed
    # If model wants 0-255 (UINT8) but we have 0-1 (Float), scale it up.
    if target_dtype == np.uint8 and tf.reduce_max(input_image) <= 1.5:
        input_image = input_image * 255.0

    # AUTO-FIX: Cast to the correct type (UINT8 or FLOAT32)
    input_tensor = tf.cast(input_image, dtype=target_dtype)
    
    # Set the input tensor (Use .numpy() to be safe for TFLite)
    interpreter.set_tensor(input_details[0]['index'], input_tensor.numpy())
    
    # Run the model
    interpreter.invoke()
    
    # Get the result
    keypoints_with_scores = interpreter.get_tensor(output_details[0]['index'])
    
    return keypoints_with_scores