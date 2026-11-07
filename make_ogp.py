"""Generate static/ogp.png (1200x630). Never fails the build."""
import glob
from PIL import Image, ImageDraw, ImageFont
fonts = sorted(glob.glob("/usr/share/fonts/**/*CJK*Bold*", recursive=True)) or sorted(glob.glob("/usr/share/fonts/**/*CJK*", recursive=True))
print("font:", fonts[:1])
def f(size):
    try:
        return ImageFont.truetype(fonts[0], size, index=0)
    except Exception:
        return ImageFont.load_default()
W, H = 1200, 630
im = Image.new("RGB", (W, H), "#f3f5f4"); d = ImageDraw.Draw(im)
d.rectangle([0, 0, 24, H], fill="#c0392b"); d.rectangle([24, 0, 40, H], fill="#b7791f")
d.text((110, 170), "IT朝刊", font=f(150), fill="#1b2420")
d.line([(115, 370), (1080, 370)], fill="#1b2420", width=4)
d.text((115, 380), "セキュリティ × 新技術を毎朝", font=f(52), fill="#0f6b5c")
d.text((115, 460), "専門用語はタップで解説", font=f(40), fill="#5d6b65")
im.save("static/ogp.png", optimize=True)
print("ogp.png written")
