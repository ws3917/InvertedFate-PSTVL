import os
from PIL import Image
import imageio

COMIC_DIR = "comic/Ch39"


def get_last_frame_gif(path):
    gif = Image.open(path)
    try:
        while True:
            gif.seek(gif.tell() + 1)
    except EOFError:
        return gif.convert("RGB")


def load_image(path):
    if path.lower().endswith(".gif"):
        return get_last_frame_gif(path)
    return Image.open(path).convert("RGB")


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


def process_image(path):
    img = load_image(path)
    result = {"file": os.path.basename(path)}

    if is_battle_type(img):
        result["type"] = "战斗类"
        result["战斗文本框"] = "有" if has_battle_textbox(img, 250) else "无"
    else:
        result["type"] = "非战斗类"
        top = has_textbox(img, 10)
        bottom = has_textbox(img, 320)

        if not top and not bottom:
            result["文本框位置"] = "无文本框"
        elif top:
            result["文本框位置"] = "上方"
            result["头像"] = "有" if not check_avatar_absent(img, 60, 100) else "无"
        elif bottom:
            result["文本框位置"] = "下方"
            result["头像"] = "有" if not check_avatar_absent(img, 370, 410) else "无"

    return result


def main():
    for file in os.listdir(COMIC_DIR):
        if file.lower().endswith((".png", ".gif")):
            path = os.path.join(COMIC_DIR, file)
            result = process_image(path)
            print(result)


if __name__ == "__main__":
    main()
