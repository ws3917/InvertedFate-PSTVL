import os
import json, re
from PIL import Image
import easyocr
import numpy as np
import pytesseract

from collections import OrderedDict
from paddleocr import PaddleOCR

COMIC_ROOT = "comic"
TEXT_OUTPUT_DIR = "text2"

reader = easyocr.Reader(["en"], gpu=True)


def get_last_frame_gif(path):
    gif = Image.open(path)
    try:
        while True:
            gif.seek(gif.tell() + 1)
    except EOFError:
        return gif.convert("RGB")


def load_image(path):
    return (
        get_last_frame_gif(path)
        if path.lower().endswith(".gif")
        else Image.open(path).convert("RGB")
    )


def get_color(img, x, y):
    return img.getpixel((x, y))


def is_color(c, hex_code):
    rgb = tuple(int(hex_code[i : i + 2], 16) for i in (1, 3, 5))
    return c == rgb


def check_diag(img, x1, y1, x2, y2, color_hex):
    return is_color(get_color(img, x1, y1), color_hex) and is_color(
        get_color(img, x2, y2), color_hex
    )


def is_battle_type(img):
    pts = [(32, 473), (185, 432), (454, 473), (609, 432)]
    return all(
        is_color(get_color(img, x, y), "#ff7f27")
        or is_color(get_color(img, x, y), "#ffff00")
        for x, y in pts
    )


def has_textbox(img, base_y_offset):
    return (
        check_diag(img, 32, base_y_offset, 37, base_y_offset + 5, "#ffffff")
        and check_diag(
            img, 604, base_y_offset + 146, 609, base_y_offset + 151, "#ffffff"
        )
        and check_diag(img, 38, base_y_offset + 6, 42, base_y_offset + 10, "#000000")
    )


def has_battle_textbox(img, base_y_offset):
    return (
        check_diag(img, 32, base_y_offset, 36, base_y_offset + 4, "#ffffff")
        and check_diag(
            img, 602, base_y_offset + 135, 606, base_y_offset + 139, "#ffffff"
        )
        and check_diag(img, 37, base_y_offset + 5, 41, base_y_offset + 9, "#000000")
    )


def check_avatar_absent(img, y1, y2):
    def line_black(y):
        for x in range(60, 145):
            if get_color(img, x, y) != (0, 0, 0):
                return False
        return True

    return line_black(y1) and line_black(y2)


def crop_textbox(img, is_battle, has_avatar, base_y_offset):
    x0 = 160 if has_avatar else (39 if is_battle else 40)
    y0 = base_y_offset + (7 if is_battle else 8)
    y1 = base_y_offset + (132 if is_battle else 143)
    x1 = 600 if is_battle else 602
    return img.crop((x0, y0, x1, y1))


def ocr_text(img_region):
    np_img = np.array(img_region)
    result = reader.readtext(np_img, detail=0)
    return " ".join(result).strip()


# ocr = PaddleOCR(use_angle_cls=True, lang="en")


# def ocr_text(img_region):
#     result = ocr.ocr(np.array(img_region))
#     if result and result[0]:
#         return " ".join([line[1][0] for line in result[0]]).strip()
#     return ""


# def ocr_text(img_region):
#     text = pytesseract.image_to_string(img_region, config="--psm 6")
#     return text.strip().replace("=", "*")


def describe_result(file, pos, avatar, battle_type):
    return f"{file}-{pos}{avatar}{battle_type}"


def process_image(path):
    img = load_image(path)
    file = os.path.basename(path)
    entry = None

    if is_battle_type(img):
        has_txt = has_battle_textbox(img, 250)
        if has_txt:
            textbox_img = crop_textbox(
                img, is_battle=True, has_avatar=False, base_y_offset=250
            )
            text = ocr_text(textbox_img)
            if text:
                key = describe_result(file, "战斗文本框", "无头像", "战斗")
                entry = {key: text}
    else:
        top = has_textbox(img, 10)
        bottom = has_textbox(img, 320)
        if top:
            avatar_absent = check_avatar_absent(img, 60, 100)
            textbox_img = crop_textbox(
                img, is_battle=False, has_avatar=not avatar_absent, base_y_offset=10
            )
            text = ocr_text(textbox_img)
            if text:
                key = describe_result(
                    file,
                    "顶部文本框",
                    "无头像" if avatar_absent else "有头像",
                    "非战斗",
                )
                entry = {key: text}
        elif bottom:
            avatar_absent = check_avatar_absent(img, 370, 410)
            textbox_img = crop_textbox(
                img, is_battle=False, has_avatar=not avatar_absent, base_y_offset=320
            )
            text = ocr_text(textbox_img)
            if text:
                key = describe_result(
                    file,
                    "底部文本框",
                    "无头像" if avatar_absent else "有头像",
                    "非战斗",
                )
                entry = {key: text}

    return entry


def main():
    os.makedirs(TEXT_OUTPUT_DIR, exist_ok=True)

    for root, dirs, files in os.walk(COMIC_ROOT):
        if os.path.basename(root).startswith("Ch"):
            chapter = os.path.basename(root)
            output = {}
            for file in sorted(files):
                if file.lower().endswith((".png", ".gif")):
                    path = os.path.join(root, file)
                    entry = process_image(path)
                    if entry:
                        output.update(entry)

            def extract_number(s):
                match = re.search(r"(\d+)", s)
                return int(match.group(1)) if match else float("inf")

            if output:
                sorted_output = OrderedDict(
                    sorted(output.items(), key=lambda x: extract_number(x[0]))
                )
                if not os.path.exists(os.path.join(TEXT_OUTPUT_DIR, f"{chapter}")):
                    os.makedirs(os.path.join(TEXT_OUTPUT_DIR, f"{chapter}"))
                with open(
                    os.path.join(TEXT_OUTPUT_DIR, f"{chapter}/OCR1.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    json.dump(sorted_output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
