"""
watermark.py — накладывает текстовый водяной знак на фото товаров,
а видео (mov/mp4/avi и др.) конвертирует в браузеро-совместимый MP4
(многие видео с айфона в формате .MOV не проигрываются в браузере
как есть — нужно перекодировать в H.264/AAC .mp4).

СТРУКТУРА ПАПОК (уже создана в проекте):

my-shop/
├── content/
│   ├── raw/            ← сюда кладёшь ИСХОДНЫЕ фото и видео товара
│   ├── watermarked/     ← сюда скрипт складывает ГОТОВЫЙ результат
│   └── watermark.py     ← этот файл, запускается отсюда
├── index.html
├── catalog.html
├── product.html
└── assets/

КАК ПОЛЬЗОВАТЬСЯ:
1. Кидаешь фото/видео нового товара в content/raw/
   (можно называть как угодно, например: neverfull-1.jpg, neverfull-2.jpg,
   neverfull-3.jpg, neverfull.mov)
2. Заходишь в папку content и запускаешь:
       python3 watermark.py
3. В content/watermarked/ появятся:
   - фото — уже со знаком
   - видео — сконвертированные в .mp4 (даже если исходник был .mov —
     на выходе всегда будет тот же файл с расширением .mp4)
4. Готовые файлы уже лежат там, откуда их берёт сайт (content/watermarked/) —
   никуда переносить не нужно. Просто присылаешь мне имена файлов и
   данные товара, и я допишу products.js.

ТРЕБОВАНИЯ:
- Pillow (для фото): pip install Pillow
- ffmpeg (для видео): без него видео будут просто скопированы БЕЗ
  конвертации, и .mov может не заработать в браузере. Поставить на
  Windows: открыть командную строку и выполнить
      winget install ffmpeg
  затем перезапустить командную строку/компьютер, чтобы команда
  ffmpeg стала доступна.
"""

import os
import shutil
import subprocess
from PIL import Image, ImageDraw, ImageFont

# ================== НАСТРОЙКИ — меняй под себя ==================
INPUT_DIR = "raw"
OUTPUT_DIR = "watermarked"
WATERMARK_TEXT = "via.accessories"
FONT_SIZE_RATIO = 0.07
MARGIN_RATIO = 0.03
OPACITY = 110
TEXT_COLOR = (255, 255, 255)
POSITION = "upper-center"   # bottom-right / bottom-left / top-right / top-left / upper-center
# ==================================================================

IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")
VIDEO_EXT = (".mp4", ".mov", ".webm", ".mkv")

# Пробуем найти жирный шрифт в системе — по очереди Windows, Mac, Linux.
# Если ни один не найдётся, используется встроенный шрифт Pillow (менее красивый,
# но скрипт всё равно отработает, а не упадёт с ошибкой).
FONT_CANDIDATES = [
    # Шрифт Champignon — если установлен на компьютере (см. инструкцию выше
    # в этом файле / в чате), будет использован в первую очередь.
    "Champignon.otf",
    "Champignon Regular.otf",
    "Champignon.ttf",
    "C:/Windows/Fonts/Champignon.otf",
    "C:/Windows/Fonts/Champignon Regular.otf",
    "C:/Windows/Fonts/Champignon.ttf",
    "C:/Program Files/champignon/Champignon.otf",                     # если шрифт лежит тут без установки
    "C:/Program Files/champignon/champignonaltswash.ttf",
    "/Library/Fonts/Champignon.otf",                                  # Mac
    "/Users/Shared/Fonts/Champignon.otf",
    # Изящные курсивные (не жирные, тонкие) шрифты — запасной вариант,
    # если Champignon не установлен
    "GARAIT.TTF",                                                     # Windows (Garamond Italic)
    "C:/Windows/Fonts/GARAIT.TTF",
    "georgiai.ttf",                                                   # Windows (Georgia Italic)
    "C:/Windows/Fonts/georgiai.ttf",
    "timesi.ttf",                                                     # Windows (Times New Roman Italic)
    "C:/Windows/Fonts/timesi.ttf",
    "/System/Library/Fonts/Supplemental/Big Caslon Medium.ttf",       # Mac
    "/System/Library/Fonts/Supplemental/Didot.ttc",                   # Mac
    "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf",  # Linux
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
    # Если ни одного из этих не нашлось — жирный курсивный (как было раньше)
    "SCRIPTBL.TTF",                                                  # Windows (Script MT Bold)
    "C:/Windows/Fonts/SCRIPTBL.TTF",
    "MTCORSVA.TTF",                                                  # Windows (Monotype Corsiva)
    "C:/Windows/Fonts/MTCORSVA.TTF",
    "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrechorus-mediumitalic.otf",  # Linux
    # Совсем крайний случай — обычный жирный (не сломается)
    "arialbd.ttf",                                                  # Windows (Arial Bold)
    "Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",            # Mac
    "/System/Library/Fonts/Helvetica.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",         # Linux
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]


def load_font(size):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    print("⚠ Не нашёл системный шрифт, использую встроенный (текст будет проще).")
    return ImageFont.load_default(size=size)


def add_watermark(image_path, output_path):
    base = Image.open(image_path).convert("RGBA")
    width, height = base.size

    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(12, int(width * FONT_SIZE_RATIO))
    font = load_font(font_size)

    bbox = draw.textbbox((0, 0), WATERMARK_TEXT, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    margin = int(width * MARGIN_RATIO)

    if POSITION == "bottom-right":
        x, y = width - text_w - margin, height - text_h - margin
    elif POSITION == "bottom-left":
        x, y = margin, height - text_h - margin
    elif POSITION == "top-right":
        x, y = width - text_w - margin, margin
    elif POSITION == "upper-center":
        x, y = (width - text_w) / 2, height * 0.42 - text_h / 2
    else:
        x, y = margin, margin

    draw.text((x, y), WATERMARK_TEXT, font=font, fill=(*TEXT_COLOR, OPACITY))

    result = Image.alpha_composite(base, overlay).convert("RGB")
    result.save(output_path, quality=92)


def has_ffmpeg():
    return shutil.which("ffmpeg") is not None


def convert_video(input_path, output_path):
    """Перекодирует видео в MP4 (H.264 + AAC) — формат, который проигрывается
    в любом браузере, независимо от того, чем было снято исходное видео."""
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def main():
    if not os.path.isdir(INPUT_DIR):
        print(f'Папка "{INPUT_DIR}" не найдена. Убедись, что запускаешь скрипт из папки content/.')
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    files = os.listdir(INPUT_DIR)
    images = [f for f in files if f.lower().endswith(IMAGE_EXT)]
    videos = [f for f in files if f.lower().endswith(VIDEO_EXT)]

    if not images and not videos:
        print(f'В папке "{INPUT_DIR}" не найдено фото или видео.')
        return

    for name in images:
        add_watermark(os.path.join(INPUT_DIR, name), os.path.join(OUTPUT_DIR, name))
        print(f"✓ фото со знаком: {name}")

    ffmpeg_ok = has_ffmpeg()
    if videos and not ffmpeg_ok:
        print()
        print("⚠ ffmpeg не найден на компьютере — видео будут скопированы БЕЗ конвертации.")
        print("  Если исходник .mov (например, с айфона), он может не заработать в браузере.")
        print("  Чтобы это исправить: открой командную строку и выполни -> winget install ffmpeg")
        print("  Затем перезапусти командную строку и запусти скрипт заново.")
        print()

    for name in videos:
        in_path = os.path.join(INPUT_DIR, name)
        base, _ext = os.path.splitext(name)
        if ffmpeg_ok:
            out_name = base + ".mp4"
            out_path = os.path.join(OUTPUT_DIR, out_name)
            try:
                convert_video(in_path, out_path)
                print(f"✓ видео сконвертировано в MP4: {out_name}")
            except subprocess.CalledProcessError:
                shutil.copy2(in_path, os.path.join(OUTPUT_DIR, name))
                print(f"✗ не удалось сконвертировать {name}, скопировано как есть (может не заработать в браузере)")
        else:
            shutil.copy2(in_path, os.path.join(OUTPUT_DIR, name))
            print(f"→ видео скопировано без конвертации: {name}")

    print(f"\nГотово: {len(images)} фото обработано, {len(videos)} видео обработано.")
    print(f"Результат в папке '{OUTPUT_DIR}'.")


if __name__ == "__main__":
    main()
