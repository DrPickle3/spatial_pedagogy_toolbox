import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import json
from datetime import datetime
import os

from .analysis import calculate_affine_transform
from . import image


class Controller:
    def __init__(self, model, view, experiment_path=None):
        self.model = model
        self.view = view
        self.model.experiment_path = experiment_path
        self._bind_events()

    def _bind_events(self):
        self.view.image_canvas.bind("<Button-1>", lambda event: self._add_landmark(event, 'image'))
        self.view.csv_canvas.bind("<Button-1>", lambda event: self._add_landmark(event, 'csv'))
        # Right-click to delete is complex with the new list-based model, so disabling for now.
        # self.view.image_canvas.bind("<Button-3>", lambda event: self._delete_landmark(event, 'image'))
        # self.view.csv_canvas.bind("<Button-3>", lambda event: self._delete_landmark(event, 'csv'))

    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg;*.jpeg")])
        if not path:
            return
        try:
            raw_image = Image.open(path).convert("RGBA")
            self.model.image_path = path
            processed_image = self._preprocess_image(raw_image)
            self.model.image = processed_image
            self.model.image_tk = ImageTk.PhotoImage(self.model.image)
            self.view.display_image(self.model.image_tk)
            self.view.update_status(f"Loaded and processed Image: {path}")
            self.model.clear_landmarks()
            self._redraw_landmarks()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or process image file: {e}")

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            raw_data = np.loadtxt(path, delimiter=',')
            self.model.csv_path = path
            processed_image = self._preprocess_csv(raw_data)
            self.model.csv_tk = ImageTk.PhotoImage(processed_image)
            self.view.display_csv_as_image(self.model.csv_tk)
            self.view.update_status(f"Loaded and processed CSV: {path}")
            self.model.clear_landmarks()
            self._redraw_landmarks()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or process CSV file: {e}")

    def _add_landmark(self, event, canvas_type):
        point = (event.x - 25, event.y - 25) # Subtract padding
        if canvas_type == 'image':
            if not self.model.add_image_landmark(point):
                self.view.update_status("Maximum number of image landmarks (12) reached.")
                return
        elif canvas_type == 'csv':
            if not self.model.add_csv_landmark(point):
                self.view.update_status("Maximum number of CSV landmarks (12) reached.")
                return
        
        self._redraw_landmarks()
        self._update_calibrate_button_state()

    def undo_last_point(self):
        self.model.undo_last_landmark()
        self._redraw_landmarks()
        self._update_calibrate_button_state()

    def _redraw_landmarks(self):
        self.view.clear_landmarks()
        for i, (x, y) in enumerate(self.model.landmarks_image):
            self.view.draw_landmark(self.view.image_canvas, x + 25, y + 25, i + 1, color="red")
        for i, (x, y) in enumerate(self.model.landmarks_csv):
            self.view.draw_landmark(self.view.csv_canvas, x + 25, y + 25, i + 1, color="green")
        self.view.update_landmark_lists(self.model.landmarks_csv, self.model.landmarks_image)

    def _update_calibrate_button_state(self):
        num_pairs = min(len(self.model.landmarks_image), len(self.model.landmarks_csv))
        if num_pairs >= 3:
            self.view.calibrate_button.config(state="normal")
        else:
            self.view.calibrate_button.config(state="disabled")

    def run_calibration(self):
        image_points, csv_points = self.model.get_landmark_pairs()
        
        if len(image_points) < 3:
            messagebox.showerror("Calibration Error", "At least 3 landmark pairs are required.")
            return

        try:
            results = calculate_affine_transform(csv_points, image_points)
            self.model.calibration_results = results
            
            overlay_image = self._create_overlay_image()
            self.view.show_results_window(results, overlay_image)
            
        except ValueError as e:
            messagebox.showerror("Calibration Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during calibration: {e}")

    def _create_overlay_image(self):
        # Ensure the base image for overlay is the one displayed on the canvas, with padding
        base_image = Image.new("RGBA", (self.view.canvas_size, self.view.canvas_size), (211, 211, 211, 255))
        base_image.paste(self.model.image, (25, 25))
        overlay = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        image_points, csv_points = self.model.get_landmark_pairs()
        affine_matrix_2x3 = np.array(self.model.calibration_results['affine_matrix'])[:2, :]
        
        # 1. Draw all scaled CSV points transformed
        print(self.model.scaled_csv_data)
        if self.model.scaled_csv_data is not None:
            all_csv_points_padded = np.hstack([self.model.scaled_csv_data, np.ones((self.model.scaled_csv_data.shape[0], 1))])
            all_transformed_points = np.dot(all_csv_points_padded, affine_matrix_2x3.T)
            for p in all_transformed_points:
                print(p)
                # Offset by padding for drawing
                p_draw = p + 25
                draw.ellipse((p_draw[0]-2, p_draw[1]-2, p_draw[0]+2, p_draw[1]+2), fill=(0, 0, 255, 50))

        # 2. Draw user-selected landmark pairs
        csv_points_padded = np.hstack([csv_points, np.ones((csv_points.shape[0], 1))])
        transformed_landmark_points = np.dot(csv_points_padded, affine_matrix_2x3.T)

        for i in range(len(image_points)):
            # Draw target image points (as red crosses)
            p_target = image_points[i] + 25 # Offset by padding
            draw.line((p_target[0]-5, p_target[1], p_target[0]+5, p_target[1]), fill="red", width=2)
            draw.line((p_target[0], p_target[1]-5, p_target[0], p_target[1]+5), fill="red", width=2)

            # Draw transformed csv points (as dark blue circles)
            p_transformed = transformed_landmark_points[i] + 25 # Offset by padding
            print(p_transformed)
            draw.ellipse((p_transformed[0]-4, p_transformed[1]-4, p_transformed[0]+4, p_transformed[1]+4), fill="blue", outline="black")

        return Image.alpha_composite(base_image, overlay)

    def save_results(self):
        if not self.model.calibration_results:
            messagebox.showwarning("No Results", "No calibration has been performed yet.")
            return

        base_filename = os.path.join(self.model.experiment_path, "calibration_results")
        json_path = base_filename + ".json"
        overlay_path = base_filename + "_overlay.png"

        try:
            # Prepare data for JSON
            data_to_save = {
                "timestamp": datetime.now().isoformat(),
                "csv_file": self.model.csv_path,
                "image_file": self.model.image_path,
                "landmarks": {
                    "image": self.model.landmarks_image,
                    "csv": self.model.landmarks_csv
                },
                "calibration_results": self.model.calibration_results
            }

            with open(json_path, 'w') as f:
                json.dump(data_to_save, f, indent=4)

            # Save overlay image
            overlay_image = self._create_overlay_image()
            overlay_image.save(overlay_path)

            self.view.update_status(f"Results saved to {self.model.experiment_path}")
            messagebox.showinfo("Success", f"Results and overlay image saved to:\n{self.model.experiment_path}")

        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save results: {e}")

    def _preprocess_csv(self, raw_data):
        # Scale Coordinates
        x_min, y_min = raw_data.min(axis=0)
        x_max, y_max = raw_data.max(axis=0)
        
        target_dim = self.view.canvas_size - 50 # Account for 25px padding on each side
        scale_x = target_dim / (x_max - x_min) if (x_max - x_min) > 0 else 1
        scale_y = target_dim / (y_max - y_min) if (y_max - y_min) > 0 else 1
        scale = min(scale_x, scale_y)

        scaled_data = (raw_data - [x_min, y_min]) * scale
        self.model.scaled_csv_data = scaled_data # Store in model

        # Save Scaled CSV
        scaled_csv_path = os.path.join(self.model.experiment_path, "scaled_coordinates.csv")
        np.savetxt(scaled_csv_path, scaled_data, delimiter=',')

        # Generate Image from Points
        img = self._create_image_from_coords(scaled_data)

        # Save Visualization
        visualization_path = os.path.join(self.model.experiment_path, "points_visualization.png")
        img.save(visualization_path)

        # Final Crop
        cropped_img_np = image.auto_crop(np.array(img.convert('RGBA')), borders=50)
        cropped_img = Image.fromarray(cropped_img_np)
        
        return cropped_img

    def _create_image_from_coords(self, scaled_data):
        x_max, y_max = scaled_data.max(axis=0)
        img_size = (int(x_max + 20), int(y_max + 20))
        img = Image.new("L", img_size, "white")
        draw = ImageDraw.Draw(img)

        for x, y in scaled_data:
            draw.ellipse((x+10-2, y+10-2, x+10+2, y+10+2), fill="black", outline="black")
            
        return img

    def _preprocess_image(self, raw_image):
        # First Crop
        cropped_image_np = image.auto_crop(np.array(raw_image), borders=0)
        cropped_image = Image.fromarray(cropped_image_np)

        # Scale Image
        width, height = cropped_image.size
        target_dim = self.view.canvas_size - 50 # Account for 25px padding on each side
        if width > 0 and height > 0:
            scale = min(target_dim / width, target_dim / height)
            new_size = (int(width * scale), int(height * scale))
            scaled_image = cropped_image.resize(new_size, Image.LANCZOS)
        else:
            scaled_image = cropped_image

        # Second Crop
        final_image_np = image.auto_crop(np.array(scaled_image), borders=50)
        final_image = Image.fromarray(final_image_np)

        # Save Processed Image
        processed_image_path = os.path.join(self.model.experiment_path, "processed_image.png")
        final_image.save(processed_image_path)
        return final_image
