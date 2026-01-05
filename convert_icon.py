"""
Convert SVG motor icon to ICO format for Windows executable
"""
from PIL import Image
import cairosvg
import io

# Convert SVG to PNG in memory
svg_file = 'motor_icon.svg'
png_data = cairosvg.svg2png(url=svg_file, output_width=256, output_height=256)

# Open PNG data and save as ICO
img = Image.open(io.BytesIO(png_data))
img.save('motor_icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])

print("✅ motor_icon.ico created successfully!")
