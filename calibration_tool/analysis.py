import numpy as np
import time


def calculate_affine_transform(image_points, csv_points):
    """
    Calculates the 2x3 affine transformation matrix from image points to csv points.

    Args:
        image_points (np.ndarray): A (N, 2) array of coordinates from the image.
        csv_points (np.ndarray): A (N, 2) array of corresponding coordinates from the CSV.

    Returns:
        dict: A dictionary containing the transformation matrix, error metrics,
              and computation time.
    """
    if len(image_points) < 3:
        raise ValueError(
            "At least 3 landmark pairs are required for affine transformation."
        )

    start_time = time.perf_counter()

    # Augment coordinates for least squares
    pad = lambda x: np.hstack([x, np.ones((x.shape[0], 1))])
    A = pad(image_points)
    b = pad(csv_points)

    # Solve for the transformation matrix
    x, res, rank, s = np.linalg.lstsq(A, b, rcond=None)
    affine_matrix = x.T

    # Reshape to a 3x3 matrix for easier transformations
    affine_matrix_3x3 = np.vstack([affine_matrix[:2, :], [0, 0, 1]])

    # Apply the transformation to the image points
    transformed_points = np.dot(A, x)[:, 0:2]

    # Calculate errors
    errors = np.linalg.norm(transformed_points - csv_points, axis=1)
    min_error = np.min(errors)
    max_error = np.max(errors)
    mean_error = np.mean(errors)
    std_error = np.std(errors)

    computation_time = time.perf_counter() - start_time

    return {
        "affine_matrix": affine_matrix_3x3,
        "errors": errors.tolist(),
        "min_error": min_error,
        "max_error": max_error,
        "mean_error": mean_error,
        "std_error": std_error,
        "computation_time": computation_time,
    }
