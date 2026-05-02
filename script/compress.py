import os
from PIL import Image

def compress_images(input_folder, output_folder, target_kb=300, max_width=1920):
    # Переводим килобайты в байты
    target_bytes = target_kb * 1024
    
    # Создаем папку для готовых картинок, если её нет
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        # Ищем только изображения
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            continue
            
        input_path = os.path.join(input_folder, filename)
        # Меняем расширение на .webp для лучшего сжатия
        output_filename = os.path.splitext(filename)[0] + '.webp'
        output_path = os.path.join(output_folder, output_filename)

        try:
            with Image.open(input_path) as img:
                # WebP отлично поддерживает прозрачность (RGBA), 
                # но другие экзотические форматы лучше перевести в RGB
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA") if "A" in img.mode else img.convert("RGB")

                # Ограничиваем максимальную ширину для полноэкранных изображений
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_height = int(img.height * ratio)
                    img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

                # Динамический подбор качества
                quality = 95
                while True:
                    # Сохраняем во временный файл
                    img.save(output_path, 'WEBP', quality=quality)
                    file_size = os.path.getsize(output_path)
                    
                    # Если уложились в лимит или качество уже на минимуме — останавливаемся
                    if file_size <= target_bytes or quality <= 10:
                        break
                    
                    # Иначе снижаем качество на шаг и пробуем снова
                    quality -= 5 
                    
            print(f"✅ Готово: {output_filename} ({file_size / 1024:.1f} КБ, качество: {quality})")
            
        except Exception as e:
            print(f"❌ Ошибка с файлом {filename}: {e}")

# Запуск скрипта
# 1. Создай папку 'input_images' и закинь туда свои 50 исходников
# 2. Скрипт сохранит сжатые версии в папку 'output_portfolio'
compress_images(
    '/Users/asa8motor/Desktop/Projects/ss_website/script/input_images', 
    '/Users/asa8motor/Desktop/Projects/ss_website/script/output', 
    target_kb=300
)