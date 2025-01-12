# Image Scaler

## Install on Mac:

```bash
git clone https://github.com/oleksii-pi/image-scaler
cd image-scaler
chmod +x run.sh
./run.sh
```

## Main Features and Limitations:

- Automatically scales PNG images in specified folders to multiple predefined sizes:
  - 16x20 (1600px x 2000px)
  - 11x14 (1100px x 1400px)
  - 18x24 (1800px x 2400px)
  - 24x36 (2400px x 3600px)
  - 50x70 (5000px x 7000px)
- Crops images to maintain the aspect ratio and maximize usage of the original image.
- Outputs scaled images into appropriately named ZIP archives.
- Ensures that each archive does not exceed 20 MB.
- Processes all subfolders in the specified directory that do not contain a `scaled` subfolder.

## Requirements:

- Python 3.x
- `pip` package manager
- MacOS (other systems may require adjustments to the `run.sh` script).

## Usage:

1. Clone the repository and navigate to the project directory.
2. Make the `run.sh` script executable using `chmod +x run.sh`.
3. Run the script with `./run.sh`.
4. Place your images in the desired folder structure within the root directory.
5. The script will automatically detect folders and process PNG images.

## Output:

- Scaled images are saved in a `scaled` subfolder within each processed directory.
- Archives are named using the folder name and size (e.g., `Birds_16x20.zip`).
- If an archive exceeds 20MB, it is split into multiple archives (e.g., `Birds_16x20_2.zip`).
