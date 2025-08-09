# -*- coding: utf-8 -*-
"""
This module provides a collection of utility functions for image manipulation.

These functions are essential for the preprocessing pipeline of the calibration
tool. They handle tasks such as removing backgrounds, cropping images to the
content, resizing, and padding. The goal is to standardize the input images
to ensure consistent and reliable calibration results.
"""
import numpy as np
from PIL import Image
from skimage.segmentation import flood_fill


def remove_background(img, threshold=10, init_pos=(0, 0), mode="fill"):
    """
    Removes the background of an image based on a sample color.

    This function identifies the background by looking at the color of a single
    pixel (usually a corner pixel) and then makes this color transparent.

    Args:
        img (np.ndarray): The input image as a NumPy array.
        threshold (int, optional): A tolerance value. Pixels with colors that
            are "close" to the background color (within this threshold) will
            also be removed. Defaults to 10.
        init_pos (tuple, optional): The (row, column) coordinate of the pixel
            to sample for the background color. Defaults to (0, 0), the top-left corner.
        mode (str, optional): The method to use for background removal.
            'fill' uses a flood-fill algorithm, which is good for contiguous
            backgrounds. 'value' removes all pixels close to the background
            color, regardless of location. Defaults to 'fill'.

    Returns:
        tuple: A tuple containing:
            - np.ndarray: The new image with a transparent background (RGBA format).
            - np.ndarray: The black and white mask used, where white is the
                          foreground and black is the background.
    """
    # Ensure the image is in a floating-point format for calculations.
    img = img.astype(np.float32)
    # If the image already has an alpha channel, remove it for processing.
    if img.shape[-1] == 4:
        img = img[:, :, 0:3]

    # Get the color value of the background pixel.
    value = img[init_pos]
    # Calculate the Euclidean distance of every pixel's color from the background color.
    # This creates a grayscale image where darker pixels are more similar to the background.
    norm = np.linalg.norm(np.abs(img - value), axis=-1)

    if mode == "fill":
        # The 'footprint' defines the connectivity for the flood fill.
        # This structure connects pixels horizontally and vertically.
        binary_struct = np.zeros((3, 3))
        binary_struct[0:3, 1] = 1
        binary_struct[1, 0:3] = 1

        # Perform the flood fill. It starts at init_pos and fills all pixels
        # within the 'tolerance' with the value 999.
        mask = flood_fill(
            norm, init_pos, 999, footprint=binary_struct, tolerance=threshold
        )
        # Create the final mask: where the fill happened (999), make it transparent (0).
        # Everywhere else becomes opaque (255).
        mask = np.where(mask == 999, 0, 255)
    else:
        # A simpler method: any pixel with a color distance less than the
        # threshold is considered background (transparent).
        mask = np.where(norm < threshold, 0, 255)

    # Create a new 4-channel (RGBA) image.
    new_img = np.zeros(img.shape[0:2] + (4,)).astype(np.uint8)
    # Copy the original RGB data.
    new_img[:, :, 0:3] = img
    # Apply the generated mask to the alpha channel.
    new_img[:, :, 3] = mask

    return new_img, mask.astype(np.uint8)


def auto_crop(img, borders=0):
    """
    Crops an image to the bounding box of the main content.

    This function automatically finds the object in the image (assuming it's on
    a uniform background) and crops the image to fit this object, optionally
    adding a border.

    Args:
        img (np.ndarray): The input image as a NumPy array.
        borders (int, optional): The number of pixels to add as a border
            around the cropped content. Defaults to 0.

    Returns:
        np.ndarray: The cropped image.
    """
    # This function first adds a temporary border to ensure the background
    # removal works correctly, especially if the object touches the edges.
    value = img[0, 0]
    new_shape = (img.shape[0] + borders, img.shape[1] + borders, img.shape[2])
    new_img = np.ones(new_shape, dtype=np.uint8) * value

    # Place the original image in the center of this new, larger image.
    new_img[
        borders // 2 : borders // 2 + img.shape[0],
        borders // 2 : borders // 2 + img.shape[1],
        :,
    ] = img
    # Generate the foreground mask.
    _, mask = remove_background(new_img)

    # Find all non-background (opaque) pixels in the mask.
    x, y = np.where(mask == 255)
    # Determine the minimum and maximum coordinates to find the bounding box.
    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)
    # Crop the image to this bounding box.
    cropped = new_img[
        x_min - borders // 2 : x_max + borders // 2 + 1,
        y_min - borders // 2 : y_max + borders // 2 + 1,
        :,
    ]

    return cropped


def resize(img, ratio_frac=None, ratio_val=None, dimensions=None, scale=None):
    """
    Resizes an image using various methods.

    This is a flexible wrapper around the Pillow library's resize function.

    Args:
        img (np.ndarray): The input image as a NumPy array.
        ratio_frac (float, optional): A fractional aspect ratio (height/width).
        ratio_val (tuple, optional): A tuple-based ratio (height, width).
        dimensions (tuple, optional): The target (width, height) in pixels.
        scale (float, optional): A scaling factor to apply to the image.

    Returns:
        PIL.Image.Image: The resized image as a Pillow Image object.
    """
    if ratio_val is not None:
        if len(ratio_val) != 2:
            raise ValueError("Ratio must be a 2-tuple")
        if ratio_val[1] == 0:
            raise ValueError("Ratio must be non-zero")
    # Calculate the fractional ratio if a tuple was provided.
    ratio_frac = ratio_val[1] / ratio_val[0] if ratio_val is not None else ratio_frac
    # Calculate the target dimensions if a scale factor was provided.
    if scale is not None:
        dimensions = (img.shape[1] * scale, img.shape[0] * scale)

    if dimensions is not None:
        dim_1, dim_2 = dimensions
    elif ratio_frac is not None:
        dim_1 = img.shape[0]
        dim_2 = img.shape[0] * ratio_frac
    else:
        raise ValueError("At least one of the options must be specified!")

    # Use Pillow to perform the resize operation.
    return Image.fromarray(img).resize((int(dim_1), int(dim_2)))


def generate_mosaic(
    imgs,
    rows,
    columns,
    auto_bbox=True,
    auto_border=True,
    scaling_method="resize_to_avg",
):
    """
    Generates a mosaic from a list of images. (Not used in the current app)

    This function arranges a list of images into a grid. It can automatically
    crop and resize them to create a uniform mosaic.

    Args:
        imgs (list): A list of images as NumPy arrays.
        rows (int): The number of rows in the mosaic grid.
        columns (int): The number of columns in the mosaic grid.
        auto_bbox (bool, optional): Whether to auto-crop each image. Defaults to True.
        auto_border (bool, optional): Whether to add a border to each image. Defaults to True.
        scaling_method (str, optional): How to make the images fit together.
            'resize_to_avg': Resize all to the average size.
            'resize_to_max': Resize all to the max size.
            'pad_to_max': Pad all to the max size.
            Defaults to "resize_to_avg".

    Returns:
        np.ndarray: The final mosaic image.
    """
    sizes = np.zeros((len(imgs), 2))
    for i, img in enumerate(imgs):
        if auto_bbox:
            imgs[i] = auto_crop(img)
        if auto_border:
            border = (img.shape[0] + img.shape[1]) // 20
            imgs[i] = auto_crop(img, borders=border)
        sizes[i] = imgs[i].shape[0:2]

    # Compute the final size of each cell in the mosaic.
    ratio = sizes[:, 0] / sizes[:, 1]
    if scaling_method == "resize_to_avg":
        final_size = np.mean(sizes, axis=0, dtype=np.uint16)
    elif scaling_method == "resize_to_max" or scaling_method == "pad_to_max":
        final_size = np.max(sizes, axis=0).astype(np.uint16)
    avg_ratio = final_size[0] / final_size[1]
    for i, img in enumerate(imgs):
        # Preserve aspect ratio while fitting to the target cell size.
        if ratio[i] > avg_ratio:
            dim_1 = final_size[0]
            dim_2 = dim_1 / ratio[i]
        else:
            dim_2 = final_size[1]
            dim_1 = dim_2 * ratio[i]

        if scaling_method == "resize_to_avg" or scaling_method == "resize_to_max":
            imgs[i] = np.asarray(resize(img, dimensions=(dim_2, dim_1)))
        # Pad the image to make sure it's exactly the final_size.
        imgs[i] = pad_image_to_center(imgs[i], final_size)

    # Create the blank canvas for the mosaic.
    mosaic = np.zeros((int(final_size[0] * rows), int(final_size[1] * columns), 3))

    # Place each processed image into its correct cell in the mosaic.
    for i, img in enumerate(imgs):
        if rows <= columns:
            row = i % columns
            col = i // columns
        else:
            row = i // rows
            col = i % rows
        mosaic[
            col * final_size[0] : (col + 1) * final_size[0],
            row * final_size[1] : (row + 1) * final_size[1],
            :,
        ] = img[:, :, 0:3]

    return mosaic.astype(np.uint8)


def pad_image_to_center(img, new_shape):
    """
    Pads an image with a solid color to fit a new, larger shape.

    This is useful for ensuring all images have the same dimensions before
    displaying them, without distorting their aspect ratio.

    Args:
        img (np.ndarray): The input image as a NumPy array.
        new_shape (tuple): The target (height, width) of the output image.

    Returns:
        np.ndarray: The padded image.
    """
    old_image_height, old_image_width, channels = img.shape
    new_image_height, new_image_width = new_shape
    if old_image_width > new_image_width or old_image_height > new_image_height:
        raise ValueError("New shape must be larger than old shape!")

    # Create a new image filled with a solid color (black).
    color = (0, 0, 0)
    new_img = np.full(
        (new_image_height, new_image_width, channels), color, dtype=np.uint8
    )

    # Calculate the top-left coordinate where the original image should be placed.
    x_center = (new_image_width - old_image_width) // 2
    y_center = (new_image_height - old_image_height) // 2

    # Paste the original image onto the new background.
    new_img[
        y_center : y_center + old_image_height, x_center : x_center + old_image_width
    ] = img

    return new_img
