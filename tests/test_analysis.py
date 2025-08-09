import numpy as np
import pytest
from calibration_tool.analysis import calculate_affine_transform


def test_calculate_affine_transform_success():
    # A simple transformation: scale by 2 and translate by (10, 20)
    image_points = np.array([[10, 10], [20, 10], [10, 20]])
    csv_points = np.array([[30, 40], [50, 40], [30, 60]])  # (p*2 + [10, 20])

    results = calculate_affine_transform(image_points, csv_points)

    expected_matrix = np.array([
        [2.0, 0.0, 10.0],
        [0.0, 2.0, 20.0],
        [0.0, 0.0, 1.0]
    ])
    
    assert results is not None
    np.testing.assert_allclose(results['affine_matrix'], expected_matrix, atol=1e-6)
    assert results["mean_error"] < 1e-6


def test_calculate_affine_transform_insufficient_points():
    image_points = np.array([[10, 10], [20, 10]])
    csv_points = np.array([[30, 40], [50, 40]])

    with pytest.raises(ValueError, match="At least 3 landmark pairs are required"):
        calculate_affine_transform(image_points, csv_points)
