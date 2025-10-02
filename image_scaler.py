import os
import zipfile
from PIL import Image
from math import ceil

BASE_DIR = "."
# Configuration
SCALES = {
    "16x20": (1600, 2000),
    "11x14": (1571, 2000),
    "18x24": (1728, 2304),
    "24x36": (1728, 2592),
    "50x70": (1890, 2646), 
}

def scale_and_crop(image_path, size):
    with Image.open(image_path) as img:
        # Convert to RGB mode to ensure consistent color handling
        if img.mode != 'RGB':
            img = img.convert('RGB')
            
        # Check if image is horizontal and rotate if needed
        should_rotate = img.width > img.height
        if should_rotate:
            img = img.rotate(90, expand=True, resample=Image.BICUBIC)
        
        aspect_ratio = img.width / img.height
        target_width, target_height = size
        target_aspect_ratio = target_width / target_height

        if aspect_ratio > target_aspect_ratio:  # Image is wider
            new_height = target_height
            new_width = ceil(new_height * aspect_ratio)
        else:  # Image is taller or equal aspect ratio
            new_width = target_width
            new_height = ceil(new_width / aspect_ratio)

        img = img.resize((new_width, new_height), Image.LANCZOS)
        left = (new_width - target_width) / 2
        top = (new_height - target_height) / 2
        right = left + target_width
        bottom = top + target_height

        return img.crop((left, top, right, bottom))

def create_zip(archive_path, files):
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path, arcname in files:
            zipf.write(file_path, arcname)

def process_folder(folder_path):
    print(f"Processing folder: {folder_path}")
    folder_name = os.path.basename(folder_path)
    scaled_dir = os.path.join(folder_path, "scaled")
    os.makedirs(scaled_dir, exist_ok=True)

    image_paths = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.lower().endswith((".png", ".webp", ".jpg", ".jpeg"))
    ]

    for scale_name, size in SCALES.items():
        scaled_images = []

        for idx, image_path in enumerate(image_paths, start=1):
            scaled_image_path = os.path.join(
                scaled_dir, f"{idx}_{folder_name}_{scale_name}.png"
            )
            scaled_image = scale_and_crop(image_path, size)
            # Save with maximum quality settings
            scaled_image.save(scaled_image_path, format="PNG", optimize=False)
            scaled_images.append(scaled_image_path)

        archive_base_name = os.path.join(scaled_dir, f"{folder_name}_{scale_name}")
        current_files = []
        for scaled_image_path in scaled_images:
            arcname = os.path.basename(scaled_image_path)
            current_files.append((scaled_image_path, arcname))

        archive_path = f"{archive_base_name}.zip"
        create_zip(archive_path, current_files)

if __name__ == "__main__":
    images_dir = os.path.expanduser(BASE_DIR)

    for folder in os.listdir(images_dir):
        folder_path = os.path.join(images_dir, folder)
        # Skip venv folder and folders that already have 'scaled'
        if (
            os.path.isdir(folder_path)
            and folder != "venv"
            and "scaled" not in os.listdir(folder_path)
        ):
            process_folder(folder_path)
