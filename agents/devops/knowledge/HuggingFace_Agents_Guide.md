# Документация по Hugging Face Agents (smolagents)

smolagents — это легковесная библиотека от Hugging Face для создания агентов, которые могут писать код для решения задач или вызывать инструменты через JSON.

## 1. Установка

```bash
pip install smolagents
```

## 2. Основные концепции

Агент состоит из двух ключевых компонентов:
- **Инструменты (Tools):** Функции, которые агент может вызывать (поиск в сети, расчеты, генерация картинок).
- **Модель (LLM):** "Мозг" агента (можно использовать модели через HF Inference API, OpenAI, Anthropic или локальные модели).

## 3. Быстрый старт: Создание CodeAgent

CodeAgent — это самый эффективный тип агента, так как он генерирует Python-код для выполнения цепочки действий.

```python
from smolagents import CodeAgent, DuckDuckGoSearchTool, HfApiModel

# 1. Выбираем модель (например, Qwen или Llama через API)
model = HfApiModel()

# 2. Инициализируем инструмент поиска
search_tool = DuckDuckGoSearchTool()

# 3. Создаем агента
agent = CodeAgent(tools=[search_tool], model=model)

# 4. Запускаем задачу
agent.run("Найди текущий курс биткоина и рассчитай, сколько это будет в евро.")
```

## 4. Создание собственных инструментов

Инструменты создаются с помощью декоратора `@tool`. Обязательно наличие docstring (описания), так как агент использует его для понимания того, когда вызывать функцию.

```python
from smolagents import tool

@tool
def get_weather(location: str) -> str:
    """
    Возвращает текущую погоду для указанного города.
    Args:
        location: Название города на английском.
    """
    return f"В {location} сейчас солнечно, +25°C"

agent = CodeAgent(tools=[get_weather], model=model)
```

## 5. Типы агентов

- **CodeAgent:** Пишет код. Лучше всего подходит для задач, требующих логики, циклов и вычислений.
- **ToolCallingAgent:** Генерирует JSON/текстовые вызовы инструментов. Подходит для простых сценариев "вопрос-ответ".

## 6. Интеграция SeeDream (Изображения) и SeeDance (Видео)

SeeDream и SeeDance — модели от Kwai/Kolors на HuggingFace для генерации изображений и видео.

### SeeDream — генерация изображений:
```python
from smolagents import tool
from huggingface_hub import InferenceClient

@tool
def generate_image_seedream(prompt: str) -> str:
    """
    Генерирует изображение через SeeDream модель.
    Args:
        prompt: Текстовый промпт для генерации изображения.
    Returns:
        Путь к сохраненному изображению.
    """
    client = InferenceClient(token="hf_ВАШ_ТОКЕН")
    image = client.text_to_image(prompt, model="Kwai-Kolors/Kolors")
    image.save("/tmp/seedream_output.png")
    return "/tmp/seedream_output.png"
```

### SeeDance — генерация видео:
```python
@tool
def generate_video_seedance(prompt: str) -> str:
    """
    Генерирует видео через SeeDance модель.
    Args:
        prompt: Текстовый промпт для генерации видео.
    """
    client = InferenceClient(token="hf_ВАШ_ТОКЕН")
    # SeeDance endpoint
    result = client.post(
        json={"inputs": prompt},
        model="Kwai-Kolors/SeeDance"
    )
    return result
```

## 7. Полезные ссылки

- [Официальный репозиторий GitHub](https://github.com/huggingface/smolagents)
- [HuggingFace Kolors](https://huggingface.co/Kwai-Kolors)
- [HF Inference API Docs](https://huggingface.co/docs/api-inference)

## 8. Как использовать HF API ключ

```bash
# Логин через CLI
huggingface-cli login

# Или через переменную окружения
export HF_TOKEN="hf_ваш_токен"
```

---

*Сохранено DevOps агентом AXIS | 2026-02-24*
