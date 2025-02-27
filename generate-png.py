from PIL import Image
import os

# Constants for card layout
CARDS_PER_ROW = 2  # Cards per row (updated)
CARDS_PER_COLUMN = 3  # Cards per column (remains the same)
CARDS_PER_PAGE = CARDS_PER_ROW * CARDS_PER_COLUMN  # 6 cards per page
CARD_WIDTH_CM = 6.35  # Standard MTG card width in cm
CARD_HEIGHT_CM = 8.89  # Standard MTG card height in cm
MARGIN_CM = 0.2  # Margin between cards

# Convert cm to pixels (300 DPI)
CM_TO_PIXELS = 300 / 2.54
CARD_WIDTH_PX = int(CARD_WIDTH_CM * CM_TO_PIXELS)
CARD_HEIGHT_PX = int(CARD_HEIGHT_CM * CM_TO_PIXELS)
MARGIN_PX = int(MARGIN_CM * CM_TO_PIXELS)

# Folder where images are stored
IMAGE_FOLDER = "mtg_cards"
OUTPUT_FOLDER = "images"
OUTPUT_IMAGE_PREFIX = "combined_mtg_cards"

def load_images(folder):
    """Loads and sorts image files from the specified folder."""
    image_files = sorted(
        [f for f in os.listdir(folder) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    )

    if not image_files:
        print("⚠️ No images found in the folder. Make sure to download the card images first!")
        return []

    images = []
    for file in image_files:
        img_path = os.path.join(folder, file)
        img = Image.open(img_path).convert("RGBA")  # Keep transparency
        images.append(img)
    
    return images

def rotate_image(img, index):
    """Rotate the 2nd and 5th images by 90 degrees and swap width/height."""
    if index % CARDS_PER_PAGE == 1 or index % CARDS_PER_PAGE == 4:  # Positions 2 and 5 (0-indexed)
        img = img.rotate(90, expand=True)
    return img

def combine_images(images):
    """Combines images into multiple PNG images with a maximum of 6 cards per image."""
    if not images:
        print("❌ No images available to combine.")
        return

    pages = [images[i:i + CARDS_PER_PAGE] for i in range(0, len(images), CARDS_PER_PAGE)]
    
    for page_index, page_images in enumerate(pages):
        total_width = CARD_WIDTH_PX + CARD_HEIGHT_PX + MARGIN_PX
        total_height = 2 * CARD_HEIGHT_PX + CARD_WIDTH_PX + 2 * MARGIN_PX

        combined_image = Image.new("RGBA", (total_width, total_height), (255, 255, 255, 0))
        combined_image.info["dpi"] = (300, 300)
        x_offset = 0
        y_offset = 0

        for card_index, img in enumerate(page_images):
            img = rotate_image(img, card_index)
            
            if (card_index + 1) == 4 or (card_index + 1) == 6:
                combined_image.paste(img, (x_offset - CARD_WIDTH_PX + CARD_HEIGHT_PX, y_offset + CARD_WIDTH_PX - CARD_HEIGHT_PX), img)
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
        combined_image.save(image_path, "PNG", dpi=(300, 300))
        print(f"✅ Page {page_index + 1} created: {output_image}")

# Main process
if os.path.exists(IMAGE_FOLDER):
    card_images = load_images(IMAGE_FOLDER)
    combine_images(card_images)
else:
    print(f"❌ Folder '{IMAGE_FOLDER}' not found. Make sure card images are available.")
