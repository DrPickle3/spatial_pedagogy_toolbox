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
        self._pending_landmark_id = None
        self._bind_events()

    def _bind_events(self):
        self.view.image_canvas.bind("<Button-1>", lambda event: self._add_landmark_start(event))
        self.view.csv_canvas.bind("<Button-1>", lambda event: self._add_landmark_end(event))
        self.view.image_canvas.bind("<Button-3>", lambda event: self._delete_landmark(event, 'image'))
        self.view.csv_canvas.bind("<Button-3>", lambda event: self._delete_landmark(event, 'csv'))

    def load_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return
        try:
            raw_data = np.loadtxt(path, delimiter=',')
            self.model.csv_path = path
            processed_image = self._preprocess_csv(raw_data)
            self.model.image_tk = ImageTk.PhotoImage(processed_image)
            self.view.display_left_image(self.model.image_tk)
            self.view.update_status(f"Loaded and processed CSV: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or process CSV file: {e}")

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
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load or process image file: {e}")

    def _get_next_landmark_id(self):
        if not self.model.landmarks_image:
            return 1
        return max(self.model.landmarks_image.keys()) + 1

    def _add_landmark_start(self, event):
        if self._pending_landmark_id:
            self.view.update_status("Error: Select the corresponding point on the CSV panel first.")
            return
        if len(self.model.landmarks_image) >= 12:
            self.view.update_status("Error: Maximum of 12 landmarks reached.")
            return

        landmark_id = self._get_next_landmark_id()
        self._pending_landmark_id = landmark_id
        
        x, y = event.x, event.y
        self.model.landmarks_image[landmark_id] = (x, y)
        
        self.view.draw_landmark(self.view.image_canvas, x, y, landmark_id)
        self.view.update_landmark_lists(self.model.landmarks_csv, self.model.landmarks_image)
        self.view.update_status(f"Select corresponding point for Landmark #{landmark_id} on the left panel.")

    def _add_landmark_end(self, event):
        if not self._pending_landmark_id:
            self.view.update_status("Error: Select a point on the image panel first.")
            return

        landmark_id = self._pending_landmark_id
        x, y = event.x, event.y
        
        # This is a simplified mapping. A real implementation might need to map canvas coords back to data coords.
        # For this example, we store canvas coordinates for simplicity.
        self.model.landmarks_csv[landmark_id] = (x, y)
        
        self.view.draw_landmark(self.view.csv_canvas, x, y, landmark_id, color="green")
        self.view.update_landmark_lists(self.model.landmarks_csv, self.model.landmarks_image)
        self.view.update_status(f"Paired Landmark #{landmark_id}. Select a new point on the image panel.")
        self._pending_landmark_id = None
        self._update_calibrate_button_state()

    def _delete_landmark(self, event, canvas_type):
        canvas = self.view.image_canvas if canvas_type == 'image' else self.view.csv_canvas
        item = canvas.find_closest(event.x, event.y)
        tags = canvas.gettags(item)
        
        landmark_id = None
        for tag in tags:
            if tag.startswith("landmark_"):
                landmark_id = int(tag.split("_")[1])
                break
        
        if landmark_id:
            self.model.delete_landmark(landmark_id)
            self.view.clear_landmarks() # Simple redraw all
            for lid, (x,y) in self.model.landmarks_image.items():
                self.view.draw_landmark(self.view.image_canvas, x, y, lid)
            for lid, (x,y) in self.model.landmarks_csv.items():
                self.view.draw_landmark(self.view.csv_canvas, x, y, lid, color="green")

            self.view.update_landmark_lists(self.model.landmarks_csv, self.model.landmarks_image)
            self.view.update_status(f"Deleted Landmark #{landmark_id}.")
            self._update_calibrate_button_state()

    def _update_calibrate_button_state(self):
        num_pairs = len(self.model.landmarks_csv)
        if 4 <= num_pairs <= 12:
            self.view.calibrate_button.config(state="normal")
        else:
            self.view.calibrate_button.config(state="disabled")

    def run_calibration(self):
        image_points, csv_points = self.model.get_landmark_pairs()
        
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
        base_image = self.model.image.copy().convert("RGBA")
        overlay = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        image_points, csv_points = self.model.get_landmark_pairs()
        
        # Augment and transform csv points
        A = np.hstack([csv_points, np.ones((csv_points.shape[0], 1))])
        affine_matrix = np.array(self.model.calibration_results['affine_matrix'])[:2, :].T
        transformed_points = np.dot(A, affine_matrix)

        for i in range(len(image_points)):
            # Draw target image points (as red crosses)
            p_target = image_points[i]
            draw.line((p_target[0]-5, p_target[1], p_target[0]+5, p_target[1]), fill="red", width=2)
            draw.line((p_target[0], p_target[1]-5, p_target[0], p_target[1]+5), fill="red", width=2)

            # Draw transformed csv points (as blue circles)
            p_transformed = transformed_points[i]
            draw.ellipse((p_transformed[0]-3, p_transformed[1]-3, p_transformed[0]+3, p_transformed[1]+3), fill="blue", outline="blue")

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
        
        target_dim = self.view.canvas_size
        scale_x = target_dim / (x_max - x_min) if (x_max - x_min) > 0 else 1
        scale_y = target_dim / (y_max - y_min) if (y_max - y_min) > 0 else 1
        scale = min(scale_x, scale_y)

        scaled_data = (raw_data - [x_min, y_min]) * scale

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
        target_dim = self.view.canvas_size
        if width > 0 and height > 0:
            scale = min(target_dim / width, target_dim / height)
            new_size = (int(width * scale), int(height * scale))
            scaled_image = cropped_image.resize(new_size, Image.LANCZOS)
        else:
            scaled_image = cropped_image

        # Save Processed Image
        processed_image_path = os.path.join(self.model.experiment_path, "processed_image.png")
        scaled_image.save(processed_image_path)

        # Second Crop
        final_image_np = image.auto_crop(np.array(scaled_image), borders=50)
        final_image = Image.fromarray(final_image_np)

        return final_image
