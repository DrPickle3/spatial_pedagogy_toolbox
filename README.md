# 2D Affine Transformation Calibration Toolbox

A tool with a graphical user interface for calculating the 2D affine transformation between a set of CSV coordinates and a corresponding image.

## Features

* **Standardized Workflow**: Each run creates a dedicated, timestamped experiment folder to store all inputs and outputs.
* **Input Preprocessing**: Automatically scales and visualizes CSV data, and normalizes input images for consistent calibration.
* **Interactive Landmark Selection**: Interactively select corresponding points on the CSV data visualization and the image.
* **Affine Transformation**: Calculates the affine transformation matrix using a least-squares fit.
* **Visual Feedback**: Generates and displays an overlay image showing the accuracy of the transformation.
* **Save & Reload**: Save calibration results (matrix, error metrics, landmarks) to a JSON file and preload data via command-line for reproducibility.

## Installation

1.  Clone the repository.
2.  It is highly recommended to use a Python virtual environment.
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Install the toolbox package itself:
    ```bash
    pip install -e .
    ```

## Usage

1.  Run the application from the command line:
    ```bash
    python main.py
    ```
2.  When prompted, enter a name for your experiment. A new directory named `Your-Name_YYYYMMDD_HHMMSS` will be created in the current directory.
3.  Use the **File > Load CSV...** menu to select your coordinate file. A visualization of the scaled points will appear in the left panel.
4.  Use the **File > Load Image...** menu to select your image file. A cropped and scaled version will appear in the right panel.
5.  Select landmark pairs by clicking a point on the **right image panel** and then its corresponding point on the **left CSV panel**.
6.  Once at least 3 pairs are selected, the **Calibrate** button will become active.
7.  Click **Calibrate** to compute the transformation. A results window will appear with statistics and an overlay image.
8.  Click **Save Results** to save the landmarks, transformation matrix, and overlay image into your experiment folder.

### Command-Line Arguments

You can also automate the startup process using command-line arguments:

* `--canvas-size`: Set the size of the display canvases (e.g., `--canvas-size 800`).
* `--csv`: Preload a CSV file by providing its path.
* `--png`: Preload an image file by providing its path.
* `--experiment_name`: Specify the experiment name directly.
* `--force-overwrite`: If the experiment folder already exists and is not empty, this flag allows overwriting it.
