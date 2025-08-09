import pytest
import numpy as np
from calibration_tool.model import CalibrationModel


@pytest.fixture
def model():
    return CalibrationModel()


def test_initial_state(model):
    assert model.landmarks_csv == []
    assert model.landmarks_image == []
    assert model.action_history == []


def test_add_landmarks(model):
    model.add_image_landmark((10, 20))
    model.add_csv_landmark((30, 40))
    assert model.landmarks_image == [(10, 20)]
    assert model.landmarks_csv == [(30, 40)]
    assert model.action_history == ["image", "csv"]


def test_undo_last_landmark(model):
    model.add_image_landmark((10, 20))
    model.add_csv_landmark((30, 40))
    model.undo_last_landmark()
    assert model.landmarks_csv == []
    assert model.landmarks_image == [(10, 20)]
    assert model.action_history == ["image"]
    model.undo_last_landmark()
    assert model.landmarks_image == []
    assert model.action_history == []


def test_clear_landmarks(model):
    model.add_image_landmark((10, 20))
    model.add_csv_landmark((30, 40))
    model.clear_landmarks()
    assert model.landmarks_csv == []
    assert model.landmarks_image == []
    assert model.action_history == []


def test_get_landmark_pairs(model):
    model.add_image_landmark((1, 1))
    model.add_csv_landmark((10, 10))
    model.add_image_landmark((2, 2))
    model.add_csv_landmark((20, 20))
    model.add_image_landmark((3, 3))  # Unpaired

    img_pts, csv_pts = model.get_landmark_pairs()

    assert img_pts.shape == (2, 2)
    assert csv_pts.shape == (2, 2)
    np.testing.assert_array_equal(img_pts, np.array([[1, 1], [2, 2]]))
    np.testing.assert_array_equal(csv_pts, np.array([[10, 10], [20, 20]]))
