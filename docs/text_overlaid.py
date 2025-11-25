from PIL import ImageDraw, ImageFont 

# Create a draw object to modify the base image  
draw = ImageDraw.Draw(base_image)  
 
# Load a font (replace with your font path; use system fonts or download from Google Fonts)  
# Example: Use Arial (Windows) or Roboto (downloaded)  
font = ImageFont.truetype(font_choice, size= size_choice)  # Size = 40pt  
 
# Text content and style  
text = "Summer Sale 2024!"  
text_color = (255, 0, 0)  # Red (RGB values: 0-255)  
text_position = (50, height - 100)  # 50px left, 100px above bottom  
 
# Draw the text  
draw.text(text_position, text, font=font, fill=text_color)  