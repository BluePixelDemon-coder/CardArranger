import os
import re
import requests
from time import sleep

# Scryfall API URLs
SCRYFALL_API_SET = "https://api.scryfall.com/cards/{}/{}"  # Format: set_code / collector_number

# Folder to store downloaded images
IMAGE_FOLDER = "mtg_cards"
CARD_LIST_FILE = "card_list.txt"

def fetch_card_image(card_name, set_code, collector_number, display_number):
    """Fetches a card image from Scryfall and saves it."""
    url = SCRYFALL_API_SET.format(set_code.lower(), collector_number)
    response = requests.get(url)
    sleep(0.1)

    if response.status_code != 200:
        print(f"❌ ({display_number}) Error fetching '{card_name} ({set_code}) {collector_number}': {response.json().get('details', 'Unknown error')}")
        return

    card_data = response.json()
    
    # Try getting the PNG image (best quality with transparency)
    image_url = card_data.get("image_uris", {}).get("png")
    if not image_url:
        print(f"⚠️ ({display_number}) No PNG image found for '{card_name}'")
        return

    # Format filename to include set and number
    filename = f"{card_name}_{set_code}_{collector_number}.png"
    save_path = os.path.join(IMAGE_FOLDER, filename)

    # Download and save the image
    image_response = requests.get(image_url)
    if image_response.status_code == 200:
        with open(save_path, "wb") as img_file:
            img_file.write(image_response.content)
        print(f"✅ ({display_number}) Downloaded: {filename}")
    else:
        print(f"❌ ({display_number}) Failed to download image for '{card_name}'")

def load_card_list(filename):
    """Reads the list of card names from a file with the format: '1 Card Name (SET) NUMBER'."""
    if not os.path.exists(filename):
        print(f"❌ File '{filename}' not found. Please create it with card names.")
        return []

    card_entries = []
    pattern = re.compile(r"(\d+)\s+(.+?)\s+\((\w+)\)\s+(\d+)")
    
    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            match = pattern.match(line.strip())
            if match:
                display_number = match.group(1)  # Ignore quantity
                card_name = match.group(2)
                set_code = match.group(3)
                collector_number = match.group(4)
                card_entries.append((display_number, card_name, set_code, collector_number))
    
    return card_entries

def download_cards_from_file():
    """Main function to download all cards listed in a file."""
    if not os.path.exists(IMAGE_FOLDER):
        os.makedirs(IMAGE_FOLDER)

    card_entries = load_card_list(CARD_LIST_FILE)

    if not card_entries:
        print("⚠️ No valid cards found in the file.")
        return

    for display_number, card_name, set_code, collector_number in card_entries:
        filename = f"{card_name}_{set_code}_{collector_number}.png"
        image_path = os.path.join(IMAGE_FOLDER, filename)

        if os.path.exists(image_path):
            print(f"⏭️ ({display_number}) Skipping '{filename}' (already downloaded)")
        else:
            fetch_card_image(card_name, set_code, collector_number, display_number)

# Run the script
download_cards_from_file()
