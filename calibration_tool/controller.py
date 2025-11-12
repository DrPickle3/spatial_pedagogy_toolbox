# -*- coding: utf-8 -*-
"""
This module defines the Controller for the calibration application.

In the Model-View-Controller (MVC) architecture, the Controller is the core
logic hub. It responds to user actions from the View (e.g., button clicks),
interacts with the Model to update the application's state, and calls on
other modules (like `analysis.py` and `image.py`) to perform specialized tasks.
"""
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import json
from datetime import datetime
import os
import csv

from .analysis import calculate_affine_transform
from . import image


class Controller:
    """
    The Controller class orchestrates the application's logic.

    It connects the user interface (View) with the data store (Model),
    handling all user interactions and data processing workflows.

    Attributes:
        model (CalibrationModel): The data model instance.
        view (App): The main application window (GUI) instance.
    """

    def __init__(self, model, view, experiment_path=None):
        """
        Initializes the Controller.

        Args:
            model (CalibrationModel): An instance of the application's data model.
            view (App): An instance of the main GUI application window.
            experiment_path (str, optional): The path to the directory where
                all outputs for this session will be saved. Defaults to None.
        """
        self.model = model
        self.view = view
        # The experiment path is created in main.py and passed here.
        self.model.experiment_path = experiment_path
        # Connect the controller's methods to the view's events (e.g., clicks).
        self._bind_events()

    def _bind_events(self):
        """
        Binds user interface events to controller methods.

        This is where the connection between the View and Controller is made.
        For example, a left-click on the image canvas is linked to the
        _add_landmark method.
        """
        # A lambda function is used to pass additional arguments to the event handler.
        # Here, we tell the handler which canvas ('image' or 'csv') was clicked.
        self.view.image_canvas.bind(
            "<Button-1>", lambda event: self._add_landmark(event, "image")
        )
        self.view.csv_canvas.bind(
            "<Button-1>", lambda event: self._add_landmark(event, "csv")
        )

    def load_image(self, path=None):
        """
        Handles the entire workflow for loading and processing an image file.

        Args:
            path (str, optional): The file path to the image. If None, a file
                dialog will be opened for the user to choose. Defaults to None.
        """
        # If no path is provided (e.g., from a command-line argument),
        # open a standard file dialog for the user.
        if not path:
            path = filedialog.askopenfilename(
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg;*.jpeg")]
            )
        # If the user cancels the dialog, the path will be empty.
        if not path:
            return
        try:
            # Open the image using Pillow and ensure it has an alpha channel.
            raw_image = Image.open(path).convert("RGBA")
            # Store the original path in the model.
            self.model.image_path = path
            # The image goes through a multi-step preprocessing pipeline.
            processed_image = self._preprocess_image(raw_image)
            # Store the processed image in the model.
            self.model.image = processed_image
            # Convert the Pillow image to a format Tkinter can display.
            self.model.image_tk = ImageTk.PhotoImage(self.model.image)
            # Tell the view to display the new image.
            self.view.display_image(self.model.image_tk)
            self.view.update_status(f"Loaded and processed Image: {path}")
            # When a new image is loaded, clear any old landmarks.
            self.model.clear_landmarks()
            self._redraw_landmarks()
        except Exception as e:
            # Show a user-friendly error message if anything goes wrong.
            messagebox.showerror("Error", f"Failed to load or process image file: {e}")

    def load_csv(self, path=None):
        """
        Handles the entire workflow for loading and processing a CSV file.

        Args:
            path (str, optional): The file path to the CSV. If None, a file
                dialog will be opened. Defaults to None.
        """
        if not path:
            path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            # Load the CSV data into a NumPy array.
            raw_data = np.loadtxt(path, delimiter=",", usecols=(-3, -2), skiprows=1)
            self.model.csv_path = path
            # Preprocess the CSV data, which includes scaling and converting it to an image.
            processed_image = self._preprocess_csv(raw_data)
            # Convert the resulting image to a Tkinter-compatible format.
            self.model.csv_tk = ImageTk.PhotoImage(processed_image)
            # Tell the view to display the CSV data visualization.
            self.view.display_csv_as_image(self.model.csv_tk)
            self.view.update_status(f"Loaded and processed CSV: {path}")
            # Clear any old landmarks.
            self.model.clear_landmarks()
            self._redraw_landmarks()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or process CSV file: {e}")

    def _add_landmark(self, event, canvas_type):
        """
        Adds a landmark point when the user clicks on a canvas.

        Args:
            event (tk.Event): The tkinter event object, which contains the click coordinates.
            canvas_type (str): Either 'image' or 'csv' to identify the source canvas.
        """
        # The canvas has a 25px padding, so we subtract it to get the coordinate
        # relative to the image itself.
        point = (event.x - 25, event.y - 25)
        if canvas_type == "image":
            # The model handles the logic of adding the point and checking the limit.
            if not self.model.add_image_landmark(point):
                self.view.update_status(
                    "Maximum number of image landmarks (12) reached."
                )
                return
        elif canvas_type == "csv":
            if not self.model.add_csv_landmark(point):
                self.view.update_status("Maximum number of CSV landmarks (12) reached.")
                return

        # After adding a point, update the display.
        self._redraw_landmarks()
        # Check if the "Calibrate" button should be enabled.
        self._update_calibrate_button_state()

    def undo_last_point(self):
        """Removes the most recently added landmark."""
        # The model contains the logic for undoing the last action.
        self.model.undo_last_landmark()
        # Redraw the canvases to reflect the change.
        self._redraw_landmarks()
        self._update_calibrate_button_state()

    def _redraw_landmarks(self):
        """
        Clears and redraws all landmarks on both canvases.

        This ensures the display is always in sync with the model's state.
        """
        self.view.clear_landmarks()
        # Draw the image landmarks in red.
        for i, (x, y) in enumerate(self.model.landmarks_image):
            # Add the padding back for drawing on the canvas.
            self.view.draw_landmark(
                self.view.image_canvas, x + 25, y + 25, i + 1, color="red"
            )
        # Draw the CSV landmarks in green.
        for i, (x, y) in enumerate(self.model.landmarks_csv):
            self.view.draw_landmark(
                self.view.csv_canvas, x + 25, y + 25, i + 1, color="green"
            )
        # Update the text lists of landmarks in the side panel.
        self.view.update_landmark_lists(
            self.model.landmarks_csv, self.model.landmarks_image
        )

    def _update_calibrate_button_state(self):
        """
        Enables or disables the 'Calibrate' button based on the number of landmark pairs.
        """
        # We need at least 3 complete pairs to perform calibration.
        num_pairs = min(len(self.model.landmarks_image), len(self.model.landmarks_csv))
        if num_pairs >= 3:
            # The 'state' of a tkinter widget can be 'normal' (enabled) or 'disabled'.
            self.view.calibrate_button.config(state="normal")
        else:
            self.view.calibrate_button.config(state="disabled")

    def run_calibration(self):
        """
        Executes the core calibration process.
        """
        # Get the complete pairs of landmarks from the model.
        image_points, csv_points = self.model.get_landmark_pairs()

        if len(image_points) < 3:
            messagebox.showerror(
                "Calibration Error", "At least 3 landmark pairs are required."
            )
            return

        try:
            # Call the analysis function to calculate the transformation.
            # Note the order: we are mapping CSV points TO image points.
            results = calculate_affine_transform(csv_points, image_points)
            # Store the results dictionary in the model.
            self.model.calibration_results = results

            # Generate the visual overlay to show the accuracy of the fit.
            overlay_image = self._create_overlay_image()
            # Tell the view to open the results window.
            self.view.show_results_window(results, overlay_image)

        except ValueError as e:
            messagebox.showerror("Calibration Error", str(e))
        except Exception as e:
            messagebox.showerror(
                "Error", f"An unexpected error occurred during calibration: {e}"
            )

    def _create_overlay_image(self):
        """
        Generates an image that visually represents the calibration result.

        It overlays the transformed CSV points onto the original image.
        A good calibration will show the blue dots (transformed CSV points)
        very close to the red crosses (original image landmarks).

        Returns:
            PIL.Image.Image: The composite overlay image.
        """
        # Create a blank white canvas to draw on.
        base_image = Image.new(
            "RGBA", (self.view.canvas_size, self.view.canvas_size), (255, 255, 255, 255)
        )
        # Paste the processed image onto the canvas.
        base_image.paste(self.model.image, (0, 0))

        # Create a transparent layer for drawing the overlay graphics.
        overlay = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        image_points, csv_points = self.model.get_landmark_pairs()
        # The affine matrix is 3x3, but for transforming 2D points, we only need the 2x3 part.
        affine_matrix_2x3 = np.array(self.model.calibration_results["affine_matrix"])[ 
            :2, :
        ]

        # --- Visualization Part 1: Transform ALL CSV points ---
        # This shows how the entire CSV point cloud maps onto the image space.
        if self.model.scaled_csv_data is not None:
            # Augment the coordinates with a column of ones for matrix multiplication.
            all_csv_points_padded = np.hstack(
                [
                    self.model.scaled_csv_data,
                    np.ones((self.model.scaled_csv_data.shape[0], 1)),
                ]
            )
            # Apply the transformation. The result is a new set of 2D coordinates.
            all_transformed_points = np.dot(all_csv_points_padded, affine_matrix_2x3.T)
            # Draw each transformed point as a small, semi-transparent blue dot.
            for p in all_transformed_points:
                draw.ellipse(
                    (p[0] - 2, p[1] - 2, p[0] + 2, p[1] + 2),
                    fill=(0, 0, 255, 100),
                )

        # --- Visualization Part 2: Highlight the user-selected landmark pairs ---
        csv_points_padded = np.hstack([csv_points, np.ones((csv_points.shape[0], 1))])
        transformed_landmark_points = np.dot(csv_points_padded, affine_matrix_2x3.T)

        for i in range(len(image_points)):
            # Draw the target image landmark as a red cross. This is the "ground truth".
            p_target = image_points[i]
            draw.line(
                (p_target[0] - 5, p_target[1], p_target[0] + 5, p_target[1]),
                fill="red",
                width=2,
            )
            draw.line(
                (p_target[0], p_target[1] - 5, p_target[0], p_target[1] + 5),
                fill="red",
                width=2,
            )

            # Draw the corresponding CSV landmark after transformation as a blue circle.
            # The distance between this circle and the red cross is the error for that pair.
            p_transformed = transformed_landmark_points[i]
            draw.ellipse(
                (
                    p_transformed[0] - 4,
                    p_transformed[1] - 4,
                    p_transformed[0] + 4,
                    p_transformed[1] + 4,
                ),
                fill="darkblue",
                outline="black",
            )

        # Combine the base image with the drawing layer.
        return Image.alpha_composite(base_image, overlay)

    def save_results(self):
        """
        Saves the calibration results to a JSON file and the overlay to a PNG.
        """
        if not self.model.calibration_results:
            messagebox.showwarning(
                "No Results", "No calibration has been performed yet."
            )
            return

        # Define the output file paths within the experiment folder.
        base_filename = os.path.join(self.model.experiment_path, "calibration_results")
        json_path = base_filename + ".json"
        overlay_path = base_filename + "_overlay.png"

        try:
            # Prepare a dictionary with all the data we want to save.
            # We make a copy to avoid modifying the model's state directly.
            data_to_save = {
                "timestamp": datetime.now().isoformat(),
                "csv_file": self.model.csv_path,
                "image_file": self.model.image_path,
                "landmarks": {
                    "image": self.model.landmarks_image,
                    "csv": self.model.landmarks_csv,
                },
                "calibration_results": self.model.calibration_results.copy(),
            }
            # JSON cannot handle NumPy arrays, so we convert the matrix to a standard list.
            data_to_save["calibration_results"]["affine_matrix"] = data_to_save[
                "calibration_results"
            ]["affine_matrix"].tolist()

            # Write the dictionary to a JSON file with nice formatting.
            with open(json_path, "w") as f:
                json.dump(data_to_save, f, indent=4)

            # Generate and save the overlay image.
            overlay_image = self._create_overlay_image()
            overlay_image.save(overlay_path)

            self.view.update_status(f"Results saved to {self.model.experiment_path}")
            messagebox.showinfo(
                "Success",
                f"Results and overlay image saved to:\n{self.model.experiment_path}",
            )


            csv_points_padded = np.hstack([self.model.scaled_csv_data, np.ones((self.model.scaled_csv_data.shape[0], 1))])
            affine_matrix_2x3 = np.array(self.model.calibration_results["affine_matrix"])[:2, :]
            all_transformed_points = np.dot(csv_points_padded, affine_matrix_2x3.T)
            # CSV
            # Load original CSV data again (all columns)
            with open(self.model.csv_path, newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                fieldnames = reader.fieldnames

                data_rows = list(reader)

            # Attach results back to rows (keep row order)
            for row, transformed in zip(data_rows, all_transformed_points):
                row["x_transformed"] = transformed[0]  # first column
                row["y_transformed"] = transformed[1]  # second column

            # Write out new CSV with added columns
            calibrated_path = os.path.join(self.model.experiment_path, "calibrated_points.csv")
            with open(calibrated_path, "w", newline='', encoding='utf-8') as outfile:
                writer = csv.DictWriter(outfile, fieldnames=fieldnames + ["x_transformed", "y_transformed"])
                writer.writeheader()
                writer.writerows(data_rows)

            self.view.update_status(f"Calibrated points saved to {calibrated_path}")
            messagebox.showinfo("Success", f"Updated CSV saved to:\n{calibrated_path}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save results: {e}")

    def _preprocess_csv(self, raw_data):
        """
        Standardizes the raw CSV data for display and calibration.

        This involves scaling the points to fit the canvas and generating a
        visual representation (an image) of the points.

        Args:
            raw_data (np.ndarray): The raw coordinate data from the CSV file.

        Returns:
            PIL.Image.Image: An image representing the scaled CSV points.
        """
        # --- Step 1: Scale the coordinates to fit the canvas ---
        x_min, y_min = raw_data.min(axis=0)
        x_max, y_max = raw_data.max(axis=0)

        # We want the data to fit within the canvas, leaving a 25px margin.
        target_dim = self.view.canvas_size - 50
        # Calculate the scaling factor needed for each axis.
        scale_x = target_dim / (x_max - x_min) if (x_max - x_min) > 0 else 1
        scale_y = target_dim / (y_max - y_min) if (y_max - y_min) > 0 else 1
        # Use the smaller of the two scaling factors to maintain the aspect ratio.
        scale = min(scale_x, scale_y)

        # Apply the scaling. We first shift the data so the minimum is at (0,0).
        scaled_data = (raw_data - [x_min, y_min]) * scale
        # Store the scaled data in the model for later use in calibration.
        self.model.scaled_csv_data = scaled_data

        # --- Step 2: Save the intermediate scaled data ---
        scaled_csv_path = os.path.join(
            self.model.experiment_path, "scaled_coordinates.csv"
        )
        np.savetxt(scaled_csv_path, scaled_data, delimiter=",")

        # --- Step 3: Generate an image from the scaled points ---
        img = self._create_image_from_coords(scaled_data)

        # --- Step 4: Save the visualization of the points ---
        visualization_path = os.path.join(
            self.model.experiment_path, "points_visualization.png"
        )
        img.save(visualization_path)

        # --- Step 5: Crop the generated image to fit the content ---
        # This removes any excess white space around the points.
        cropped_img_np = image.auto_crop(np.array(img.convert("RGBA")), borders=50)
        cropped_img = Image.fromarray(cropped_img_np)

        return cropped_img

    def _create_image_from_coords(self, scaled_data):
        """
        Draws a set of coordinates onto a new image.

        Args:
            scaled_data (np.ndarray): The (N, 2) array of coordinates to draw.

        Returns:
            PIL.Image.Image: A new image with the points drawn as black ellipses.
        """
        # Determine the size of the image needed to contain all points.
        x_max, y_max = scaled_data.max(axis=0)
        img_size = (int(x_max + 20), int(y_max + 20)) # Add padding
        # Create a new white image.
        img = Image.new("L", img_size, "white")
        draw = ImageDraw.Draw(img)

        # Draw a small black ellipse for each coordinate.
        for x, y in scaled_data:
            draw.ellipse(
                (x + 10 - 2, y + 10 - 2, x + 10 + 2, y + 10 + 2),
                fill="black",
                outline="black",
            )

        return img

    def _preprocess_image(self, raw_image):
        """
        Standardizes the raw input image for display and calibration.

        This involves cropping, scaling, and saving the processed version.

        Args:
            raw_image (PIL.Image.Image): The raw image loaded from a file.

        Returns:
            PIL.Image.Image: The fully processed image.
        """
        # --- Step 1: Initial crop to remove uniform borders ---
        cropped_image_np = image.auto_crop(np.array(raw_image), borders=0)
        cropped_image = Image.fromarray(cropped_image_np)

        # --- Step 2: Scale the image to fit the canvas ---
        width, height = cropped_image.size
        target_dim = self.view.canvas_size - 50  # Leave a margin
        if width > 0 and height > 0:
            # Calculate the scale factor to fit the image, preserving aspect ratio.
            scale = min(target_dim / width, target_dim / height)
            new_size = (int(width * scale), int(height * scale))
            # Resize the image using a high-quality downsampling filter.
            scaled_image = cropped_image.resize(new_size, Image.LANCZOS)
        else:
            scaled_image = cropped_image

        # --- Step 3: Final crop with a border ---
        # This ensures the object is nicely framed in the canvas.
        final_image_np = image.auto_crop(np.array(scaled_image), borders=50)
        final_image = Image.fromarray(final_image_np)

        # --- Step 4: Save the processed image for reproducibility ---
        processed_image_path = os.path.join(
            self.model.experiment_path, "processed_image.png"
        )
        final_image.save(processed_image_path)
        return final_image
