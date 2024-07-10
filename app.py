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
        print(font)
        if total_height <= max_height:
            return font, lines
    
    font = ImageFont.truetype("fonts/Inter-Bold.ttf", min_font_size)
    return font, wrap_text(draw, text, font, max_width)

def load_external_image(image_link, image_width, height):
    try:
        response = requests.get(image_link, stream=True)
        response.raise_for_status()
        external_img = Image.open(BytesIO(response.content))
        external_img.thumbnail((image_width, height))
        return external_img
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image: {e}")
    except IOError as e:
        print(f"Error processing image: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    return None

def calculate_percentage(price, list_price):
    if not list_price or float(list_price) <= float(price):
        return None
    discount = float(list_price) - float(price)
    percentage = (discount / float(list_price)) * 100
    return round(percentage)

def draw_text_section(width, height, title, listPrice, price):
    blue_section = Image.new('RGB', (width, height), color=(0, 0, 255))
    d_blue = ImageDraw.Draw(blue_section)

    # Reserve space for price information
    price_section_height = 100
    title_section_height = height - price_section_height

    # Fit title text
    font_title, wrapped_title = fit_text(d_blue, title, width - 20, title_section_height - 60, 25, 40)

    # Draw title
    current_y_position = 10
    for line in wrapped_title:
        d_blue.text((10, current_y_position), line, fill="white", font=font_title)
        text_height = font_title.getbbox(line)[3] - font_title.getbbox(line)[1]
        current_y_position += text_height + 5

    # Draw price information
    font_price = ImageFont.truetype("fonts/Inter-Medium.ttf", 30)
    font_listPrice = ImageFont.truetype("fonts/Inter-Regular.ttf", 18)
    font_percentage = ImageFont.truetype("fonts/Inter-Bold.ttf", 20)

    list_price_y_position = height - 75
    price_y_position = height - 50

    # Draw list price
    list_price_text = f"${listPrice}"
    d_blue.text((10, list_price_y_position), list_price_text, fill="white", font=font_listPrice)
    text_width = font_listPrice.getbbox(list_price_text)[2] - font_listPrice.getbbox(list_price_text)[0]
    d_blue.line([(10, list_price_y_position + 10), (10 + text_width, list_price_y_position + 10)], fill="white", width=1)

    # Draw price and percentage
    price_text = f"${price}"
    d_blue.text((10, price_y_position), price_text, fill="white", font=font_price)
    
    price_width = font_price.getbbox(price_text)[2] - font_price.getbbox(price_text)[0]
    if listPrice and float(listPrice) > float(price):
        percentage = calculate_percentage(price, listPrice)
        if percentage:
            percentage_x = 15 + price_width
            d_blue.text((percentage_x, price_y_position), f" ({percentage}% off)", fill="white", font=font_percentage)
        
    return blue_section

def create_image(title, price, listPrice, image_link):
    width, height = 600, 600
    blue_width = int(0.33 * width)
    image_width = width - blue_width
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    
    logo_url = 'https://backend.pzdeals.com/assets/6f2ceb4e-a8e4-4b03-82f5-8a93dc53850e?cache-buster=2024-06-20T15:11:09.711Z&key=system-large-contain'
    response = requests.get(logo_url)
    logo_img = Image.open(BytesIO(response.content))

    logoWidth = 45
    logoHeight = int((logo_img.height / logo_img.width) * logoWidth)
    logo_img = logo_img.resize((logoWidth, logoHeight))
    img.paste(logo_img, (10, 10))

    external_img = load_external_image(image_link, image_width, height)
    if external_img:
        paste_x = (image_width - external_img.width) // 2
        paste_y = (height - external_img.height) // 2
        img.paste(external_img, (paste_x, paste_y))
    else:
        d = ImageDraw.Draw(img)
        d.text((10, 10), "Failed to load image", fill=(255, 0, 0))

    blue_section = draw_text_section(blue_width, height, title, listPrice, price)
    img.paste(blue_section, (image_width, 0))

    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr

@app.route('/generate_image')
def generate_image():
    title = request.args.get('title', 'Default Title')
    price = request.args.get('price', '0.00')
    listPrice = request.args.get('listPrice', '0.00')
    image_link = request.args.get('imageLink', 'https://www.pzdeals.com/cdn/shop/files/v-2024-06-09T120851.090_grande.png?v=1717949388')

    img_buffer = create_image(title, price, listPrice, image_link)
    response = send_file(img_buffer, mimetype='image/png')
    response.headers['Content-Length'] = img_buffer.getbuffer().nbytes
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8055)