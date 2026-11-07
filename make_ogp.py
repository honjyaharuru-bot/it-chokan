"""Generate static/ogp.png (1200x630) for link cards. Needs Pillow and fonts-noto-cjk."""
from PIL import Image, ImageDraw, ImageFont
W, H = 1200, 630
im = Image.new("RGB", (W, H), "#f3f5f4"); d = ImageDraw.Draw(im)
d.rectangle([0, 0, 24, H], fill="#c0392b"); d.rectangle([24, 0, 40, H], fill="#b7791f")
f = lambda s, w="Bold": ImageFont.truetype(f"/usr/share/fonts/opentype/noto/NotoSansCJK-{w}.ttc", s, index=0)
d.text((110, 170), "IT朝刊", font=f(150, "Black"), fill="#1b2420")
d.line([(115, 370), (1080, 370)], fill="#1b2420", width=4)
d.text((115, 380), "セキュリティ × 新技術を毎朝", font=f(52), fill="#0f6b5c")
d.text((115, 460), "専門用語はタップで解説", font=f(40, "Regular"), fill="#5d6b65")
im.convert("P", palette=Image.ADAPTIVE, colors=16).save("static/ogp.png", optimize=True)
print("ogp.png written")
