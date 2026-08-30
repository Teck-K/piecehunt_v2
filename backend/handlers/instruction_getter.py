import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import cv2
import fitz
import httpx
import numpy as np
from bs4 import BeautifulSoup

from settings import INSTR_DIR, YOLO_MODEL

# PyMuPDF (fitz), faster then pdf2image

logger = logging.getLogger(__name__)

_worker_model = None


def _run_detection(img, output_path):
    """Runs YOLO detection on a single page image.

    Saves the image if stickered parts are detected.

    Args:
        img: The OpenCV image array to analyse.
        output_path: Path to save the image if a detection is made.

    Returns:
        True if stickered parts were detected, False otherwise.
    """
    global _worker_model
    if _worker_model is None:
        from ultralytics import YOLO

        _worker_model = YOLO(YOLO_MODEL)

    results = _worker_model.predict(
        source=img,
        name="detect",
        save=False,
        conf=0.7,
        show=False,
        save_txt=False,
        # workers en batch hebben geen effect binnen yolo, op 1 gezet en zelf multiprocessing opgezet
        workers=1,
        batch=1,
        device="cpu",
    )
    for r in results:
        if len(r.boxes) > 0:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), img)
            return True
    return False


class InstructionGetter:
    """Downloads and processes building instructions for a Lego set.

    Scrapes the Lego website for PDF instructions, converts pages to images
    and uses a YOLO model to detect pages containing stickered parts.

    Args:
        set_nr: The Lego set number.
    """

    def __init__(self, set_nr):
        self.lego_url = "https://www.lego.com/nl-be/service/building-instructions/"
        self.set_nr = set_nr
        self.instructions_folder = INSTR_DIR / str(self.set_nr)

        self.sticker_folder = INSTR_DIR / str(self.set_nr) / "sticker"

        self.number_of_books = 0

    def get_from_site(self):
        """Scrapes and downloads instruction PDFs from the Lego website.

        Returns:
            A message describing the result of the download.
        """
        try:
            url = self.lego_url + str(self.set_nr)
            headers = {"User-Agent": "Mozilla/5.0"}
            response = httpx.get(url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            pdf_links = []
            for a in soup.find_all("a", href=True):
                # a-tags are hyperlinks, href is the link itself
                href = a["href"]
                if href.endswith(".pdf"):
                    # filename not used for now, has another format than the set number
                    pdf_file = Path(urlparse(href).path).name.lower()
                    # product.bi.core points to the instructions pdf
                    if "product.bi.core.pdf" in href:
                        pdf_links.append((href, pdf_file))
            self.number_of_books = len(pdf_links)

            if self.number_of_books == 0:
                logger.warning("No instructions found for set: %s", self.set_nr)
                return "No instructions found"

            self.instructions_folder.mkdir(parents=True, exist_ok=True)

            for book, (pdf_url, _pdf_file) in enumerate(pdf_links, start=1):
                pdf_data = httpx.get(pdf_url, headers=headers).content
                with open(self.instructions_folder / f"{self.set_nr}_{book}.pdf", "wb") as f:
                    f.write(pdf_data)

        except Exception as e:
            logger.error("Failed to get instructions for set %s: %s", self.set_nr, e, exc_info=True)
            return f"Error occured while getting instructions: {e}"

        logger.info("%d instruction book(s) downloaded for set: %s", self.number_of_books, self.set_nr)
        return f"{self.number_of_books} instruction book(s) downloaded and saved succesfully"

    def stream_pdf_pages(self, pdf_path):
        """Yields pages from a PDF file one at a time to minimise memory usage.

        Args:
            pdf_path: Path to the PDF file.

        Yields:
            A tuple of (page_index, png_bytes) for each page.
        """
        # yield to avoid overuse of ram, only loads a page at a time
        # fitz uses zoom instead of dpi rate
        dpi_rate = 150
        zoom = dpi_rate / 72.0
        doc = fitz.open(pdf_path)
        mat = fitz.Matrix(zoom, zoom)

        for page_index, page in enumerate(doc):
            pix = page.get_pixmap(matrix=mat)
            yield page_index, pix.tobytes("png")

    def get_stickered_parts(self):
        """Scans all instruction PDFs for pages containing stickered parts.

        Uses a YOLO model with multiprocessing to detect sticker pages.
        Saves detected pages as images in the sticker subfolder.

        Yields:
            Progress messages as strings.
        """
        total = 0
        for pdf in self.instructions_folder.rglob("*.pdf"):
            doc = fitz.open(pdf)
            total += len(doc)

        yield f"Scanning {total} pages for stickered parts"

        done = 0
        positive_detections = 0
        last_perc = -1

        with ProcessPoolExecutor(max_workers=8) as executor:
            for book, pdf_file in enumerate(self.instructions_folder.rglob("*.pdf"), start=1):
                futures = []

                for page_index, img_bytes in self.stream_pdf_pages(pdf_file):
                    nparr = np.frombuffer(img_bytes, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                    output_path = self.sticker_folder / f"book{book}_pg{page_index}.png"
                    futures.append(executor.submit(_run_detection, img, output_path))

                for f in as_completed(futures):
                    done += 1
                    perc = int(done / total * 100)
                    try:
                        if f.result():
                            positive_detections += 1

                    except Exception as e:
                        logger.error("Error in YOLO worker: %s", e, exc_info=True)

                    if perc != last_perc:
                        last_perc = perc
                        yield f"Scanning {total} pages for stickered parts, {perc}% done, {positive_detections} pages with stickers found"
