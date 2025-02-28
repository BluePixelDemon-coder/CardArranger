import os
import re
import shutil

import requests
from time import sleep
import numpy as np
from PIL import Image 
import cv2
from reportlab.pdfgen import canvas

SCRYFALL_API_SET = "https://api.scryfall.com/cards/{}/{}"  # Format: set_code / collector_number
IMAGE_FOLDER = "mtg_cards"
CARD_LIST_FILE = "card_list.txt"
IMAGE_FOLDER_BLEED = "mtg_cards_bleed"
OUTPUT_FOLDER = "images"
OUTPUT_IMAGE_PREFIX = "combined_mtg_cards"
CARDS_PER_ROW = 2  # Cards per row (updated)
CARDS_PER_COLUMN = 3  # Cards per column (remains the same)
CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COLUMN  # 6 cards per page
CARD_WIDTH_CM = 6.35  # Standard MTG card width in cm
CARD_HEIGHT_CM = 8.89  # Standard MTG card height in cm
MARGIN_CM = 0.2  # Margin between cards
TOTAL_WIDTH = CARD_WIDTH_CM + CARD_HEIGHT_CM + MARGIN_CM
print("Total width in cm: ", TOTAL_WIDTH)
DPI = 300
CM_TO_PIXELS = DPI / 2.54
CARD_WIDTH_PX = int(CARD_WIDTH_CM * CM_TO_PIXELS)
CARD_HEIGHT_PX = int(CARD_HEIGHT_CM * CM_TO_PIXELS)
MARGIN_PX = int(MARGIN_CM * CM_TO_PIXELS)
BLEED_SIZE_PX = 38
A4_WIDTH = 2480
A4_HEIGHT = 3508
ALL_FILENAMES = []


def fetch_card_image(card_name, set_code, collector_number, count):
    """Fetches a card image from Scryfall and saves it."""
    url = SCRYFALL_API_SET.format(set_code.lower(), collector_number)
    response = requests.get(url)
    sleep(0.1)

    if response.status_code != 200:
        print(
            f"({count}) Error fetching '{card_name} ({set_code}) {collector_number}': {response.json().get('details', 'Unknown error')}")
        return

    card_data = response.json()

    image_url = card_data.get("image_uris", {}).get("png")
    if not image_url:
        print(f"({count}) No PNG image found for '{card_name}'")
        return

    filename = f"{card_name}_{set_code}_{collector_number}.png"
    filename = filename.replace("?", "")
    filename = filename.replace("é", "")
    save_path = os.path.join(IMAGE_FOLDER, filename)

    image_response = requests.get(image_url)
    if image_response.status_code == 200:
        with open(save_path, "wb") as img_file:
            img_file.write(image_response.content)
        print(f"({count}) Downloaded: {filename}")
    else:
        print(f"({count}) Failed to download image for '{card_name}'")


def load_card_list(filename):
    """Reads the list of card names from a file with the format: '1 Card Name (SET) NUMBER'."""
    if not os.path.exists(filename):
        print(f"File '{filename}' not found. Please create it with card names.")
        return []

    card_entries = []
    pattern = re.compile(r"(\d+)\s+(.+?)\s+\((\w+)\)\s+(\d+)")

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            match = pattern.match(line.strip())
            if match:
                count = match.group(1)  # Ignore quantity
                card_name = match.group(2)
                set_code = match.group(3)
                collector_number = match.group(4)
                card_entries.append((count, card_name, set_code, collector_number))

    return card_entries


def download_cards_from_file():
    """Main function to download all cards listed in a file."""
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)

    card_entries = load_card_list(CARD_LIST_FILE)

    if not card_entries:
        print(f"No valid cards found in {CARD_LIST_FILE}.")
        exit(1)

    for count, card_name, set_code, collector_number in card_entries:
        filename = f"{card_name}_{set_code}_{collector_number}.png"
        filename = filename.replace("?", "")
        filename = filename.replace("é", "")
        for j in range(int(count)):
            ALL_FILENAMES.append(filename)
        image_path = os.path.join(IMAGE_FOLDER, filename)

        if os.path.exists(image_path):
            print(f"({count}) Skipping '{filename}' (already downloaded)")
        else:
            fetch_card_image(card_name, set_code, collector_number, count)


def generate_bleed_images(images):
    if not os.path.exists(IMAGE_FOLDER_BLEED):
        os.makedirs(IMAGE_FOLDER_BLEED)
    image_files = sorted(
        [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    )

    if not image_files:
        print("⚠️ No images found in the folder. Make sure to download the card images first!")
        return []

    for file in image_files:
        img_path = os.path.join(IMAGE_FOLDER, file)
        img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        bleed_size = 38  # pixels to add on each side (adjust as needed)

        # ---- Load the Image with Transparency ----
        #img = cv2.imread("input.png", cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError("Image not found or unable to load.")
        height, width = img.shape[:2]

        # ---- Separate Color and Alpha Channels ----
        # (Assuming a PNG with 4 channels: B, G, R, A)
        color = img[:, :, :3]
        alpha = img[:, :, 3]

        # ---- Extend the Color Data ----
        # Use border replication to create a natural bleed in the color channels.
        extended_color = cv2.copyMakeBorder(
            color,
            bleed_size, bleed_size, bleed_size, bleed_size,
            cv2.BORDER_REPLICATE
        )

        # ---- Create a New Alpha Mask via Dilation ----
        # First, create a binary mask from the original alpha channel.
        # (Pixels with alpha > 128 become 255, others 0.)
        _, orig_mask = cv2.threshold(alpha, 128, 255, cv2.THRESH_BINARY)

        # Create an empty canvas for the extended mask.
        extended_mask = np.zeros((height + 2 * bleed_size, width + 2 * bleed_size), dtype=np.uint8)
        # Place the original mask in the center.
        extended_mask[bleed_size:bleed_size + height, bleed_size:bleed_size + width] = orig_mask

        # Dilate the mask to “grow” the nontransparent region.
        # Using an elliptical kernel preserves the rounded shape.
        kernel_size = 2 * bleed_size + 1  # kernel dimensions
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        dilated_mask = cv2.dilate(extended_mask, kernel)

        # Optionally, smooth the dilated mask to get anti-aliased (softer) edges.
        smoothed_mask = cv2.GaussianBlur(dilated_mask, (7, 7), 0)

        # ---- Combine the Extended Color and New Alpha ----
        final_extended = np.dstack([extended_color, smoothed_mask])

        # ---- Save the Final Image ----
        final_image = Image.fromarray(final_extended, "RGBA")
        save_path = os.path.join(IMAGE_FOLDER_BLEED, file)
        final_image.save(save_path)


def load_images(folder):
    """Loads and sorts image files from the specified folder."""
    images = []
    print("All filenames: ", ALL_FILENAMES)
    for filename in ALL_FILENAMES:
        try:
            img = Image.open(os.path.join(folder, filename)).convert("RGBA")
            images.append(img)
        except FileNotFoundError:
            continue
    return images


def rotate_image(img, index):
    """Rotate the 2nd and 5th images by 90 degrees and swap width/height."""
    if index % CARDS_PER_PAGE == 1 or index % CARDS_PER_PAGE == 4:  # Positions 2 and 5 (0-indexed)
        img = img.rotate(90, expand=True)
    return img


def create_cards_page(images):
    """Combines images into multiple PNG images with a maximum of 6 cards per image."""
    if not images:
        print("❌ No images available to combine.")
        return

    pages = [images[i:i + CARDS_PER_PAGE] for i in range(0, len(images), CARDS_PER_PAGE)]

    for page_index, page_images in enumerate(pages):
        total_width = CARD_WIDTH_PX + CARD_HEIGHT_PX + MARGIN_PX
        total_height = 2 * CARD_HEIGHT_PX + CARD_WIDTH_PX + 2 * MARGIN_PX

        combined_image = Image.new("RGBA", (total_width, total_height), (255, 255, 255, 0))
        combined_image.info["dpi"] = (DPI, DPI)
        x_offset = 0
        y_offset = 0

        for card_index, img in enumerate(page_images):
            img = img.resize((CARD_WIDTH_PX, CARD_HEIGHT_PX))
            img = rotate_image(img, card_index)

            if (card_index + 1) == 4 or (card_index + 1) == 6:
                combined_image.paste(img, (
                x_offset - CARD_WIDTH_PX + CARD_HEIGHT_PX, y_offset + CARD_WIDTH_PX - CARD_HEIGHT_PX), img)
            else:
                combined_image.paste(img, (x_offset, y_offset), img)

            if (card_index + 1) % CARDS_PER_ROW == 0:
                x_offset = 0
                y_offset += CARD_HEIGHT_PX + MARGIN_PX
            else:
                x_offset += CARD_WIDTH_PX + MARGIN_PX

        output_image = f"{OUTPUT_IMAGE_PREFIX}_{page_index + 1}.png"
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)
        image_path = os.path.join(OUTPUT_FOLDER, output_image)
        combined_image.save(image_path, "PNG", dpi=(DPI, DPI))
        ALL_FILENAMES.append(output_image)
        print(f"✅ Page {page_index + 1} created: {output_image}")


def combine_corners_with_image(img1, img2, output_path, image2_new_width):
    aspect_ratio = img2.height / img2.width
    image2_new_height = int(image2_new_width * aspect_ratio)
    img2_resized = img2.resize((image2_new_width, image2_new_height), Image.LANCZOS)

    canvas_width = A4_WIDTH
    print("canvas_width:", canvas_width)
    canvas_height = A4_HEIGHT
    print("canvas_height:", canvas_height)

    canvas = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))
    canvas.info["dpi"] = (DPI, DPI)
    canvas.paste(img1, ((canvas_width - img1.width) // 2, (canvas_height - img1.height) // 2), img1)

    img2_x = (canvas_width - image2_new_width) // 2
    # img2_x += 2
    img2_y = (canvas_height - image2_new_height) // 2
    # img2_y += 3

    canvas.paste(img2_resized, (img2_x, img2_y), img2_resized)
    canvas.save(output_path, format="PNG", dpi=(DPI, DPI))
    print(f"Image saved to {output_path}")


if __name__ == "__main__":
    if os.path.exists(OUTPUT_FOLDER):
        shutil.rmtree(OUTPUT_FOLDER)
    if os.path.exists("result"):
        shutil.rmtree("result")
    download_cards_from_file()
    if os.path.exists(IMAGE_FOLDER):
        card_images = load_images(IMAGE_FOLDER)
        create_cards_page(card_images)
    else:
        print(f"❌ Folder '{IMAGE_FOLDER}' not found. Make sure card images are available.")

    c = canvas.Canvas("result.pdf")
    for i, img in enumerate(load_images("images")):
        aspect_ratio = img.height / img.width
        registration_corner_img = Image.open("registration-corners-only.png").convert("RGBA")
        os.makedirs("result", exist_ok=True)
        path = os.path.join("result", f"result_{i}.png")
        combine_corners_with_image(registration_corner_img, img, path, 1830)
        result_img = Image.open(f"result/result_{i}.png").convert("RGBA")
        c.setPageSize((A4_WIDTH, A4_HEIGHT))
        c.drawImage(f"result/result_{i}.png", 0, 0, width=A4_WIDTH, height=A4_HEIGHT)
        c.showPage()
    c.save()
