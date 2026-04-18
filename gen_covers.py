from PIL import Image, ImageDraw, ImageFont
import math, random

def create_cover(ep_num, title1, title2, title_color, chart_func, cta_text, filename):
    w, h = 1080, 1920
    img = Image.new('RGB', (w, h), (15, 20, 35))
    draw = ImageDraw.Draw(img)
    
    for y in range(h):
        t = y / h
        r = int(15 + t * 20)
        g = int(20 + t * 15)
        b = int(35 + t * 40)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    
    try:
        title_font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 110)
        label_font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 52)
        subtitle_font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 58)
        small_font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 46)
    except:
        title_font = label_font = subtitle_font = small_font = ImageFont.load_default()
    
    draw.rounded_rectangle([380, 130, 700, 210], radius=15, fill=(255, 200, 50))
    draw.text((540, 170), f'EP.{ep_num}/4', fill=(15, 20, 35), font=label_font, anchor='mm')
    
    draw.text((w//2, 310), title1, fill=(255, 255, 255), font=title_font, anchor='mm')
    draw.text((w//2, 440), title2, fill=title_color, font=title_font, anchor='mm')
    
    chart_func(draw, w, h)
    
    draw.text((w//2, 1550), cta_text, fill=(255, 200, 50), font=subtitle_font, anchor='mm')
    draw.text((w//2, 1650), '@AlexTheTrader', fill=(150, 150, 150), font=small_font, anchor='mm')
    
    img.save(filename, 'PNG')
    print(f'{filename} saved!')

def chart_ep2(draw, w, h):
    chart_y, chart_h, chart_w = 650, 600, 800
    chart_x = (w - chart_w) // 2
    draw.rounded_rectangle([chart_x, chart_y, chart_x+chart_w, chart_y+chart_h], 
                           radius=20, fill=(25, 30, 50), outline=(60, 70, 100), width=3)
    random.seed(42)
    candle_w, gap = 22, 32
    start_x = chart_x + 60
    base_y = chart_y + chart_h - 80
    prices = [400, 420, 410, 445, 460, 430, 455, 465, 440, 450, 462, 470, 445, 455]
    for i, price in enumerate(prices):
        x = start_x + i * gap
        open_p = prices[i-1] if i > 0 else 390
        close_p = price
        high = max(open_p, close_p) + random.randint(3, 12)
        low = min(open_p, close_p) - random.randint(3, 12)
        py = lambda p: int(base_y - (p - 350) * 1.3)
        is_green = close_p >= open_p
        color = (0, 200, 100) if is_green else (220, 60, 60)
        mid = x + candle_w // 2
        draw.line([(mid, py(high)), (mid, py(low))], fill=color, width=2)
        top = py(max(open_p, close_p))
        bot = py(min(open_p, close_p))
        draw.rectangle([x, top, x+candle_w, max(bot, top+3)], fill=color)
    res_y = py(465)
    draw.line([(start_x, res_y), (start_x + 13*gap + 20, res_y)], fill=(255, 80, 80), width=4)
    for idx in [4, 7, 11]:
        x = start_x + idx * gap + candle_w // 2
        draw.text((x, res_y - 35), 'X', fill=(255, 80, 80), font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 40), anchor='mm')
    draw.text((start_x + 13*gap + 50, res_y), 'Resistance', fill=(255, 80, 80), font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 38), anchor='lm')
    draw.text((chart_x + 20, res_y), '$920', fill=(255, 80, 80), font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 42), anchor='lm')

def chart_ep3(draw, w, h):
    chart_y, chart_h, chart_w = 650, 600, 800
    chart_x = (w - chart_w) // 2
    draw.rounded_rectangle([chart_x, chart_y, chart_x+chart_w, chart_y+chart_h], 
                           radius=20, fill=(25, 30, 50), outline=(60, 70, 100), width=3)
    random.seed(42)
    candle_w, gap = 22, 32
    start_x = chart_x + 60
    base_y = chart_y + chart_h - 80
    prices = [400, 380, 395, 375, 390, 370, 385, 395, 420, 450, 480, 510, 540, 560]
    for i, price in enumerate(prices):
        x = start_x + i * gap
        open_p = prices[i-1] if i > 0 else 410
        close_p = price
        high = max(open_p, close_p) + random.randint(3, 12)
        low = min(open_p, close_p) - random.randint(3, 12)
        py = lambda p: int(base_y - (p - 300) * 1.3)
        is_green = close_p >= open_p
        color = (0, 200, 100) if is_green else (220, 60, 60)
        mid = x + candle_w // 2
        draw.line([(mid, py(high)), (mid, py(low))], fill=color, width=2)
        top = py(max(open_p, close_p))
        bot = py(min(open_p, close_p))
        draw.rectangle([x, top, x+candle_w, max(bot, top+3)], fill=color)
    sup_y = py(370)
    draw.line([(start_x, sup_y), (start_x + 6*gap, sup_y)], fill=(0, 200, 100), width=4)
    for idx in [1, 3, 5]:
        x = start_x + idx * gap + candle_w // 2
        draw.text((x, sup_y + 35), 'Bounce', fill=(0, 200, 100), font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 28), anchor='mm')
    draw.text((chart_x + 20, sup_y), '$810', fill=(0, 200, 100), font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 42), anchor='lm')
    arrow_x = start_x + 8 * gap
    draw.line([(arrow_x, py(420)), (arrow_x + 80, py(470))], fill=(255, 200, 50), width=5)
    draw.text((arrow_x + 100, py(460)), 'BREAKOUT!', fill=(255, 200, 50), font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 48), anchor='lm')

def chart_ep4(draw, w, h):
    chart_y, chart_h, chart_w = 650, 600, 800
    chart_x = (w - chart_w) // 2
    draw.rounded_rectangle([chart_x, chart_y, chart_x+chart_w, chart_y+chart_h], 
                           radius=20, fill=(25, 30, 50), outline=(60, 70, 100), width=3)
    random.seed(42)
    candle_w, gap = 22, 32
    start_x = chart_x + 60
    base_y = chart_y + chart_h - 80
    prices = [400, 420, 410, 445, 460, 430, 455, 480, 470, 500, 490, 520, 510, 540]
    for i, price in enumerate(prices):
        x = start_x + i * gap
        open_p = prices[i-1] if i > 0 else 390
        close_p = price
        high = max(open_p, close_p) + random.randint(3, 12)
        low = min(open_p, close_p) - random.randint(3, 12)
        py = lambda p: int(base_y - (p - 350) * 1.3)
        is_green = close_p >= open_p
        color = (0, 200, 100) if is_green else (220, 60, 60)
        mid = x + candle_w // 2
        draw.line([(mid, py(high)), (mid, py(low))], fill=color, width=2)
        top = py(max(open_p, close_p))
        bot = py(min(open_p, close_p))
        draw.rectangle([x, top, x+candle_w, max(bot, top+3)], fill=color)
    entry_y = py(460)
    sl_y = py(400)
    tp_y = py(540)
    draw.line([(start_x, entry_y), (start_x + 13*gap + 20, entry_y)], fill=(255, 200, 50), width=3)
    draw.text((chart_x + 20, entry_y), 'BUY', fill=(255, 200, 50), font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 38), anchor='lm')
    draw.line([(start_x, sl_y), (start_x + 13*gap + 20, sl_y)], fill=(220, 60, 60), width=3)
    draw.text((chart_x + 20, sl_y), 'SL', fill=(220, 60, 60), font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 38), anchor='lm')
    draw.line([(start_x, tp_y), (start_x + 13*gap + 20, tp_y)], fill=(0, 200, 100), width=3)
    draw.text((chart_x + 20, tp_y), 'TP', fill=(0, 200, 100), font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 38), anchor='lm')
    draw.rounded_rectangle([chart_x + chart_w - 220, chart_y + 30, chart_x + chart_w - 30, chart_y + 100], 
                           radius=10, fill=(255, 200, 50))
    draw.text((chart_x + chart_w - 125, chart_y + 65), 'R:R = 1:3', fill=(15, 20, 35), 
              font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 36), anchor='mm')

desktop = r'C:\Users\Administrator\Desktop'
create_cover(2, '3x REJECTED', 'at $920', (255, 80, 80), chart_ep2, 'Next: EP.3 When Support BREAKS', f'{desktop}/tiktok_cover_ep2.png')
create_cover(3, 'When Support', 'BREAKS', (0, 200, 100), chart_ep3, 'Final: EP.4 Your Cheat Sheet', f'{desktop}/tiktok_cover_ep3.png')
create_cover(4, 'Your Trading', 'CHEAT SHEET', (255, 200, 50), chart_ep4, 'Follow for more series!', f'{desktop}/tiktok_cover_ep4.png')
print('All covers done!')
