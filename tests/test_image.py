import numpy as np
import pytest
from PIL import Image
from calibration_tool.image import auto_crop, remove_background, pad_image_to_center


@pytest.fixture
def sample_image_array():
    # Create a 100x100 image with a white background (255)
    # and a 20x30 black rectangle (0) inside.
    img = np.full((100, 100, 3), 255, dtype=np.uint8)
    img[40:60, 35:65] = [10, 20, 30]  # The object
    return img


def test_auto_crop_no_border(sample_image_array):
    cropped_img = auto_crop(sample_image_array, borders=0)
    # Should crop to the 20x30 rectangle
    assert cropped_img.shape == (20, 30, 3)
    # Check if the content is the rectangle's color
    np.testing.assert_array_equal(cropped_img[0, 0], [10, 20, 30])


def test_auto_crop_with_border(sample_image_array):
    cropped_img = auto_crop(sample_image_array, borders=10)
    # Should be 20x30 rectangle + 10px border
    assert cropped_img.shape == (30, 40, 3)


def test_remove_background(sample_image_array):
    # The background is at (0,0) with value 255
    img_rgba, mask = remove_background(
        sample_image_array, init_pos=(0, 0), threshold=10
    )
    assert img_rgba.shape == (100, 100, 4)  # Should have an alpha channel
    # Mask should be 0 (transparent) for the background
    assert mask[0, 0] == 0
    # Mask should be 255 (opaque) for the foreground object
    assert mask[50, 50] == 255


def test_pad_image_to_center():
    small_img = np.full((10, 20, 3), 50, dtype=np.uint8)
    padded_img = pad_image_to_center(
        small_img, (40, 30)
    )  # new_shape is (height, width)

    # Pillow uses (width, height), numpy uses (height, width)
    assert padded_img.shape == (40, 30, 3)

    # Check that the original image is centered
    # y_center = (40-10)//2 = 15, x_center = (30-20)//2 = 5
    assert padded_img[15, 5, 0] == 50
    assert padded_img[15 + 9, 5 + 19, 0] == 50
    # Check a background pixel
    assert padded_img[0, 0, 0] != 50
