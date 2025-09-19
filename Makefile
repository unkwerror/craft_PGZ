# Makefile - автоматизация задач разработки
.PHONY: install run-dev run-prod test lint format clean help

# Помощь
help:
	@echo "Tender Analyzer 2.0 - Команды разработки"
	@echo ""
	@echo "install      - Установить зависимости"
	@echo "run-dev      - Запустить в режиме разработки (Streamlit)"
	@echo "run-prod     - Запустить production версию"
	@echo "test         - Запустить тесты"
	@echo "lint         - Проверить код линтерами"
	@echo "format       - Форматировать код"
	@echo "clean        - Очистить временные файлы"

# Установка зависимостей
install:
	pip install -r requirements.txt
	pre-commit install

# Разработка
run-dev:
	python main.py --mode streamlit --debug

# Production
run-prod:
	docker-compose up --build

# Тестирование
test:
	pytest tests/ -v --cov=.

# Линтеры
lint:
	flake8 .
	mypy .
	black --check .
	isort --check-only .

# Форматирование
format:
	black .
	isort .

# Очистка
clean:
	find . -type d -name __pycache__ -delete
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/

# Создание структуры папок
setup-dirs:
	mkdir -p data/documents
	mkdir -p data/reports  
	mkdir -p data/exports
	mkdir -p logs
	mkdir -p tests/unit
	mkdir -p tests/integration