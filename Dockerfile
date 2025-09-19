# Dockerfile - для контейнеризации
FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание директорий для данных
RUN mkdir -p data/documents data/reports data/exports

# Переменные окружения
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:///./data/tender_analyzer.db

# Открываем порты
EXPOSE 8501 8000

# Команда по умолчанию
CMD ["python", "main.py", "--mode", "streamlit"]