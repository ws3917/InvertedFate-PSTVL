import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# 构建下载链接模板
url_template = "https://www.invertedfate.com/images/pages/part_{}/page_{}.png"


# 下载单页图片，判断文件大小大于 100KB 跳过下载
def download_image(chapter, page):
    url = url_template.format(chapter, page)
    folder = f"Ch{chapter}"
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"page_{page}.png")

    # 如果文件已存在就跳过
    if os.path.exists(filename) or os.path.exists(filename.replace(".png", ".gif")):
        # print(f"✅ 已存在: Ch{chapter}/page_{page}.png")
        return True

    try:
        response = requests.get(url, timeout=10, stream=True)

        # 判断文件大小：如果文件大小大于 100KB 跳过
        content_length = response.headers.get("Content-Length")
        if not content_length:
            print(f"⚠️ 文件大小大于100KB，跳过: Ch{chapter}/page_{page}.png")
            return False

        if response.status_code == 404:
            print(f"❌ 404: Ch{chapter}/page_{page}.png")
            return False

        # 如果下载的文件正常，保存文件
        response.raise_for_status()
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"📥 成功下载: Ch{chapter}/page_{page}.png")
        return True
    except Exception as e:
        print(f"⚠️ 下载失败: Ch{chapter}/page_{page}.png 错误: {e}")
        return False


# 下载整章
def download_chapter(chapter, max_pages=500):
    print(f"📘 开始下载第 {chapter} 章")
    for page in range(1, max_pages + 1):
        success = download_image(chapter, page)
        if not success:
            continue
    print(f"✅ 完成第 {chapter} 章\n")


# 多线程并行章节下载
def download_all_chapters(start_ch=1, end_ch=66, max_workers=100):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = (
            [
                executor.submit(download_chapter, f"{ch}")
                for ch in range(start_ch, end_ch + 1)
            ]
            + [
                executor.submit(download_chapter, f"{ch}A")
                for ch in range(start_ch, end_ch + 1)
            ]
            + [
                executor.submit(download_chapter, f"{ch}B")
                for ch in range(start_ch, end_ch + 1)
            ]
            + [
                executor.submit(download_chapter, f"{ch}C")
                for ch in range(start_ch, end_ch + 1)
            ]
            + [
                executor.submit(download_chapter, f"Bonus{ch}")
                for ch in range(start_ch, 10)
            ]
        )
        for _ in as_completed(futures):
            pass  # 你可以在这里做进度统计等


# 启动下载
download_all_chapters()
