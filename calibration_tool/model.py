# -*- coding: utf-8 -*-
"""
This module defines the data model for the calibration application.

The CalibrationModel class acts as a central repository for all the application's
state. Following the Model-View-Controller (MVC) design pattern, the Model is
responsible for holding the data and has no direct interaction with the user
interface (the View). The Controller modifies the model and tells the View
when to update.
"""
import numpy as np


class CalibrationModel:
    """
    Holds the runtime state and data of the calibration application.

    This class stores everything the application needs to remember, such as file
    paths, loaded images, user-selected landmarks, and the final calibration
    results. It provides methods to safely modify this state.

    Attributes:
        csv_path (str): The absolute path to the loaded CSV file.
        image_path (str): The absolute path to the loaded image file.
        image (PIL.Image.Image): The processed image, ready for display.
        image_tk (ImageTk.PhotoImage): The tkinter-compatible version of the image.
        landmarks_csv (list): A list of (x, y) tuples for landmarks on the CSV canvas.
        landmarks_image (list): A list of (x, y) tuples for landmarks on the image canvas.
        action_history (list): A log of the type of landmarks added ('image' or 'csv')
                               to support the undo functionality.
        scaled_csv_data (np.ndarray): The preprocessed and scaled CSV coordinates.
        calibration_results (dict): A dictionary to store the results from the
                                    affine transformation calculation.
        experiment_path (str): The path to the dedicated folder for the current session.
    """

    def __init__(self):
        """Initializes the model with default empty values."""
        self.csv_path = None
        self.image_path = None
        self.image = None
        self.image_tk = None
        self.landmarks_csv = []
        self.landmarks_image = []
        self.action_history = []
        self.scaled_csv_data = None
        self.calibration_results = {}
        self.experiment_path = None

    def clear_landmarks(self):
        """Resets all landmark data and the action history."""
        self.landmarks_csv = []
        self.landmarks_image = []
        self.action_history = []

    def add_image_landmark(self, point):
        """
        Adds a landmark for the image canvas.

        Args:
            point (tuple): The (x, y) coordinate of the landmark.

        Returns:
            bool: True if the landmark was added, False if the maximum number
                  of landmarks (12) was already reached.
        """
        # We limit the number of landmarks to 12 to keep the UI clean.
        if len(self.landmarks_image) < 12:
            self.landmarks_image.append(point)
            # Record this action so we can undo it if requested.
            self.action_history.append("image")
            return True
        return False

    def add_csv_landmark(self, point):
        """
        Adds a landmark for the CSV canvas.

        Args:
            point (tuple): The (x, y) coordinate of the landmark.

        Returns:
            bool: True if the landmark was added, False if the maximum number
                  of landmarks (12) was already reached.
        """
        if len(self.landmarks_csv) < 12:
            self.landmarks_csv.append(point)
            # Record this action for the undo history.
            self.action_history.append("csv")
            return True
        return False

    def undo_last_landmark(self):
        """
        Removes the most recently added landmark.

        It checks the action history to see whether the last point was added to
        the image or the CSV canvas and removes it from the corresponding list.
        """
        # Do nothing if there's no history to undo.
        if not self.action_history:
            return

        # Get the last action performed.
        last_action = self.action_history.pop()
        # Remove the last point from the appropriate list.
        if last_action == "image" and self.landmarks_image:
            self.landmarks_image.pop()
        elif last_action == "csv" and self.landmarks_csv:
            self.landmarks_csv.pop()

    def get_landmark_pairs(self):
        """
        Returns the landmark points as paired NumPy arrays.

        This function is crucial for calibration. It ensures that for every image
        landmark, there is a corresponding CSV landmark. It will only return
        as many pairs as are complete.

        For example, if there are 4 image points and 3 CSV points, this will
        return 3 pairs of points.

        Returns:
            tuple: A tuple containing two NumPy arrays:
                - The first array contains the image landmark coordinates.
                - The second array contains the corresponding CSV landmark coordinates.
        """
        # The number of complete pairs is the minimum of the two list lengths.
        num_pairs = min(len(self.landmarks_image), len(self.landmarks_csv))
        # Convert the lists of tuples to NumPy arrays for numerical computation.
        image_points = np.array(self.landmarks_image[:num_pairs])
        csv_points = np.array(self.landmarks_csv[:num_pairs])
        return image_points, csv_points
