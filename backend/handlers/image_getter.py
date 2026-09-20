"""Image downloading utilities for PieceHunt.

Provides an abstract base class and concrete implementations for
downloading images from Rebrickable and BrickLink.
"""

import json
import logging
from abc import ABC, abstractmethod

import httpx

from settings import (
    BACKEND_HANDLERS_DIR,
    MINIFIGS_IMAGES_DIR,
    PART_IMAGES_DIR,
    SETS_IMAGES_DIR,
)

logger = logging.getLogger(__name__)


class ImageGetter(ABC):
    """Abstract base class for downloading and caching images.

    Subclasses must implement get_url() and get_destination_path()
    to define the source URL and local storage location.
    -> manditory because of ABC

    Args:
        max_MB: Maximum allowed image size in megabytes. Defaults to 10.
    """

    def __init__(self, max_MB=10):

        self.client = httpx.Client(timeout=10, transport=httpx.HTTPTransport(retries=3))  # transport = retries at conn error
        url = self.get_url()
        self.max_MB = max_MB
        self.url = url

    @abstractmethod
    def get_url(self):
        """Returns the URL of the image to download.
        implemented by the child class"""
        pass

    @abstractmethod
    def get_destination_path(self):
        """Returns the local Path where the image should be saved.
        implemented by the child class"""
        pass

    def get_image(self):
        """Downloads the image if it does not already exist locally."""
        self.destination_path = self.get_destination_path()

        if self.destination_path.exists():
            return True, "Image already exists"

        if not self.url or not str(self.url).startswith("http"):
            return False, "No valid url"

        try:
            response = self.client.get(
                self.url,
                follow_redirects=True,
            )
            response.raise_for_status()

            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > self.max_MB * 1024 * 1024:
                raise ValueError(f"Image exceptionally large ({int(content_length) / 1024 / 1024:.2f} MB), check url: {self.url}")

            with open(self.destination_path, "wb") as f:
                f.write(response.content)

            return True, "Image download successful"

        except Exception as e:
            logger.error(
                "Failed to download image %s: %s",
                self.url,
                e,
                exc_info=True,
            )
            return False, f"Error while downloading image {self.url}: {e}"


class RebrickableImageGetter(ImageGetter):
    def __init__(self, rb_url, destination, filename):
        self.rb_url = rb_url
        self.destination = destination
        self.filename = filename
        super().__init__()

    def get_url(self):
        return self.rb_url

    def get_destination_path(self):
        return self.destination / self.filename


class SetImageGetter(RebrickableImageGetter):
    def __init__(self, rb_url, filename):
        destination = SETS_IMAGES_DIR
        super().__init__(rb_url, destination, filename)


class MinifigImageGetter(RebrickableImageGetter):
    def __init__(self, rb_url, filename):
        destination = MINIFIGS_IMAGES_DIR
        super().__init__(rb_url, destination, filename)


class PartImageGetter(RebrickableImageGetter):
    def __init__(self, rb_url, filename):
        destination = PART_IMAGES_DIR
        super().__init__(rb_url, destination, filename)


class BricklinkPartImageGetter(ImageGetter):
    """Downloads part images from BrickLink using a Rebrickable to BrickLink color mapping.

    The color mapping is loaded once as a class attribute to avoid
    repeated file reads.

    Args:
        rb_url: The Rebrickable image URL as fallback reference.
        rb_color_id: The Rebrickable color ID to map to BrickLink.
        rb_part_num: The Rebrickable part number.
        filename: The local filename to save the image as.
        alternative: If True, strips non-numeric characters from the part number.
    """

    color_mapping_file = BACKEND_HANDLERS_DIR / "color_mapping.json"
    with open(color_mapping_file, "r") as f:
        color_mapping = json.load(f)

    def __init__(self, rb_color_id, rb_part_num, filename, alternative=False, rb_url=None):
        self.destination = PART_IMAGES_DIR
        self.filename = filename
        self.alternative = alternative
        self.rb_color_id = rb_color_id
        self.rb_part_num = rb_part_num
        self.rb_url = rb_url
        super().__init__()

    def get_destination_path(self):
        return self.destination / self.filename

    def get_url(self):
        # color mapping because rebrickable uses other color codes then bricklink

        bricklink_data = BricklinkPartImageGetter.color_mapping.get(str(self.rb_color_id))
        if bricklink_data:
            bricklink_color_id = bricklink_data["ext_ids"][0]
            if not bricklink_color_id:
                return None
            if self.alternative:
                numbers_only = "".join(c for c in self.rb_part_num if c.isdigit())
                return f"https://img.bricklink.com/ItemImage/PN/{bricklink_color_id}/{numbers_only}.png"

            return f"https://img.bricklink.com/ItemImage/PN/{bricklink_color_id}/{self.rb_part_num}.png"

        return None
