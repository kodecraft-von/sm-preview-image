from flask import Flask, send_file, request
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO

app = Flask(__name__)

def load_external_image(image_link, image_width, height):
    try:
        response = requests.get(image_link, stream=True)
        response.raise_for_status()
        external_img = Image.open(BytesIO(response.content))
        external_img.thumbnail((image_width, height))
        return external_img
    except Exception as e:
        print(f"Error loading image: {e}")
        return None

def draw_price_section(width, height, listPrice, price):
    blue_section = Image.new('RGB', (width, height), color=(0, 0, 255))
    d_blue = ImageDraw.Draw(blue_section)

    font_price = ImageFont.truetype("fonts/Inter-Bold.ttf", 60)
    font_listPrice = ImageFont.truetype("fonts/Inter-Bold.ttf", 45)
    font_percentage_number = ImageFont.truetype("fonts/GilaBold.ttf", 90)  # Larger font for percentage number
    font_percentage_symbol = ImageFont.truetype("fonts/Gila.ttf", 40)  # Smaller font for '%' and 'OFF'

    # Calculate vertical positions
    list_price_y_position = height // 2 - 120
    price_y_position = height // 2 - 40

    # Draw list price
    list_price_text = f"${listPrice}"
    text_width = font_listPrice.getbbox(list_price_text)[2] - font_listPrice.getbbox(list_price_text)[0]
    x_position = (width - text_width) // 2
    d_blue.text((x_position, list_price_y_position), list_price_text, fill="#FFDE59", font=font_listPrice)
    d_blue.line([(x_position, list_price_y_position + 25), (x_position + text_width, list_price_y_position + 25)], fill="#FFDE59", width=4)

    # Draw price
    price_text = f"${price}"
    text_width = font_price.getbbox(price_text)[2] - font_price.getbbox(price_text)[0]
    x_position = (width - text_width) // 2
    d_blue.text((x_position, price_y_position), price_text, fill="white", font=font_price)

    # Calculate and draw percentage
    if float(listPrice) > float(price):
        discount = float(listPrice) - float(price)
        percentage = round((discount / float(listPrice)) * 100)
        
        # Draw large percentage number
        percentage_text = str(percentage)
        number_width = font_percentage_number.getbbox(percentage_text)[2] - font_percentage_number.getbbox(percentage_text)[0]
        number_height = font_percentage_number.getbbox(percentage_text)[3] - font_percentage_number.getbbox(percentage_text)[1]
        number_x = (width - number_width) // 2 - 40  # Shift left to make room for '%'
        number_y = price_y_position + 80
        d_blue.text((number_x, number_y), percentage_text, fill="#FFDE59", font=font_percentage_number)

        # Draw '%' symbol
        percent_symbol = "%"
        symbol_width = font_percentage_symbol.getbbox(percent_symbol)[2] - font_percentage_symbol.getbbox(percent_symbol)[0]
        symbol_x = number_x + number_width
        symbol_y = number_y + 20
        d_blue.text((symbol_x, symbol_y), percent_symbol, fill="#FFDE59", font=font_percentage_symbol)

        # Draw 'OFF' text
        off_text = "off"
        off_width = font_percentage_symbol.getbbox(off_text)[2] - font_percentage_symbol.getbbox(off_text)[0]
        off_x = symbol_x + (symbol_width - off_width) // 2 + 20
        off_y = symbol_y + font_percentage_symbol.getbbox(percent_symbol)[3] - font_percentage_symbol.getbbox(percent_symbol)[1]
        d_blue.text((off_x, off_y), off_text, fill="#FFDE59", font=font_percentage_symbol)

    return blue_section

def create_image(price, listPrice, image_link):
    width, height = 600, 500
    blue_width = int(0.4 * width)
    image_width = width - blue_width
    img = Image.new('RGB', (width, height), color=(255, 255, 255))
    
    # Load and paste main image
    external_img = load_external_image(image_link, image_width, height)
    if external_img:
        paste_x = 0
        paste_y = (height - external_img.height) // 2
        img.paste(external_img, (paste_x, paste_y))
    else:
        d = ImageDraw.Draw(img)
        d.text((10, 10), "Failed to load image", fill=(255, 0, 0))

    # Load and paste logo
    logo_url = 'https://www.pzdeals.com/cdn/shop/t/71/assets/logo.png?v=70800974703124073071709156649'
    response = requests.get(logo_url)
    logo_img = Image.open(BytesIO(response.content)).convert("RGBA")
    logoWidth = 40
    logoHeight = int((logo_img.height / logo_img.width) * logoWidth)
    logo_img = logo_img.resize((logoWidth, logoHeight))
    img.paste(logo_img, (10, 10), mask=logo_img)

    # Create and paste price section
    blue_section = draw_price_section(blue_width, height, listPrice, price)
    img.paste(blue_section, (image_width, 0))

    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='WEBP')
    img_byte_arr.seek(0)
    return img_byte_arr

@app.route('/generate_image')
def generate_image():
    price = request.args.get('price', '987.99')
    listPrice = request.args.get('listPrice', '15.98')
    image_link = request.args.get('imageLink', 'https://www.pzdeals.com/cdn/shop/files/v-2024-06-09T120851.090_grande.png?v=1717949388')

    img_buffer = create_image(price, listPrice, image_link)
    return send_file(img_buffer, mimetype='image/webp')

if __name__ == '__main__':
    app.run(debug=True)