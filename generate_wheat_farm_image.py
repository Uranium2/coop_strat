from PIL import Image, ImageDraw

# Image size (game asset size, can be changed)
WIDTH, HEIGHT = 512, 512

# Colors
BROWN = (185, 122, 86)
YELLOW = (255, 235, 0)
DARK_BROWN = (109, 76, 61)

# Create image
img = Image.new("RGB", (WIDTH, HEIGHT), DARK_BROWN)
draw = ImageDraw.Draw(img)

# Draw the main farm plot (brown rectangle)
farm_margin = 32
farm_rect = [farm_margin, farm_margin, WIDTH - farm_margin, HEIGHT - farm_margin]
draw.rectangle(farm_rect, fill=BROWN, outline=DARK_BROWN, width=4)

# Draw wheat rows (yellow rectangles inside the farm)
row_count = 7
row_spacing = 10
row_height = 24
row_margin = 24
for i in range(row_count):
    top = farm_margin + row_margin + i * (row_height + row_spacing)
    bottom = top + row_height
    left = farm_margin + row_margin
    right = WIDTH - farm_margin - row_margin
    draw.rectangle(
        [left, top, right, bottom], fill=YELLOW, outline=(220, 180, 0), width=2
    )

# Save the image
img.save("wheat_farm_rts_topview.png")
print("Image saved as wheat_farm_rts_topview.png")
