"""Image resizing utilities for PieceHunt.

Provides single image and batch resizing using wxPython's image handling.
Requires a wx.App instance to be active before use.
"""

import logging

import wx

logger = logging.getLogger(__name__)


def resize_image(img_path, out_path, max_w, max_h):
    """Resizes a single image to fit within the given dimensions.

    Maintains aspect ratio and saves as PNG with maximum quality.
    Only supports .jpg, .jpeg and .png files.

    Args:
        img_path: Path to the source image.
        out_path: Path to save the resized image.
        max_w: Maximum width in pixels.
        max_h: Maximum height in pixels.
    """
    img = wx.Image(str(img_path), wx.BITMAP_TYPE_ANY)

    w, h = img.GetWidth(), img.GetHeight()

    scale = min(max_w / w, max_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)
    try:
        if img_path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
            img = img.Scale(new_w, new_h, wx.IMAGE_QUALITY_HIGH)
            img.SetOption(wx.IMAGE_OPTION_QUALITY, "100")
            img.SaveFile(str(out_path), wx.BITMAP_TYPE_PNG)
        else:
            raise ValueError(f"Unsupported image format: {img_path.suffix}")

    except ValueError as e:
        logger.error("Failed to resize image %s: %s", img_path, e)

    except OSError as e:
        logger.error("Failed to read or write image %s: %s", img_path, e, exc_info=True)

    except Exception as e:
        logger.error("Unexpected error resizing image %s: %s", img_path, e, exc_info=True)


def batch_resize(src_folder, dst_folder, max_w, max_h):
    """Resizes all images in a folder to fit within the given dimensions.

    Args:
        src_folder: Path to the source folder.
        dst_folder: Path to the destination folder, created if it doesn't exist.
        max_w: Maximum width in pixels.
        max_h: Maximum height in pixels.
    """
    dst_folder.mkdir(exist_ok=True)

    for file in src_folder.iterdir():
        out = dst_folder / file.name
        resize_image(file, out, max_w, max_h)


if __name__ == "__main__":
    pass
