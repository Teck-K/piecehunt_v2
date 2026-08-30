import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread

import wx

from backend.handlers.image_getter import (
    BricklinkPartImageGetter,
    MinifigImageGetter,
    PartImageGetter,
    SetImageGetter,
)
from backend.handlers.user_handler import UserHandler
from backend.helper.connection_checker import is_connected
from backend.helper.resize_with_wx import resize_image
from backend.helper.singletonmeta import SingletonMeta
from services.api_client import (
    ApiError,
    add_user_set,
    delete_user_set,
    get_my_sets,
    get_set_status,
    get_user_set,
)
from services.api_retry import call_with_refresh
from services.feedback import report_feedback
from settings import (
    MINIFIGS_IMAGES_DIR,
    PART_IMAGES_DIR,
    SETS_IMAGES_DIR,
    MINIFIGS_IMAGES_DIR_150x150,
    PART_IMAGES_DIR_60x60,
    SETS_IMAGES_DIR_160x120,
)

logger = logging.getLogger(__name__)


class SetHandler(metaclass=SingletonMeta):
    """Handles all set-related operations including adding, deleting and image downloading.

    All database access now goes through the Piecehunt API (services.api_client).
    This class only handles local concerns: calling the API and managing images
    on disk.
    """

    def __init__(self):
        self.set_num = ""
        self.normalized_set_num = ""
        self.set_obj = None
        self.images_dir = SETS_IMAGES_DIR
        self.progress_callback = None
        self.callback_text = ""
        self.user_handler = UserHandler()

    def set_exists(self, set_num: str):
        """Checks if a set exists and hasn't been added by the current user yet.

        Stores the set data internally for use in add_set().

        Args:
            set_num: The set number without suffix (e.g. '42154').

        Returns:
            A tuple of (True, success message) or (False, error message).
        """
        if not self.user_handler.is_logged_in:
            return False, "Not logged in"

        try:
            result = call_with_refresh(self.user_handler, get_set_status, set_num)
        except ApiError as e:
            return False, str(e)

        if result is None:
            return False, f"Set: {set_num} not found"

        if result["already_added"]:
            logger.warning("Set %s already added for user %s", set_num, self.user_handler.user_email)
            return False, f"Set: {set_num} is already added"

        self.set_num = set_num
        self.normalized_set_num = f"{set_num}-1"
        self.set_obj = result["set"]

        return True, "Set added"

    def add_set(self):
        """Adds a set to the user's collection and downloads all part images.

        Must be called after set_exists(). The database writes (UserSets,
        UserSetParts for the set + all minifigs) now happen server-side in
        one API call. This method only downloads/rescales the images.

        Minifig images are downloaded in a background thread so the UI is
        never blocked by slow or failing image fetches. The set image is
        downloaded on the main thread so it's available when the UI renders.

        Returns:
            A tuple of (True, success message) or (False, error message).
        """
        try:
            result = call_with_refresh(self.user_handler, add_user_set, self.set_num)
        except ApiError as e:
            logger.error("Failed to add set %s: %s", self.normalized_set_num, e)
            return False, str(e)

        parts = result["parts"]
        minifigs = result["minifigs"]
        set_img_url = result.get("set_img_url")
        set_img_filename = f"{self.normalized_set_num}.jpg"

        try:
            self.callback_text = "Part"
            self.download_part_images(parts)
        except ConnectionError as e:
            logger.error("Internet connection lost while adding set: %s", self.normalized_set_num)
            if self.progress_callback:
                wx.CallAfter(self.progress_callback, 0, 1, "Lost internet connection")
            return False, str(e)

        if self.progress_callback:
            wx.CallAfter(self.progress_callback, 1, 1, "Finalysing")

        # Set image op de hoofdthread — moet beschikbaar zijn wanneer UI rendert
        if not (SETS_IMAGES_DIR / set_img_filename).exists():
            if set_img_url:
                succes, msg = SetImageGetter(set_img_url, set_img_filename).get_image()
                if not succes:
                    logger.error("Failed to save set image for %s: %s", set_img_filename, msg)
                    try:
                        call_with_refresh(
                            self.user_handler,
                            report_feedback,
                            feedback_type="missing_image",
                            description=f"Failed to save set image for {set_img_filename}, url: {set_img_url}: \n {msg}",
                        )
                    except ApiError:
                        pass
                else:
                    self.rescale(image_type="set", filename=set_img_filename)
            else:
                logger.warning("No set image URL available for %s", set_img_filename)

        # Minifig images in achtergrond — UI blokkeert niet op trage/falende downloads
        Thread(
            target=self.download_minifigs_imgs,
            args=(minifigs,),
            daemon=True,
        ).start()

        logger.info("Set %s added for user %s", self.normalized_set_num, self.user_handler.user_email)
        return True, "Set and Image saved"

    def rescale(self, image_type, filename):
        """Rescales an image to the correct dimensions for its type.

        Args:
            image_type: One of 'set', 'minifig' or 'part'.
            filename: The filename of the image to rescale.
        """
        if not filename:
            logger.warning("No valid image file for rescaling: %s", filename)
            return

        if image_type == "set":
            source_file = SETS_IMAGES_DIR / filename
            destination_file = SETS_IMAGES_DIR_160x120 / filename
            max_w, max_h = 160, 120
        elif image_type == "minifig":
            source_file = MINIFIGS_IMAGES_DIR / filename
            destination_file = MINIFIGS_IMAGES_DIR_150x150 / filename
            max_w, max_h = 150, 150
        elif image_type == "part":
            source_file = PART_IMAGES_DIR / filename
            destination_file = PART_IMAGES_DIR_60x60 / filename
            max_w, max_h = 60, 60
        else:
            logger.error("Invalid image_type '%s': only set, minifig or part allowed", image_type)
            return

        if not source_file.exists() or source_file.stat().st_size == 0:
            logger.warning("Skipping rescale — file missing or empty: %s", source_file)
            return

        resize_image(img_path=source_file, out_path=destination_file, max_w=max_w, max_h=max_h)

    def download_minifigs_imgs(self, minifigs):
        """Downloads all minifig images sequentially.

        Args:
            minifigs: list of dicts met keys 'fig_num' en 'img_url' (uit add_user_set()).
        """
        for minifig in minifigs:
            filename = f"{minifig['fig_num']}.jpg"
            if (MINIFIGS_IMAGES_DIR / filename).exists():
                continue

            img_url = minifig.get("img_url")
            if img_url:
                try:
                    succes, msg = MinifigImageGetter(img_url, filename).get_image()
                    if not succes:
                        logger.error("Failed to save minifig image %s: %s", filename, msg)
                        try:
                            call_with_refresh(
                                self.user_handler,
                                report_feedback,
                                feedback_type="missing_image",
                                description=f"Failed to save minifig image {filename}, url: {img_url}:\n{msg}",
                            )
                        except ApiError:
                            pass
                    else:
                        self.rescale(image_type="minifig", filename=filename)
                except Exception:
                    logger.error("Failed to save minifig image %s", filename, exc_info=True)
            else:
                logger.warning("No image URL for minifig %s", minifig["fig_num"])
                try:
                    call_with_refresh(
                        self.user_handler,
                        report_feedback,
                        feedback_type="missing_image",
                        description=f"No image URL for minifig {minifig['fig_num']}",
                    )
                except ApiError:
                    pass

    def get_all_user_sets(self, include_spares: bool = True) -> list[dict]:
        """Retrieves all sets for the current user with progress and image data."""
        try:
            sets = call_with_refresh(self.user_handler, get_my_sets, include_spares=include_spares)
        except ApiError as e:
            logger.error("Failed to fetch user sets: %s", e)
            return []

        for s in sets:
            set_img_filename = f"{s['set_num']}.jpg"
            s["img_path"] = SETS_IMAGES_DIR_160x120 / set_img_filename

        return sets

    def download_part_images(self, parts):
        """Downloads all part images using a thread pool.

        Args:
            parts: list of dicts with keys 'part_num', 'color_id', 'img_url'
                (from add_user_set()).

        Raises:
            ConnectionError: If the internet connection is lost during download.
        """
        if not is_connected():
            raise ConnectionError("No Internet Connection")

        new_parts = []
        for part in parts:
            filename = f"{part['part_num']}_{part['color_id']}.jpg"
            if not (PART_IMAGES_DIR / filename).exists():
                new_parts.append(part)

        total = len(new_parts)
        count = 0

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(self.download_single_image, part) for part in new_parts]

            for future in as_completed(futures):
                try:
                    future.result()
                    count += 1
                    if self.progress_callback:
                        wx.CallAfter(self.progress_callback, count, total, self.callback_text)
                except ConnectionError:
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise

    def download_single_image(self, part):
        """part: dict met keys 'part_num', 'color_id', 'img_url'."""
        if not is_connected():
            raise ConnectionError("No Internet Connection")

        img_url = part.get("img_url")
        part_num = part["part_num"]
        color_id = part["color_id"]
        filename = f"{part_num}_{color_id}.jpg"
        succes = False

        if img_url:
            succes, msg = PartImageGetter(img_url, filename).get_image()
        if not succes:
            succes, msg = BricklinkPartImageGetter(rb_color_id=color_id, rb_part_num=part_num, filename=filename).get_image()
            if not succes:
                succes, msg = BricklinkPartImageGetter(
                    rb_color_id=color_id, rb_part_num=part_num, filename=filename, alternative=True
                ).get_image()
                if not succes:
                    logger.error("Failed to download part image after 3 attempts: %s - %s", filename, msg)
                    try:
                        call_with_refresh(
                            self.user_handler,
                            report_feedback,
                            feedback_type="missing_image",
                            description=f"""Failed to download part image after 3 attempts: part_num = {part_num},
                                        color_id = {color_id}:\n{msg}""",
                        )
                    except ApiError:
                        pass

        if succes:
            self.rescale(image_type="part", filename=filename)

        return True

    def delete_set(self, user_set_id):
        """Deletes a user's set (and its parts, via cascade) through the API.

        Args:
            user_set_id: The ID of the UserSets record to delete.

        Returns:
            A tuple of (True, success message) or (False, error message).
        """
        try:
            call_with_refresh(self.user_handler, delete_user_set, user_set_id)
        except ApiError as e:
            logger.error("Failed to delete set %s: %s", user_set_id, e)
            return False, str(e)

        logger.info("Set deleted: %s", user_set_id)
        return True, "Set successfully deleted"

    def get_userset_object(self, userset_id):
        try:
            result = call_with_refresh(self.user_handler, get_user_set, userset_id)
        except ApiError as e:
            logger.error("Userset %s not found: %s", userset_id, e)
            return False, "Userset Not Found"

        if result is None:
            return False, "Userset Not Found"

        return True, result
