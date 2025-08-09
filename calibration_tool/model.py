import numpy as np

class CalibrationModel:
    """
    Holds the state of the calibration application.
    """
    def __init__(self):
        self.csv_path = None
        self.image_path = None
        self.csv_data = None
        self.image = None
        self.image_tk = None
        self.landmarks_csv = {}
        self.landmarks_image = {}
        self.calibration_results = {}
        self.experiment_path = None

    def load_csv_data(self, file_path):
        """Loads CSV data from a file path."""
        self.csv_path = file_path
        self.csv_data = np.loadtxt(file_path, delimiter=',')
        # Reset landmarks when new data is loaded
        self.landmarks_csv = {}

    def get_csv_coords(self):
        """Returns the CSV data as a NumPy array."""
        return self.csv_data

    def add_landmark(self, landmark_id, csv_coord, image_coord):
        """Adds a landmark pair."""
        self.landmarks_csv[landmark_id] = csv_coord
        self.landmarks_image[landmark_id] = image_coord

    def delete_landmark(self, landmark_id):
        """Deletes a landmark pair."""
        if landmark_id in self.landmarks_csv:
            del self.landmarks_csv[landmark_id]
        if landmark_id in self.landmarks_image:
            del self.landmarks_image[landmark_id]

    def get_landmark_pairs(self):
        """Returns the landmark pairs as two lists of coordinates."""
        sorted_keys = sorted(self.landmarks_image.keys())
        image_points = np.array([self.landmarks_image[key] for key in sorted_keys])
        csv_points = np.array([self.landmarks_csv[key] for key in sorted_keys])
        return image_points, csv_points
