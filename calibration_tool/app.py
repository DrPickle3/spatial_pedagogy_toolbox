# -*- coding: utf-8 -*-
"""
This module defines the main GUI for the calibration application.

It uses the tkinter library to create the application window, canvases, buttons,
and other widgets. In the Model-View-Controller (MVC) architecture, this is
the 'View'. Its primary role is to display data from the Model and capture
user input, which it then passes to the Controller.
"""
import tkinter as tk
from tkinter import ttk
from PIL import ImageTk


class ScrollableFrame(ttk.Frame):
    """
    A custom tkinter frame that includes a vertical scrollbar.

    This is a reusable component for creating areas with scrollable content.
    """

    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        # The canvas widget will contain the content and be controlled by the scrollbar.
        canvas = tk.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        # This is the actual frame where other widgets will be placed.
        self.scrollable_frame = ttk.Frame(canvas)

        # This binding is key: when the size of the inner frame changes,
        # it tells the canvas to update its scrollable region.
        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # Place the scrollable frame inside the canvas.
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Use the pack geometry manager to arrange the canvas and scrollbar.
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


class App(tk.Frame):
    """
    The main application class for the GUI.

    This class builds and manages all the visual components of the tool.

    Attributes:
        master: The root tkinter window.
        canvas_size (int): The width and height of the main display canvases.
        controller (Controller): The application's controller instance.
        last_status (str): The last message displayed in the status bar, used
                           for restoring the text after temporary messages.
    """

    def __init__(self, master, canvas_size=500):
        """
        Initializes the main application window.

        Args:
            master: The root tkinter window object.
            canvas_size (int, optional): The size (width and height) for the
                                         image and CSV canvases. Defaults to 500.
        """
        super().__init__(master)
        self.master = master
        self.canvas_size = canvas_size
        self.master.title("2D Affine Transformation Calibration Tool")
        self.pack(fill="both", expand=True)

        self.controller = None
        self.last_status = "Load a CSV file and an image to begin."

        # The setup is broken into logical parts for clarity.
        self._create_widgets()
        self._create_layout()
        self._bind_events()

    def _create_widgets(self):
        """Creates all the individual GUI widgets."""
        # --- Menu Bar ---
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        # The menu commands are linked to the controller's methods.
        file_menu.add_command(
            label="Load Image...", command=lambda: self.controller.load_image()
        )
        file_menu.add_command(
            label="Load CSV...", command=lambda: self.controller.load_csv()
        )
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)

        # --- Main Frames ---
        # These frames help organize the layout into logical sections.
        self.top_frame = ttk.Frame(self)
        self.middle_frame = ttk.Frame(self, height=150)
        # This prevents the frame from shrinking to fit its contents.
        self.middle_frame.pack_propagate(False)
        self.bottom_frame = ttk.Frame(self)

        # --- Canvases ---
        # These are the main areas for displaying the image and CSV data.
        self.image_canvas = tk.Canvas(
            self.top_frame,
            bg="lightgray",
            width=self.canvas_size,
            height=self.canvas_size,
        )
        self.csv_canvas = tk.Canvas(
            self.top_frame,
            bg="lightgray",
            width=self.canvas_size,
            height=self.canvas_size,
        )

        # --- Landmark Lists ---
        # We use our custom ScrollableFrame to ensure the landmark lists can scroll.
        img_scroll_container = ScrollableFrame(self.middle_frame)
        csv_scroll_container = ScrollableFrame(self.middle_frame)

        self.image_landmarks_frame = ttk.LabelFrame(
            img_scroll_container.scrollable_frame, text="Image Landmarks"
        )
        self.csv_landmarks_frame = ttk.LabelFrame(
            csv_scroll_container.scrollable_frame, text="CSV Landmarks"
        )

        # --- Bottom Controls ---
        self.undo_button = ttk.Button(
            self.bottom_frame,
            text="Undo Last Point",
            command=lambda: self.controller.undo_last_point(),
        )
        self.calibrate_button = ttk.Button(
            self.bottom_frame,
            text="Calibrate",
            state="disabled",  # Disabled by default until enough points are selected.
            command=lambda: self.controller.run_calibration(),
        )
        self.status_bar = ttk.Label(
            self, text="Load an image and a CSV file to begin.", anchor="w"
        )

    def _create_layout(self):
        """Arranges all the created widgets in the main window."""
        # Pack the main frames.
        self.top_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)
        self.middle_frame.pack(side="top", fill="x", expand=False, padx=10, pady=5)
        self.bottom_frame.pack(side="top", fill="x", expand=False, padx=10, pady=10)
        self.status_bar.pack(side="bottom", fill="x", expand=False, padx=10, pady=2)

        # Pack the canvases within the top frame.
        self.image_canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self.csv_canvas.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Pack the landmark list containers.
        self.image_landmarks_frame.pack(fill="both", expand=True)
        self.csv_landmarks_frame.pack(fill="both", expand=True)
        self.image_landmarks_frame.master.master.pack(
            side="left", fill="x", expand=True, padx=(0, 5)
        )
        self.csv_landmarks_frame.master.master.pack(
            side="right", fill="x", expand=True, padx=(5, 0)
        )

        # Pack the bottom buttons.
        self.undo_button.pack(side="left", padx=10, pady=5)
        self.calibrate_button.pack(side="right", padx=10, pady=5)

    def _bind_events(self):
        """Binds events that are internal to the View, like mouse motion."""
        # When the mouse moves over a canvas, show its coordinates in the status bar.
        self.image_canvas.bind(
            "<Motion>", lambda e: self._track_coords(e, "Image Panel")
        )
        self.csv_canvas.bind("<Motion>", lambda e: self._track_coords(e, "CSV Panel"))
        # When the mouse leaves a canvas, restore the last status message.
        self.image_canvas.bind("<Leave>", self._reset_status)
        self.csv_canvas.bind("<Leave>", self._reset_status)

    def update_status(self, text):
        """
        Updates the text in the status bar.

        Args:
            text (str): The new message to display.
        """
        self.status_bar.config(text=text)
        # We store the message so it can be restored after temporary messages.
        self.last_status = text

    def _track_coords(self, event, canvas_name):
        """Displays the current mouse coordinates on the status bar."""
        coord_text = f"{canvas_name} Coords: ({event.x}, {event.y})"
        self.status_bar.config(text=coord_text)

    def _reset_status(self, event):
        """Resets the status bar to its last persistent message."""
        self.status_bar.config(text=self.last_status)

    def display_image(self, img_tk):
        """
        Displays a processed image on the image canvas.

        Args:
            img_tk (ImageTk.PhotoImage): The image to display.
        """
        self.image_canvas.delete("all")
        # We draw the image with a 25px padding from the top-left corner.
        self.image_canvas.create_image(25, 25, anchor="nw", image=img_tk)
        # Draw a border around the image.
        self.image_canvas.create_rectangle(
            25, 25, 25 + img_tk.width(), 25 + img_tk.height(), outline="black"
        )
        # This is a tkinter quirk: we must keep a reference to the image
        # to prevent it from being garbage collected.
        self.image_canvas.image = img_tk

    def display_csv_as_image(self, img_tk):
        """
        Displays the CSV point visualization on the CSV canvas.

        Args:
            img_tk (ImageTk.PhotoImage): The image to display.
        """
        self.csv_canvas.delete("all")
        self.csv_canvas.create_image(25, 25, anchor="nw", image=img_tk)
        self.csv_canvas.create_rectangle(
            25, 25, 25 + img_tk.width(), 25 + img_tk.height(), outline="black"
        )
        self.csv_canvas.image = img_tk  # Keep a reference

    def draw_landmark(self, canvas, x, y, number, color="red"):
        """
        Draws a single landmark on a canvas.

        Args:
            canvas (tk.Canvas): The canvas to draw on.
            x (int): The x-coordinate.
            y (int): The y-coordinate.
            number (int): The landmark number to display.
            color (str, optional): The color of the landmark circle. Defaults to "red".
        """
        tag = f"landmark_{number}"
        # Draw the colored circle.
        canvas.create_oval(
            x - 5, y - 5, x + 5, y + 5, fill=color, outline="black", tags=(tag, "landmark")
        )
        # Draw the landmark number in the center of the circle.
        canvas.create_text(x, y, text=str(number), fill="white", tags=(tag, "landmark"))

    def update_landmark_lists(self, landmarks_csv, landmarks_image):
        """
        Updates the text lists of landmark coordinates in the middle panel.

        Args:
            landmarks_csv (list): A list of (x, y) tuples for the CSV landmarks.
            landmarks_image (list): A list of (x, y) tuples for the image landmarks.
        """
        # Clear the previous list content.
        for widget in self.csv_landmarks_frame.winfo_children():
            widget.destroy()
        for widget in self.image_landmarks_frame.winfo_children():
            widget.destroy()

        # Add a label for each landmark.
        for i, (x, y) in enumerate(landmarks_image):
            img_text = f"#{i+1}: ({x:.1f}, {y:.1f})"
            ttk.Label(self.image_landmarks_frame, text=img_text).pack(anchor="w")

        for i, (x, y) in enumerate(landmarks_csv):
            csv_text = f"#{i+1}: ({x:.1f}, {y:.1f})"
            ttk.Label(self.csv_landmarks_frame, text=csv_text).pack(anchor="w")

    def clear_landmarks(self):
        """Removes all landmark drawings from the canvases."""
        self.image_canvas.delete("landmark")
        self.csv_canvas.delete("landmark")
        self.update_landmark_lists([], [])

    def show_results_window(self, results, overlay_image):
        """
        Creates and displays the pop-up window with calibration results.

        Args:
            results (dict): The dictionary of results from the calibration.
            overlay_image (PIL.Image.Image): The visual overlay image to display.
        """
        results_window = tk.Toplevel(self.master)
        results_window.title("Calibration Results")

        # --- Display the Overlay Image ---
        img_tk = ImageTk.PhotoImage(overlay_image)
        canvas = tk.Canvas(results_window, width=img_tk.width(), height=img_tk.height())
        canvas.create_image(0, 0, anchor="nw", image=img_tk)
        canvas.image = img_tk  # Keep a reference
        canvas.pack(pady=10, padx=10)

        # --- Display Statistics ---
        stats_frame = ttk.LabelFrame(results_window, text="Statistics")
        stats_frame.pack(pady=10, padx=10, fill="x")

        # Format the affine matrix for display.
        matrix_str = (
            "Aff-Matrix:\n"
            + f"[{results['affine_matrix'][0][0]:.4f}, {results['affine_matrix'][0][1]:.4f}, {results['affine_matrix'][0][2]:.4f}]\n"
            + f"[{results['affine_matrix'][1][0]:.4f}, {results['affine_matrix'][1][1]:.4f}, {results['affine_matrix'][1][2]:.4f}]\n"
            + f"[{results['affine_matrix'][2][0]:.4f}, {results['affine_matrix'][2][1]:.4f}, {results['affine_matrix'][2][2]:.4f}]"
        )

        # Use a fixed-width font for the matrix to ensure alignment.
        ttk.Label(stats_frame, text=matrix_str, font="TkFixedFont").grid(
            row=0, column=0, sticky="w", rowspan=4
        )

        # Display the error metrics.
        ttk.Label(stats_frame, text=f"Min Error: {results['min_error']:.4f}").grid(
            row=0, column=1, sticky="w", padx=20
        )
        ttk.Label(stats_frame, text=f"Max Error: {results['max_error']:.4f}").grid(
            row=1, column=1, sticky="w", padx=20
        )
        ttk.Label(stats_frame, text=f"Mean Error: {results['mean_error']:.4f}").grid(
            row=2, column=1, sticky="w", padx=20
        )
        ttk.Label(stats_frame, text=f"Std Error: {results['std_error']:.4f}").grid(
            row=3, column=1, sticky="w", padx=20
        )
        ttk.Label(
            stats_frame, text=f"Computation Time: {results['computation_time']:.4f}s"
        ).grid(row=4, column=1, sticky="w", padx=20)

        # --- Save Button ---
        save_button = ttk.Button(
            results_window,
            text="Save Results",
            # Link the button to the controller's save method.
            command=lambda: self.controller.save_results(),
        )
        save_button.pack(pady=10)
