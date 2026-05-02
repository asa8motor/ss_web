#!/usr/bin/env python3
"""
Скачивает все изображения из Figma-файла в 4x качестве.
"""
 
import os
import re
import sys
import time
import requests


# ─── НАСТРОЙКИ ────────────────────────────────────────────────────────────────

TOKEN   = "figd_IUnVlck4LGV9uEKH-Avsw32rIQfuyovwebjsaoT9"   # Figma → Settings → Security → Personal access tokens
FILE_KEY = "6ihJyl6AN5SdftcQ8BwAck"               # из URL: figma.com/file/FILE_KEY/...

SCALE   = 4
FORMAT  = "png"
OUT_DIR = "figma_images"
DELAY   = 2.0
 
# ──────────────────────────────────────────────────────────────────────────────
 
HEADERS = {"X-Figma-Token": TOKEN}
 
 
def get_file_tree(file_key):
    url = f"https://api.figma.com/v1/files/{file_key}"
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    return r.json()
 
 
def find_image_nodes(node, results=None):
    """
    Ищет:
    - ноды типа IMAGE
    - любые ноды с fills типа IMAGE (прямоугольники, фреймы, эллипсы)
    """
    if results is None:
        results = []
 
    ntype = node.get("type", "")
 
    if ntype == "IMAGE":
        results.append({"id": node["id"], "name": node.get("name", node["id"])})
    else:
        for fill in node.get("fills", []):
            if isinstance(fill, dict) and fill.get("type") == "IMAGE":
                results.append({"id": node["id"], "name": node.get("name", node["id"])})
                break
 
    for child in node.get("children", []):
        find_image_nodes(child, results)
 
    return results
 
 
def fetch_image_urls(file_key, node_ids, scale, fmt):
    """Один запрос к Figma API для списка нод."""
    ids_str = ",".join(node_ids)
    url = f"https://api.figma.com/v1/images/{file_key}"
    params = {"ids": ids_str, "scale": scale, "format": fmt}
    r = requests.get(url, headers=HEADERS, params=params)
    r.raise_for_status()
    data = r.json()
    if data.get("err"):
        raise RuntimeError(data["err"])
    return data.get("images", {})
 
 
def get_image_urls_safe(file_key, node_ids, scale, fmt):
    """
    Сначала пробует батч из 50 нод.
    Если 400 — отправляет по одной и пропускает проблемные.
    """
    all_urls = {}
    BATCH = 50
 
    batches = [node_ids[i:i+BATCH] for i in range(0, len(node_ids), BATCH)]
 
    for bi, batch in enumerate(batches, 1):
        print(f"  Батч {bi}/{len(batches)} ({len(batch)} нод)...")
        try:
            urls = fetch_image_urls(file_key, batch, scale, fmt)
            all_urls.update(urls)
            time.sleep(DELAY)
        except requests.HTTPError:
            print(f"  ⚠️  Батч упал, пробуем по одной...")
            for node_id in batch:
                try:
                    urls = fetch_image_urls(file_key, [node_id], scale, fmt)
                    all_urls.update(urls)
                except requests.HTTPError as e:
                    print(f"    ⏭  Пропускаем {node_id}: {e}")
                time.sleep(DELAY)
 
    return all_urls
 
 
def safe_filename(name, node_id):
    clean = re.sub(r'[\\/*?:"<>|]', "_", name).strip()[:80]
    return f"{clean}__{node_id.replace(':', '-')}"
 
 
def download_images(url_map, nodes_meta, fmt, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    total = len(url_map)
    ok = 0
 
    for i, (node_id, img_url) in enumerate(url_map.items(), 1):
        if not img_url:
            print(f"  [{i}/{total}] ⚠️  нет URL для {node_id}")
            continue
 
        name = nodes_meta.get(node_id, node_id)
        filename = f"{safe_filename(name, node_id)}.{fmt}"
        filepath = os.path.join(out_dir, filename)
 
        try:
            resp = requests.get(img_url, timeout=30)
            resp.raise_for_status()
            with open(filepath, "wb") as f:
                f.write(resp.content)
            size_kb = len(resp.content) / 1024
            print(f"  [{i}/{total}] ✅ {filename} ({size_kb:.0f} KB)")
            ok += 1
        except Exception as e:
            print(f"  [{i}/{total}] ❌ {filename}: {e}")
 
        time.sleep(DELAY)
 
    return ok
 
 
def main():
    if TOKEN == "ВАШ_PERSONAL_ACCESS_TOKEN" or FILE_KEY == "ВАШ_FILE_KEY":
        print("❌ Заполни TOKEN и FILE_KEY в начале скрипта!")
        sys.exit(1)
 
    print(f"📄 Получаем структуру файла {FILE_KEY}...")
    try:
        tree = get_file_tree(FILE_KEY)
    except requests.HTTPError as e:
        print(f"❌ Ошибка доступа к файлу: {e}")
        sys.exit(1)
 
    print("🔍 Ищем ноды с изображениями...")
    nodes = find_image_nodes(tree.get("document", {}))
 
    if not nodes:
        print("🤷 Изображений не найдено.")
        sys.exit(0)
 
    print(f"🖼  Найдено: {len(nodes)} нод")
 
    nodes_meta = {n["id"]: n["name"] for n in nodes}
    node_ids   = list(nodes_meta.keys())
 
    print(f"📡 Запрашиваем URL у Figma...")
    all_urls = get_image_urls_safe(FILE_KEY, node_ids, SCALE, FORMAT)
 
    valid_urls = {k: v for k, v in all_urls.items() if v}
    print(f"\n⬇️  Скачиваем {len(valid_urls)} изображений в «{OUT_DIR}»...")
    downloaded = download_images(valid_urls, nodes_meta, FORMAT, OUT_DIR)
 
    print(f"\n✅ Готово! Скачано {downloaded} из {len(valid_urls)}.")
    print(f"📁 {os.path.abspath(OUT_DIR)}")
 
 
if __name__ == "__main__":
    main()
 