#!/usr/bin/env python3
import urllib.request
import urllib.error
import json
import base64
import sys
import os
import re
import argparse

# Скрипт для Шкета: Генерация изображений через OpenAI Images API

# OpenAI API Key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()

if not OPENAI_API_KEY:
    print("ОШИБКА: OPENAI_API_KEY не найден", file=sys.stderr)
    sys.exit(1)

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "image"

def generate_image(prompt, output_file="post_image.jpg", model="dall-e-3", size="1024x1792", quality="high", style="vivid", background="auto", output_format="png"):
    """
    Генерирует изображение через OpenAI Images API
    
    Модели:
    - dall-e-3: Лучшее качество для киберпанк-стиля
    - gpt-image-1.5: Новая модель для генерации изображений
    - gpt-image-1-mini: Быстрая и дешевая модель
    
    Размеры:
    - DALL-E 3: 1024x1024, 1792x1024, 1024x1792
    - GPT-image: 1024x1024, 1536x1024, 1024x1536
    
    Качество:
    - DALL-E 3: hd, standard
    - GPT-image: high, medium, low
    
    Стиль (только DALL-E 3): vivid, natural
    """
    
    # OpenAI Images API endpoint
    url = "https://api.openai.com/v1/images/generations"
    
    # Формируем промпт с киберпанк-стилем
    full_prompt = f"{prompt} (High-quality cyberpunk illustration, neon lights, dark atmosphere, futuristic digital art style, 16:9 aspect ratio, high detail)"
    
    # Базовые параметры
    payload = {
        "model": model,
        "prompt": full_prompt,
        "n": 1,
        "size": size
    }
    
    # Добавляем параметры для DALL-E 3
    if model == "dall-e-3":
        payload["quality"] = quality
        payload["style"] = style
    
    # Добавляем параметры для GPT-image моделей
    elif model.startswith("gpt-image"):
        payload["quality"] = quality
        if background:
            payload["background"] = background
        if output_format:
            payload["output_format"] = output_format
    
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"DEBUG: Response keys: {list(result.keys())}")
            
            if "data" in result and len(result["data"]) > 0:
                image_data = result["data"][0]
                
                # Проверяем разные форматы ответа
                if "url" in image_data:
                    image_url = image_data["url"]
                    print(f"✅ УСПЕХ: Картинка создана!")
                    print(f"URL: {image_url}")
                    
                    # Скачиваем изображение
                    try:
                        urllib.request.urlretrieve(image_url, output_file)
                        print(f"✅ Картинка сохранена в {output_file}")
                        return image_url
                    except Exception as e:
                        print(f"❌ Ошибка скачивания: {str(e)}", file=sys.stderr)
                        return None
                
                elif "b64_json" in image_data:
                    img_b64 = image_data["b64_json"]
                    print(f"✅ УСПЕХ: Картинка получена (base64)!")
                    
                    try:
                        with open(output_file, "wb") as f:
                            f.write(base64.b64decode(img_b64))
                        print(f"✅ Картинка сохранена в {output_file}")
                        return output_file
                    except Exception as e:
                        print(f"❌ Ошибка сохранения: {str(e)}", file=sys.stderr)
                        return None
                
                else:
                    print(f"DEBUG: Image data keys: {list(image_data.keys())}")
            else:
                print(f"❌ Ошибка: API не вернул изображений. Ответ: {json.dumps(result, indent=2)[:500]}", file=sys.stderr)
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8', errors='replace')
        print(f"❌ HTTP Ошибка {e.code}: {error_body[:1000]}", file=sys.stderr)
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {str(e)}", file=sys.stderr)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Генерация изображений через OpenAI Images API для Шкета")
    ap.add_argument("prompt", help="Промпт для генерации изображения")
    ap.add_argument("output", nargs="?", default="post_image.jpg", help="Имя выходного файла")
    ap.add_argument("--model", default="dall-e-3", help="Модель: dall-e-3, gpt-image-1.5, gpt-image-1-mini")
    ap.add_argument("--size", default="1792x1024", help="Размер: 1024x1024, 1792x1024, 1024x1792 (dall-e-3) или 1024x1024, 1536x1024, 1024x1536 (gpt-image)")
    ap.add_argument("--quality", default="high", help="Качество: hd, standard (dall-e-3) или high, medium, low (gpt-image)")
    ap.add_argument("--style", default="vivid", help="Стиль: vivid или natural (только для dall-e-3)")
    ap.add_argument("--background", default="auto", help="Прозрачность фона: transparent, opaque, auto (только для gpt-image)")
    ap.add_argument("--output-format", default="png", help="Формат: png, jpeg, webp (только для gpt-image)")
    
    args = ap.parse_args()
    
    generate_image(
        args.prompt,
        args.output,
        args.model,
        args.size,
        args.quality,
        args.style,
        args.background,
        args.output_format
    )
