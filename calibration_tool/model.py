import numpy as np

class CalibrationModel:
    """
    Holds the state of the calibration application.
    """
    def __init__(self):
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
        self.landmarks_csv = []
        self.landmarks_image = []
        self.action_history = []
        self.scaled_csv_data = None

    def add_image_landmark(self, point):
        if len(self.landmarks_image) < 12:
            self.landmarks_image.append(point)
            self.action_history.append('image')
            return True
        return False

    def add_csv_landmark(self, point):
        if len(self.landmarks_csv) < 12:
            self.landmarks_csv.append(point)
            self.action_history.append('csv')
            return True
        return False

    def undo_last_landmark(self):
        if not self.action_history:
            return

        last_action = self.action_history.pop()
        if last_action == 'image' and self.landmarks_image:
            self.landmarks_image.pop()
        elif last_action == 'csv' and self.landmarks_csv:
            self.landmarks_csv.pop()

    def get_landmark_pairs(self):
        """Returns the landmark pairs as two lists of coordinates."""
        num_pairs = min(len(self.landmarks_image), len(self.landmarks_csv))
        image_points = np.array(self.landmarks_image[:num_pairs])
        csv_points = np.array(self.landmarks_csv[:num_pairs])
        return image_points, csv_points

