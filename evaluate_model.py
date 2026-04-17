# File: evaluate_model.py
# Description: Generates Accuracy, Precision, F1, and Confusion Matrix using Leave-One-Out Cross-Validation.

import os
import cv2
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime

# --- Import Core Model Functions ---
# We re-define these to ensure this script is standalone and robust
from model import movenet, input_size

def get_keypoints(image):
    """Wrapper to run MoveNet."""
    if not isinstance(image, tf.Tensor):
        image = tf.convert_to_tensor(image, dtype=tf.uint8)
    if image.shape[-1] != 3:
        image = tf.image.grayscale_to_rgb(image)
    input_image = tf.expand_dims(image, axis=0)
    input_image = tf.image.resize_with_pad(input_image, input_size, input_size)
    keypoints_with_scores = movenet(input_image)
    return keypoints_with_scores

def flatten_keypoints(keypoints_with_scores):
    """Flattens keypoints for vector comparison."""
    keypoints = np.squeeze(keypoints_with_scores)[:, :2]
    return keypoints.flatten()

def load_dataset(image_database_dir):
    """Loads all images and converts them to embedding vectors."""
    dataset = [] # List of dicts: {'label': name, 'id': unique_id, 'vector': np_array}
    
    if not os.path.isdir(image_database_dir):
        print(f"Error: Directory {image_database_dir} not found.")
        return []

    print(f"Loading dataset from: {image_database_dir}")
    classes = sorted(os.listdir(image_database_dir))
    
    for pose_name in classes:
        pose_dir = os.path.join(image_database_dir, pose_name)
        if os.path.isdir(pose_dir):
            image_files = [f for f in os.listdir(pose_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
            print(f"  Processing class '{pose_name}': {len(image_files)} images")
            
            for i, image_file in enumerate(image_files):
                image_path = os.path.join(pose_dir, image_file)
                unique_id = f"{pose_name}|{i}"
                
                try:
                    # Read and Process
                    image = tf.io.read_file(image_path)
                    image = tf.image.decode_jpeg(image)
                    keypoints = get_keypoints(image)
                    vector = flatten_keypoints(keypoints).reshape(1, -1)
                    
                    dataset.append({
                        'label': pose_name,
                        'id': unique_id,
                        'vector': vector
                    })
                except Exception as e:
                    print(f"    Failed to load {image_file}: {e}")

    return dataset, classes

def evaluate():
    # 1. Setup
    base_dir = os.path.dirname(os.path.abspath(__file__))
    image_db_dir = os.path.join(base_dir, 'imagedatabase')
    output_dir = os.path.join(base_dir, 'evaluation_results')
    os.makedirs(output_dir, exist_ok=True)

    # 2. Load Data
    data, classes = load_dataset(image_db_dir)
    if not data:
        return

    y_true = []
    y_pred = []

    print("\n--- Starting Leave-One-Out Evaluation ---")
    
    # 3. Leave-One-Out Loop
    for i, test_item in enumerate(data):
        test_vector = test_item['vector']
        true_label = test_item['label']
        test_id = test_item['id']
        
        best_score = -1.0
        predicted_label = "Unknown"

        # Compare against ALL other items
        for ref_item in data:
            # Skip self (Crucial for validity)
            if test_item['id'] == ref_item['id']:
                continue
            
            # Cosine Similarity
            score = cosine_similarity(ref_item['vector'], test_vector)[0][0]
            
            if score > best_score:
                best_score = score
                predicted_label = ref_item['label']

        y_true.append(true_label)
        y_pred.append(predicted_label)
        
        # simple progress indicator
        if i % 5 == 0:
            print(f"Processed {i}/{len(data)}: True={true_label}, Pred={predicted_label}, Score={best_score:.2f}")

    # 4. Metrics Calculation
    print("\n--- Calculating Metrics ---")
    accuracy = accuracy_score(y_true, y_pred)
    report = classification_report(y_true, y_pred, target_names=classes, zero_division=0)
    conf_matrix = confusion_matrix(y_true, y_pred, labels=classes)

    # 5. Save Text Report
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = os.path.join(output_dir, f"metrics_report_{timestamp}.txt")
    
    with open(report_path, "w") as f:
        f.write("POSE ESTIMATION EVALUATION REPORT\n")
        f.write("=================================\n")
        f.write(f"Date: {timestamp}\n")
        f.write(f"Total Images: {len(data)}\n")
        f.write(f"Overall Accuracy: {accuracy:.4f}\n\n")
        f.write("Detailed Classification Report:\n")
        f.write(report)
        f.write("\n\nConfusion Matrix (Raw):\n")
        f.write(np.array2string(conf_matrix))

    print(f"\nReport saved to: {report_path}")
    print(f"Overall Accuracy: {accuracy*100:.2f}%")

    # 6. Generate Confusion Matrix Plot
    plt.figure(figsize=(12, 10))
    sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues', 
                xticklabels=classes, yticklabels=classes)
    plt.xlabel('Predicted Label')
    plt.ylabel('True Label')
    plt.title(f'Confusion Matrix (Acc: {accuracy:.2f})')
    
    plot_path = os.path.join(output_dir, f"confusion_matrix_{timestamp}.png")
    plt.savefig(plot_path)
    print(f"Confusion Matrix saved to: {plot_path}")
    plt.close()

if __name__ == "__main__":
    evaluate()