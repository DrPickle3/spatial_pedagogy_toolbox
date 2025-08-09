# Codebase Architecture

This document provides a high-level overview of the design patterns, file structure, and core logic of the calibration toolbox.

## Architectural Design: Model-View-Controller (MVC)

The application is structured using the **Model-View-Controller (MVC)** design pattern. This pattern separates the application's concerns into three distinct, interconnected components, which makes the code more organized, scalable, and easier to maintain.

* **Model (`calibration_tool/model.py`)**: The "brain" of the application.
    - It holds all the application's data and state: file paths, landmark coordinates, action history, preprocessed data, and final calibration results.
    - The Model is pure data and state management; it has no knowledge of the user interface and performs no calculations.

* **View (`calibration_tool/app.py`)**: The "face" of the application.
    - Its sole responsibility is to present the data from the Model to the user.
    - It builds the entire `tkinter` GUI, including canvases, buttons, and labels.
    - It displays the images and draws the landmarks. It does not store any state itself, but rather reflects the state of the Model.
    - User actions (mouse clicks, menu selections) are captured here but are handled by the Controller.

* **Controller (`calibration_tool/controller.py`)**: The "hands" and orchestrator of the application.
    - It acts as the intermediary between the Model and the View.
    - It contains all the application's business logic. It responds to user actions passed from the View (e.g., "Load CSV button clicked").
    - It calls utility modules to perform tasks like preprocessing images (`image.py`) or running calculations (`analysis.py`).
    - It updates the Model with new state (e.g., adding a landmark or storing calibration results).
    - After the Model is updated, the Controller instructs the View to refresh itself to display the new state.

## Project Structure

* `main.py`: The application entry point. It handles command-line argument parsing, sets up the timestamped experiment folder, and instantiates the Model, View, and Controller classes, wiring them together.
* `requirements.txt`: Lists the Python packages required to run the application.
* `tests/`: Contains all unit tests.
* `calibration_tool/`: The main application package.
    * `app.py`: **(View)** Defines all `tkinter` widgets, the GUI layout, and methods for drawing on the canvases.
    * `model.py`: **(Model)** A data class that holds the application's runtime state.
    * `controller.py`: **(Controller)** The core logic hub. Orchestrates file loading, preprocessing, landmark management, calibration, and saving.
    * `analysis.py`: **(Math/Logic)** Contains the `calculate_affine_transform` function, which performs the core mathematical computation using NumPy's least-squares algorithm.
    * `image.py`: **(Image Processing/Logic)** A utility module containing functions for all image manipulations: `auto_crop`, `remove_background`, `resize`, and `pad_image_to_center`.

## Core Logic Breakdown

The application logic can be split into three main categories:

1.  **UI Rendering (The View)**
    - **Location:** `calibration_tool/app.py`
    - **Key Functions:**
        - `_create_widgets()` and `_create_layout()`: Build the static layout of the application window.
        - `display_image()` and `display_csv_as_image()`: Update the canvases with new images.
        - `draw_landmark()`: Draws the circles and numbers for landmarks.
        - `show_results_window()`: Creates the pop-up window to display calibration statistics and the overlay image.

2.  **Mathematical and Image Processing (The Logic)**
    - **Location:** `calibration_tool/analysis.py`, `calibration_tool/image.py`
    - **Key Functions:**
        - `calculate_affine_transform()` in `analysis.py`: This is the heart of the calibration. It takes two sets of corresponding points and computes the optimal 2x3 affine matrix that maps one set to the other.
        - `auto_crop()` in `image.py`: Intelligently removes excess background from an image to frame the content.
        - `remove_background()` in `image.py`: Uses a flood-fill algorithm to create a transparency mask for the image's background.

3.  **Orchestration and State Management (The Controller)**
    - **Location:** `calibration_tool/controller.py`
    - **Key Functions:**
        - `__init__()` and `_bind_events()`: Wire up the controller to listen to events from the view.
        - `load_csv()` and `load_image()`: Handle the file dialogs and initiate the preprocessing workflows.
        - `_preprocess_csv()` and `_preprocess_image()`: Contain the multi-step pipelines for standardizing the input CSV and image files, including calling functions from `image.py`.
        - `run_calibration()`: Gathers landmark pairs from the Model, calls `calculate_affine_transform`, and tells the View to display the results.
        - `save_results()`: Gathers all relevant data from the Model and writes the JSON and overlay PNG files to the experiment directory.
