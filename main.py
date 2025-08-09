import tkinter as tk
from tkinter import simpledialog
from datetime import datetime
import os
import argparse # <-- Import
from calibration_tool.app import App
from calibration_tool.model import CalibrationModel
from calibration_tool.controller import Controller

if __name__ == "__main__":
    # --- Add this block ---
    parser = argparse.ArgumentParser(description="2D Affine Transformation Calibration Tool.")
    parser.add_argument(
        '--canvas-size',
        type=int,
        default=500,
        help="The width and height in pixels for the main image canvases."
    )
    args = parser.parse_args()
    # --- End block ---

    # Add 150 to the canvas size
    canvas_size = args.canvas_size

    root = tk.Tk()
    root.withdraw()  # Hide the main window until we have the experiment name

    experiment_name = simpledialog.askstring("Experiment Name", "Enter a name for this experiment:")
    if not experiment_name:
        root.destroy()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_path = os.path.join(os.getcwd(), f"{experiment_name}_{timestamp}")
        os.makedirs(experiment_path, exist_ok=True)

        root.deiconify() # Show the main window
        root.title("2D Affine Transformation Calibration Tool")
        
        width = canvas_size * 2 + 200
        height = canvas_size + 300
        root.geometry(f"{width}x{height}")
        root.minsize(width, height)
        root.resizable(True, True)

        model = CalibrationModel()
        # Pass the canvas_size to the App constructor
        view = App(root, canvas_size=canvas_size) # <-- Modify this line
        controller = Controller(model, view, experiment_path=experiment_path)
        view.controller = controller
        
        root.mainloop()

