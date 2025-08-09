# -*- coding: utf-8 -*>
import numpy as np
from PIL import Image
from skimage.segmentation import flood_fill


def remove_background(img, threshold=10, init_pos=(0, 0), mode='fill'):
    """ Remove background of img using pixel value from a position

    Parameters
    ----------
    img : ndarray
        Input img.
    threshold : int, optional
        Threshold for background detection in case of noise.
    init_pos : tuple, optional
        Position at which the color is detected.
    mode : {'fill', 'value'}, optional
        Either replace all close values or use a floodfill.

    Returns
    -------
    new_img : ndarray
        img with background removed.
    mask : ndarray
        Mask of the background.

    """
    img = img.astype(np.float32)
    if img.shape[-1] == 4:
        img = img[:, :, 0:3]

    value = img[init_pos]
    norm = np.linalg.norm(np.abs(img - value), axis=-1)

    if mode == 'fill':
        binary_struct = np.zeros((3, 3))
        binary_struct[0:3, 1] = 1
        binary_struct[1, 0:3] = 1

        mask = flood_fill(norm, init_pos, 999,
                          footprint=binary_struct,
                          tolerance=threshold)
        mask = np.where(mask == 999, 0, 255)
    else:
        mask = np.where(norm < threshold, 0, 255)

    # The detected background is used in the Alpha channel
    new_img = np.zeros(img.shape[0:2] + (4,)).astype(np.uint8)
    new_img[:, :, 0:3] = img
    new_img[:, :, 3] = mask

    return new_img, mask.astype(np.uint8)


def auto_crop(img, borders=0):
    """ Crop image to the bounding box of the background

    Parameters
    ----------
    img : ndarray
        Input img.
    borders : int, optional
        Border around the bounding box.

    Returns
    -------
    cropped : ndarray
        Cropped img.

    """
    value = img[0, 0]
    new_shape = (img.shape[0] + borders, img.shape[1] + borders, img.shape[2])
    new_img = np.ones(new_shape, dtype=np.uint8) * value

    new_img[borders//2:borders//2 + img.shape[0],
            borders//2:borders//2 + img.shape[1], :] = img
    _, mask = remove_background(new_img)

    # Find the bounding box of the background mask
    x, y = np.where(mask == 255)
    x_min, x_max = np.min(x), np.max(x)
    y_min, y_max = np.min(y), np.max(y)
    cropped = new_img[x_min - borders//2:x_max + borders//2 + 1,
                      y_min - borders//2:y_max + borders//2 + 1, :]

    return cropped


def resize(img, ratio_frac=None, ratio_val=None, dimensions=None, scale=None):
    """ Resize image

    Parameters
    ----------
    img : ndarray
        Input img.
    ratio_frac : float, optional
        Ratio between the two dimensions.
    ratio_val : tuple, optional
        Values of the ratio between the two dimensions.
    dimensions : tuple, optional
        Dimensions of the output image.
    scale : float, optional
        Scaling factor of the output image.

    Returns
    -------
    resized : ndarray
        Resized image.

    """
    if ratio_val is not None:
        if len(ratio_val) != 2:
            raise ValueError('Ratio must be a 2-tuple')
        if ratio_val[1] == 0:
            raise ValueError('Ratio must be non-zero')
    ratio_frac = ratio_val[1] / \
        ratio_val[0] if ratio_val is not None else ratio_frac
    if scale is not None:
        dimensions = (img.shape[1] * scale, img.shape[0] * scale)

    if dimensions is not None:
        dim_1, dim_2 = dimensions
    elif ratio_frac is not None:
        dim_1 = img.shape[0]
        dim_2 = img.shape[0] * ratio_frac
    else:
        raise ValueError('At least one in three option must be specified!')

    return Image.fromarray(img).resize((int(dim_1), int(dim_2)))


def generate_mosaic(imgs, rows, columns, auto_bbox=True, auto_border=True,
                    scaling_method='resize_to_avg'):
    """ Generate a mosaic from a list of images

    Parameters
    ----------
    imgs : list
        List of images.
    rows : int
        Number of rows in the mosaic.
    columns : int
        Number of columns in the mosaic.
    auto_bbox : bool, optional
        Crop the images to the bounding box of the background.
    auto_border : bool, optional
        Add a border around the bounding box.
    scaling_method : {'resize_to_avg', 'resize_to_max', 'pad_to_max'}, optional
        Method used to scale the images.

    Returns
    -------
    mosaic : ndarray
        Mosaic of the images.

    """
    sizes = np.zeros((len(imgs), 2))
    for i, img in enumerate(imgs):
        if auto_bbox:
            imgs[i] = auto_crop(img)
        if auto_border:
            border = (img.shape[0] + img.shape[1]) // 20
            imgs[i] = auto_crop(img, borders=border)
        sizes[i] = imgs[i].shape[0:2]

    # Compute the final size of the mosaic using one of three methods
    ratio = sizes[:, 0] / sizes[:, 1]
    if scaling_method == 'resize_to_avg':
        final_size = np.mean(sizes, axis=0, dtype=np.uint16)
    elif scaling_method == 'resize_to_max' or scaling_method == 'pad_to_max':
        final_size = np.max(sizes, axis=0).astype(np.uint16)
    avg_ratio = final_size[0] / final_size[1]
    for i, img in enumerate(imgs):
        # If the image is wider than the final, then the width is set to the
        # final width and we compute the height accordingly.
        if ratio[i] > avg_ratio:
            dim_1 = final_size[0]
            dim_2 = dim_1 / ratio[i]
        else:
            dim_2 = final_size[1]
            dim_1 = dim_2 * ratio[i]

        if scaling_method == 'resize_to_avg' \
                or scaling_method == 'resize_to_max':
            imgs[i] = np.asarray(resize(img, dimensions=(dim_2, dim_1)))
        imgs[i] = pad_image_to_center(imgs[i], final_size)

    mosaic = np.zeros((int(final_size[0] * rows),
                       int(final_size[1] * columns), 3))

    # With the image now resized, we can create the mosaic
    for i, img in enumerate(imgs):
        if rows <= columns:
            row = i % columns
            col = i // columns
        else:
            row = i // rows
            col = i % rows
        mosaic[col * final_size[0]:(col + 1) * final_size[0],
               row * final_size[1]:(row + 1) * final_size[1], :] = img[:, :, 0:3]

    return mosaic.astype(np.uint8)


def pad_image_to_center(img, new_shape):
    """ Pad image to center (always larger than the original image)

    Parameters
    ----------
    img : ndarray
        Input image.
    new_shape : tuple
        Dimensions of the output image.

    Returns
    -------
    new_img : ndarray
        Padded image.

    """
    old_image_height, old_image_width, channels = img.shape
    new_image_width, new_image_height = new_shape[::-1]
    if old_image_width > new_image_width or old_image_height > new_image_height:
        raise ValueError('New shape must be larger than old shape!')

    color = img[0, 0]
    new_img = np.full((new_image_height, new_image_width, channels),
                      color, dtype=np.uint8)

    # compute center offset
    x_center = (new_image_width - old_image_width) // 2
    y_center = (new_image_height - old_image_height) // 2

    # copy img image into center of result image
    new_img[y_center:y_center+old_image_height,
            x_center:x_center+old_image_width] = img

    return new_img