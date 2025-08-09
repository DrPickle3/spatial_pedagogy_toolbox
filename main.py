import tkinter as tk
from tkinter import simpledialog
from datetime import datetime
import os
from calibration_tool.app import App
from calibration_tool.model import CalibrationModel
from calibration_tool.controller import Controller

if __name__ == "__main__":
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
        
        # Set a minimum size for the window, and allow it to be resizable
        root.minsize(850, 600)
        root.resizable(True, True)

        model = CalibrationModel()
        view = App(root)
        controller = Controller(model, view, experiment_path=experiment_path)
        view.controller = controller
        
        root.mainloop()

