from PIL import Image
import os

from reportlab.pdfgen import canvas


def combine_images(image1_path, image2_path, output_path, image2_new_width):
    # Open the first image (keeps original size)
    img1 = Image.open(image1_path).convert("RGBA")

    # Open the second image
    img2 = Image.open(image2_path).convert("RGBA")

    # Calculate new height to maintain aspect ratio
    aspect_ratio = img2.height / img2.width
    image2_new_height = int(image2_new_width * aspect_ratio)

    # Resize second image
    img2_resized = img2.resize((image2_new_width, image2_new_height), Image.LANCZOS)

    # Create a blank canvas large enough to fit both images
    canvas_width = 2480 # img1.width
    print("canvas_width:", canvas_width)
    canvas_height = 3508 # img1.height
    print("canvas_height:", canvas_height)

    canvas = Image.new("RGBA", (canvas_width, canvas_height), (255, 255, 255, 0))
    canvas.info["dpi"] = (300, 300)

    # Paste the first image centered
    canvas.paste(img1, ((canvas_width - img1.width) // 2, (canvas_height - img1.height) // 2), img1)

    # Calculate position for the second image (expanding from center)
    img2_x = (canvas_width - image2_new_width) // 2
    img2_x += 2
    img2_y = (canvas_height - image2_new_height ) // 2
    img2_y += 3

    # Paste the resized second image
    canvas.paste(img2_resized, (img2_x, img2_y), img2_resized)

    # Save the final combined image
    canvas.save(output_path, format="PNG", dpi=(300, 300))
    print(f"Image saved to {output_path}")

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
        # image = Image.open(img_path).convert("RGBA")  # Keep transparency
        images.append(img_path)

    return images
# Example usage
c = canvas.Canvas("result.pdf")
dpi = 300
A4_WIDTH = 11.7 * dpi 
A4_HEIGHT = 16.5 * dpi
for i, img in enumerate(load_images("images")):
   img1 = Image.open(img).convert("RGBA")
   aspect_ratio = img1.height / img1.width
   registration_corner_img = Image.open("registration-corners-only.png").convert("RGBA")
   c.setPageSize((registration_corner_img.width, registration_corner_img.height))
   combine_images("registration-corners-only.png", img, f"result_{i}.png", 1830)
   c.drawImage(f"result_{i}.png", 0, 0, width=registration_corner_img.width, height=registration_corner_img.height)
   c.showPage()
c.save()
