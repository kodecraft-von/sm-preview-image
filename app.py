from flask import Flask, send_file, request
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

app = Flask(__name__)

def wrap_text(draw, text, font, max_width):
    words = text.split(' ')
    lines = []
    line = ''
    for word in words:
        test_line = line + word + ' '
        width = font.getbbox(test_line)[2]
        if width > max_width and line:
            lines.append(line)
            line = word + ' '
        else:
            line = test_line
    lines.append(line)
    return lines

def fit_text(draw, text, max_width, max_height, min_font_size, max_font_size):
    for font_size in range(max_font_size, min_font_size - 1, -1):
        font = ImageFont.truetype("fonts/Inter-Bold.ttf", font_size)
        lines = wrap_text(draw, text, font, max_width)
        total_height = sum(font.getbbox(line)[3] - font.getbbox(line)[1] for line in lines)
        if total_height <= max_height:
            return font, lines

    font = ImageFont.truetype("fonts/Inter-Bold.ttf", min_font_size)
    return font, wrap_text(draw, text, font, max_width)

def load_external_image(image_link, image_width, height):
    try:
        response = requests.get(image_link, stream=True)
        response.raise_for_status()
        external_img = Image.open(BytesIO(response.content))
        external_img = external_img.convert("RGBA")
        
        # Resize the image while maintaining aspect ratio
        external_img.thumbnail((image_width, height))
        return external_img
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

def draw_price_section(width, height, listPrice, price, percentage, title):
    blue_section = Image.new('RGB', (width, height), "#02326A")  # Dark blue
    d_blue = ImageDraw.Draw(blue_section)

    font_price = ImageFont.truetype("fonts/Inter-Bold.ttf", 100)
    font_dollar = ImageFont.truetype("fonts/Inter-Bold.ttf", 60)  # Smaller font for dollar sign
    font_listPrice = ImageFont.truetype("fonts/Inter-Regular.ttf", 50)
    font_percentage = ImageFont.truetype("fonts/Inter-ExtraBold.ttf", 35)
    font_soloPercentage = ImageFont.truetype("fonts/Inter-ExtraBold.ttf", 80)

    if title is not None and price is None and listPrice is None and percentage is None:
        font_title, wrapped_title = fit_text(d_blue, title, width - 20, height // 2, 50, 50)
        
        line_spacing = int(font_title.size * 0.25) 
        line_heights = [font_title.getbbox(line)[3] - font_title.getbbox(line)[1] for line in wrapped_title]
        total_text_height = sum(line_heights) + line_spacing * (len(wrapped_title) - 1)
        
        start_y = (height - total_text_height) // 2 
        
        current_y_position = start_y

        for i, line in enumerate(wrapped_title):
            d_blue.text((10, current_y_position), line, fill="white", font=font_title)
            
            # Add full line spacing only between lines, not before first or after last
            if i < len(wrapped_title) - 1:
                current_y_position += line_heights[i] + line_spacing
            else:
                current_y_position += line_heights[i]

    if price is not None:
        # Calculate vertical positions
        price_y_position = height // 2 - 75
        list_price_y_position = price_y_position + 70  # Below the price

        dollar_sign = "$"
        price_text = f"{price}"
        dollar_width = d_blue.textlength(dollar_sign, font=font_dollar)
        price_width = d_blue.textlength(price_text, font=font_price)
        total_width = dollar_width + price_width + 5  # Add a small gap between $ and price
        price_x_position = (width - total_width) // 2

        # Draw dollar sign
        d_blue.text((price_x_position, price_y_position), dollar_sign, fill="white", font=font_dollar)  # Adjust Y position to align with price

        # Draw price
        d_blue.text((price_x_position + dollar_width, price_y_position), price_text, fill="white", font=font_price)

        # Calculate and draw percentage
    if percentage is not None and price is not None and listPrice is not None:
        percentage_text = f"{percentage}% OFF"
        text_width = d_blue.textlength(percentage_text, font=font_percentage)
        x_position = (width - text_width) // 2
        d_blue.text((price_x_position, price_y_position - 33), percentage_text, fill="#EE6C56", font=font_percentage)  # Orange

    if price is None and listPrice is None and percentage is not None:
        percentage_text = f"{percentage}% OFF"
        text_width = d_blue.textlength(percentage_text, font=font_percentage)
        x_position = (width - text_width) // 2 - 100
        d_blue.text((x_position, height // 2 - 60), percentage_text, fill="#EE6C56", font=font_soloPercentage)


    # Draw list price with strikethrough
    if listPrice is not None:
        list_price_text = f"${listPrice}"
        was_text = "was "
        was_width = d_blue.textlength(was_text, font=font_listPrice)
        list_price_width = d_blue.textlength(list_price_text, font=font_listPrice)
        total_width = was_width + list_price_width
        
        x_position = price_x_position
        
        # Draw "Was" text
        d_blue.text((x_position, list_price_y_position + 45), was_text, fill="white", font=font_listPrice)
        
        # Draw list price
        list_price_x = x_position + was_width
        d_blue.text((list_price_x, list_price_y_position + 45), list_price_text, fill="white", font=font_listPrice)
        
        # Add strikethrough only to the price
        text_height = font_listPrice.getbbox(list_price_text)[3] - font_listPrice.getbbox(list_price_text)[1]
        strikethrough_y = (list_price_y_position + text_height // 2) + 50 
        d_blue.line([(list_price_x, strikethrough_y), (list_price_x + list_price_width, strikethrough_y)], fill="white", width=5)



    return blue_section

def create_image(price, listPrice, image_link, percentage, title):
    width, height = 1200, 628
    blue_width = int(0.4 * width)
    image_width = (width - blue_width)
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    logo_path = 'assets/pzdeals.png'
    logo_img = Image.open(logo_path).convert("RGBA")

    # Load and paste main image
    external_img = load_external_image(image_link, image_width, height)
    if external_img:
        # Calculate the position to center the image in the left area
        paste_x = (image_width - external_img.width) // 2
        paste_y = (height - external_img.height) // 2
        img.paste(external_img, (paste_x, paste_y))

        # Load and paste logo
        logoWidth = 60
        logoHeight = int((logo_img.height / logo_img.width) * logoWidth)
        logo_img = logo_img.resize((logoWidth, logoHeight), Image.LANCZOS)
        img.paste(logo_img, (10, 10), mask=logo_img)
    else:
        # Calculate the size for the large logo (90% of the available space)
        large_logo_width = int(image_width * 0.9)
        large_logo_height = int((logo_img.height / logo_img.width) * large_logo_width)
        if large_logo_height > height * 0.9:
            large_logo_height = int(height * 0.9)
            large_logo_width = int((logo_img.width / logo_img.height) * large_logo_height)
        
        large_logo = logo_img.resize((large_logo_width, large_logo_height), Image.LANCZOS)
        paste_x = (image_width - large_logo_width) // 2
        paste_y = (height - large_logo_height) // 2
        img.paste(large_logo, (paste_x, paste_y), mask=large_logo)

    # Create and paste price section
    blue_section = draw_price_section(blue_width, height, listPrice, price, percentage, title)
    img.paste(blue_section, (image_width, 0))

    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr


@app.route('/generate_image')
def generate_image():
    price = request.args.get('price')
    listPrice = request.args.get('listPrice')
    image_link = request.args.get('imageLink')
    percentage = request.args.get('percentage')
    title = request.args.get('title')
    try:
        img_buffer = create_image(price, listPrice, image_link, percentage, title)
        return send_file(img_buffer, mimetype='image/jpeg')
    except Exception as e:
        print(f"Error generating image: {e}")
        return "Error generating image"
    
if __name__ == '__main__':
    app.run(debug=False)