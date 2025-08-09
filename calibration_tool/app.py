import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont


class App(tk.Frame):
    """The main GUI for the calibration tool."""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.master.title("2D Affine Transformation Calibration Tool")
        self.pack(fill="both", expand=True)

        self.controller = None
        self.last_status = "Load a CSV file and an image to begin."

        self._create_widgets()
        self._create_layout()
        self._bind_events()

    def _bind_events(self):
        # Bind motion events for coordinate tracking
        self.csv_canvas.bind("<Motion>", lambda e: self._track_coords(e, "Left Panel"))
        self.image_canvas.bind("<Motion>", lambda e: self._track_coords(e, "Right Panel"))
        self.csv_canvas.bind("<Leave>", self._reset_status)
        self.image_canvas.bind("<Leave>", self._reset_status)

    def _create_widgets(self):
        # Menu
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load CSV...", command=lambda: self.controller.load_csv())
        file_menu.add_command(label="Load Image...", command=lambda: self.controller.load_image())
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)

        # Main frames
        self.top_frame = ttk.Frame(self)
        self.middle_frame = ttk.Frame(self)
        self.bottom_frame = ttk.Frame(self)

        # Canvases
        self.csv_canvas = tk.Canvas(self.top_frame, bg="white", width=500, height=500)
        self.image_canvas = tk.Canvas(self.top_frame, bg="lightgray", width=500, height=500)

        # Landmark list frames
        self.csv_landmarks_frame = ttk.LabelFrame(self.middle_frame, text="CSV Landmarks")
        self.image_landmarks_frame = ttk.LabelFrame(self.middle_frame, text="Image Landmarks")

        # Bottom controls
        self.calibrate_button = ttk.Button(self.bottom_frame, text="Calibrate", state="disabled",
                                           command=lambda: self.controller.run_calibration())
        self.status_bar = ttk.Label(self, text="Load a CSV file and an image to begin.", anchor="w")

    def _create_layout(self):
        self.top_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)
        self.middle_frame.pack(side="top", fill="x", expand=False, padx=10, pady=5)
        self.bottom_frame.pack(side="top", fill="x", expand=False, padx=10, pady=10)
        self.status_bar.pack(side="bottom", fill="x", expand=False, padx=10, pady=2)

        self.csv_canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.image_canvas.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self.csv_landmarks_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.image_landmarks_frame.pack(side="right", fill="x", expand=True, padx=(5, 0))

        self.calibrate_button.pack(pady=5)

    def update_status(self, text):
        self.status_bar.config(text=text)
        self.last_status = text

    def _track_coords(self, event, canvas_name):
        coord_text = f"{canvas_name} Coords: ({event.x}, {event.y})"
        self.status_bar.config(text=coord_text)

    def _reset_status(self, event):
        self.status_bar.config(text=self.last_status)

    def display_image(self, img_tk):
        self.image_canvas.delete("all")
        self.image_canvas.create_image(0, 0, anchor="nw", image=img_tk)
        self.image_canvas.image = img_tk  # Keep a reference

    def display_left_image(self, img_tk):
        self.csv_canvas.delete("all")
        self.csv_canvas.create_image(0, 0, anchor="nw", image=img_tk)
        self.csv_canvas.image = img_tk  # Keep a reference

    def draw_landmark(self, canvas, x, y, number, color="red"):
        tag = f"landmark_{number}"
        canvas.create_oval(x-5, y-5, x+5, y+5, fill=color, outline="black", tags=(tag, "landmark"))
        canvas.create_text(x, y, text=str(number), fill="white", tags=(tag, "landmark"))
        return tag

    def update_landmark_lists(self, landmarks_csv, landmarks_image):
        for widget in self.csv_landmarks_frame.winfo_children():
            widget.destroy()
        for widget in self.image_landmarks_frame.winfo_children():
            widget.destroy()

        sorted_keys = sorted(landmarks_image.keys())

        for key in sorted_keys:
            # Add to image list
            img_coord = landmarks_image[key]
            img_text = f"#{key}: ({img_coord[0]:.1f}, {img_coord[1]:.1f})"
            ttk.Label(self.image_landmarks_frame, text=img_text).pack(anchor="w")

            # Add to csv list
            if key in landmarks_csv:
                csv_coord = landmarks_csv[key]
                csv_text = f"#{key}: ({csv_coord[0]:.1f}, {csv_coord[1]:.1f})"
                ttk.Label(self.csv_landmarks_frame, text=csv_text).pack(anchor="w")

    def clear_landmarks(self):
        self.csv_canvas.delete("landmark")
        self.image_canvas.delete("landmark")
        self.update_landmark_lists({}, {})

    def show_results_window(self, results, overlay_image):
        results_window = tk.Toplevel(self.master)
        results_window.title("Calibration Results")

        # Overlay Image
        img_tk = ImageTk.PhotoImage(overlay_image)
        canvas = tk.Canvas(results_window, width=img_tk.width(), height=img_tk.height())
        canvas.create_image(0, 0, anchor="nw", image=img_tk)
        canvas.image = img_tk # Keep a reference
        canvas.pack(pady=10, padx=10)

        # Stats
        stats_frame = ttk.LabelFrame(results_window, text="Statistics")
        stats_frame.pack(pady=10, padx=10, fill="x")

        matrix_str = "Aff-Matrix:\n" + \
            f"[{results['affine_matrix'][0][0]:.4f}, {results['affine_matrix'][0][1]:.4f}, {results['affine_matrix'][0][2]:.4f}]\n" + \
            f"[{results['affine_matrix'][1][0]:.4f}, {results['affine_matrix'][1][1]:.4f}, {results['affine_matrix'][1][2]:.4f}]\n" + \
            f"[{results['affine_matrix'][2][0]:.4f}, {results['affine_matrix'][2][1]:.4f}, {results['affine_matrix'][2][2]:.4f}]"
        
        ttk.Label(stats_frame, text=matrix_str, font="TkFixedFont").grid(row=0, column=0, sticky="w", rowspan=4)

        ttk.Label(stats_frame, text=f"Min Error: {results['min_error']:.4f}").grid(row=0, column=1, sticky="w", padx=20)
        ttk.Label(stats_frame, text=f"Max Error: {results['max_error']:.4f}").grid(row=1, column=1, sticky="w", padx=20)
        ttk.Label(stats_frame, text=f"Mean Error: {results['mean_error']:.4f}").grid(row=2, column=1, sticky="w", padx=20)
        ttk.Label(stats_frame, text=f"Std Error: {results['std_error']:.4f}").grid(row=3, column=1, sticky="w", padx=20)
        ttk.Label(stats_frame, text=f"Computation Time: {results['computation_time']:.4f}s").grid(row=4, column=1, sticky="w", padx=20)

        # Save button
        save_button = ttk.Button(results_window, text="Save Results",
                                 command=lambda: self.controller.save_results())
        save_button.pack(pady=10)
