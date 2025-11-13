import glob
import os
from pathlib import Path
from PIL import Image
from ultralytics import YOLO

def find_trees_in_images():
    folder_path = Path("../data/streetview")
    output_trees = Path("../data/trees")
    output_trees.mkdir(parents=True, exist_ok=True)

    model = YOLO("../models/best.pt")

    # Get all .jpeg files
    for file_path in folder_path.glob("*.jp*g"):
        print(f"Processing: {file_path}")

        results = model.predict(source=file_path, save=False)

        # Loop through detections in this image
        for r in results:
            boxes = r.boxes
            names = model.names  # mapping: class_id -> class_name

            img = Image.open(file_path)

            for box in boxes:
                cls_id = int(box.cls)
                label = names[cls_id]
                conf = float(box.conf)

                # Filter for 'tree'
                if label.lower() == "tree":
                    # Get bounding box coordinates (x1, y1, x2, y2)
                    x1, y1, x2, y2 = map(int, box.xyxy[0])

                    # Crop the image
                    cropped = img.crop((x1, y1, x2, y2))

                    # Save cropped image
                    save_path = output_trees / f"{file_path.stem}_tree_{x1}_{y1}.jpg"
                    cropped.save(save_path)

                    print(f"Saved: {save_path} (conf={conf:.2f})")