import os
import json

# 要合并的根目录
root_dir = "text"
# 合并后的总数据
merged_data = {}

# 遍历所有子文件夹


# 处理 OCR1.json 到 OCR3.json
for i in range(1, 4):
    for chapter_name in os.listdir(root_dir):
        chapter_path = os.path.join(root_dir, chapter_name)
        if not os.path.isdir(chapter_path) or not chapter_name.startswith("Ch"):
            continue  # 跳过非章节目录
        json_path = os.path.join(chapter_path, f"OCR{i}.json")
        if not os.path.exists(json_path):
            continue

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 追加章节前缀到键名
        for key, value in data.items():
            new_key = f"{chapter_name}-{key}"
            merged_data[new_key] = value

    # 保存合并结果
    output_path = os.path.join(f"strings/OCR{i}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)

    print(f"合并完成，共 {len(merged_data)} 条记录，输出文件：{output_path}")
