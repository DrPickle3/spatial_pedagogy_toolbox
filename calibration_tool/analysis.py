# -*- coding: utf-8 -*-
"""
This module contains the core mathematical logic for the calibration tool.

Its primary function is to calculate the affine transformation, which is a
geometric transformation that preserves lines and parallelism but not necessarily
distances and angles. This is the key to mapping the CSV coordinates to the
image coordinates.
"""
import numpy as np
import time


def calculate_affine_transform(image_points, csv_points):
    """
    Calculates the 3x3 affine transformation matrix from image points to CSV points.

    This function solves a system of linear equations to find the best-fit
    transformation matrix that maps one set of points to another. An affine
    transformation can represent scaling, rotation, shearing, and translation.

    The transformation is represented by a 2x3 matrix, but we return a 3x3
    matrix for ease of use in homogeneous coordinates, which is a common
    practice in computer graphics.

    Args:
        image_points (np.ndarray): A NumPy array of shape (N, 2), where N is the
            number of landmark points. Each row is an (x, y) coordinate
            selected from the image.
        csv_points (np.ndarray): A NumPy array of shape (N, 2) with the
            corresponding (x, y) coordinates from the CSV data visualization.

    Returns:
        dict: A dictionary containing the results of the calibration.
            - 'affine_matrix' (np.ndarray): The calculated 3x3 affine transformation matrix.
            - 'errors' (list): A list of Euclidean distances (errors) for each landmark pair.
            - 'min_error' (float): The smallest error among the pairs.
            - 'max_error' (float): The largest error among the pairs.
            - 'mean_error' (float): The average error across all pairs.
            - 'std_error' (float): The standard deviation of the errors.
            - 'computation_time' (float): The time in seconds it took to perform the calculation.

    Raises:
        ValueError: If fewer than 3 landmark pairs are provided, as an affine
                    transformation cannot be uniquely determined.
    """
    # An affine transformation in 2D is defined by 6 parameters. Each point
    # pair provides two linear equations (one for x, one for y). Therefore, we
    # need at least 3 pairs of points (3*2=6 equations) to solve for the 6 unknowns.
    if len(image_points) < 3:
        raise ValueError(
            "At least 3 landmark pairs are required for affine transformation."
        )

    # Start a high-resolution timer to measure how long the calculation takes.
    start_time = time.perf_counter()

    # To solve for the affine matrix, we use a linear least-squares method.
    # The equation is of the form Ax = b, where x is the matrix of transformation
    # coefficients we want to find.
    # To set this up, we need to augment our coordinate matrices with a column of ones.
    # This is because an affine transformation includes translation (a constant offset),
    # and this extra dimension allows us to represent translation within the matrix multiplication.
    pad = lambda x: np.hstack([x, np.ones((x.shape[0], 1))])
    A = pad(image_points)  # This becomes the matrix of source points.
    b = pad(csv_points)  # This becomes the matrix of destination points.

    # This is the core of the function. np.linalg.lstsq finds the matrix 'x'
    # that minimizes the Euclidean 2-norm ||b - Ax||^2. This is the "best fit"
    # solution for the transformation.
    # 'x' will be a 3x3 matrix containing the transformation parameters.
    # 'res', 'rank', and 's' are other results from the computation that we don't use here.
    x, res, rank, s = np.linalg.lstsq(A, b, rcond=None)

    # The result 'x' needs to be transposed to get the conventional affine matrix layout.
    affine_matrix = x.T

    # For standard computer graphics applications, a 2x3 matrix is used.
    # However, for applying transformations using homogeneous coordinates, a 3x3
    # matrix is more convenient. We create this by stacking the [0, 0, 1] row.
    affine_matrix_3x3 = np.vstack([affine_matrix[:2, :], [0, 0, 1]])

    # To evaluate the accuracy of our transformation, we apply the calculated
    # matrix 'x' back to our original image points.
    # The result should be very close to our original csv_points.
    transformed_points = np.dot(A, x)[:, 0:2]

    # Now, we calculate the error for each point pair. The error is the
    # Euclidean distance between the point transformed by our matrix and the
    # actual target point.
    errors = np.linalg.norm(transformed_points - csv_points, axis=1)
    min_error = np.min(errors)
    max_error = np.max(errors)
    mean_error = np.mean(errors)
    std_error = np.std(errors)

    # Stop the timer.
    computation_time = time.perf_counter() - start_time

    # Return all the results in a structured dictionary.
    return {
        "affine_matrix": affine_matrix_3x3,
        "errors": errors.tolist(),
        "min_error": min_error,
        "max_error": max_error,
        "mean_error": mean_error,
        "std_error": std_error,
        "computation_time": computation_time,
    }
