import tkinter as tk
from tkinter import simpledialog
from datetime import datetime
import os
import argparse
import sys
from calibration_tool.app import App
from calibration_tool.model import CalibrationModel
from calibration_tool.controller import Controller

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="2D Affine Transformation Calibration Tool.")
    parser.add_argument('--canvas-size', type=int, default=500, help="The width and height for the main image canvases.")
    parser.add_argument('--csv', type=str, help="Path to the CSV file to preload.")
    parser.add_argument('--png', type=str, help="Path to the PNG file to preload.")
    parser.add_argument('--experiment_name', type=str, help="The name for the experiment.")
    parser.add_argument('--force-overwrite', action='store_true', help="Force overwrite of a non-empty experiment folder.")
    args = parser.parse_args()

    if args.csv and not os.path.exists(args.csv):
        print(f"Error: CSV file not found at {args.csv}", file=sys.stderr)
        sys.exit(1)
    if args.png and not os.path.exists(args.png):
        print(f"Error: PNG file not found at {args.png}", file=sys.stderr)
        sys.exit(1)

    root = tk.Tk()
    root.withdraw()

    experiment_name = args.experiment_name
    if not experiment_name:
        experiment_name = simpledialog.askstring("Experiment Name", "Enter a name for this experiment:")
    
    if not experiment_name:
        root.destroy()
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_path = os.path.join(os.getcwd(), f"{experiment_name}_{timestamp}")

        if os.path.exists(experiment_path) and os.listdir(experiment_path) and not args.force_overwrite:
            print(f"Error: Experiment folder '{experiment_path}' is not empty. Use --force-overwrite to proceed.", file=sys.stderr)
            root.destroy()
            sys.exit(1)
        
        os.makedirs(experiment_path, exist_ok=True)

        root.deiconify()
        root.title("2D Affine Transformation Calibration Tool")
        
        canvas_size = args.canvas_size
        width = canvas_size * 2 + 200
        height = canvas_size + 300
        root.geometry(f"{width}x{height}")
        root.geometry(f"{width}x{height}")
        root.minsize(width, height)
        root.resizable(True, True)

        model = CalibrationModel()
        view = App(root, canvas_size=canvas_size)
        controller = Controller(model, view, experiment_path=experiment_path)
        view.controller = controller

        if args.png:
            controller.load_image(args.png)
        if args.csv:
            controller.load_csv(args.csv)
        
        root.mainloop()

