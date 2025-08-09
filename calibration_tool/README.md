# spatial_pedagogy_toolbox

A 2D affine transformation calibration tool with a graphical user interface.

## Features

*   **Load Data**: Load CSV and image files (PNG, JPEG).
*   **Landmark Selection**: Interactively select corresponding points on the CSV data visualization and the image.
*   **Affine Transformation**: Calculates the affine transformation matrix from image points to CSV points.
*   **Visual Feedback**: Displays the transformed points overlaid on the image.
*   **Save Results**: Save the calibration results, including the transformation matrix and error metrics, to a JSON file.

## New Features (as of latest update)

*   **Command-Line Resolution Control**: The size of the two main image canvases can be controlled via the command line. Use the `--canvas-size` argument to set the desired dimension (e.g., `python main.py --canvas-size 800`).
*   **Scalable UI**: The landmark lists are now in a scrollable frame, preventing the main window from resizing as points are added.
*   **Affine Transformation**: The tool uses a full affine transformation, which includes rotation, scaling, and shearing in addition to translation.

## Usage

1.  Run the application from the command line:
    ```bash
    python main.py
    ```
2.  Provide a name for the experiment. A new directory will be created to store the results.
3.  Use the "File" menu to load a CSV file and an image.
4.  Click on the image to place a landmark, then click on the corresponding point on the CSV visualization.
5.  Once at least 3 landmark pairs are selected, the "Calibrate" button will be enabled.
6.  Click "Calibrate" to compute the transformation and view the results.
7.  Save the results if desired.