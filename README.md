# README.md

# 🏢 Tender Analyzer 2.0

Система анализа государственных закупок с расчетом экономики проектов.

## ✨ Основные возможности

- 🔍 **Поиск тендеров** - поиск по госзакупкам с фильтрацией
- 💰 **Расчет экономики** - анализ прибыльности проектов с учетом команды и рисков
- 📊 **Аналитика** - сравнение с рынком, исторические данные
- 📄 **Отчеты** - экспорт в Excel, PDF с детализацией

## 🏗️ Архитектура

Проект построен на принципах чистой архитектуры:

```
tender_analyzer/
├── 🌐 web/                    # Presentation Layer
│   ├── streamlit_app.py       # Streamlit UI (переходный период)
│   └── fastapi_app.py         # FastAPI REST API (будущее)
├── 🏢 application/            # Application Services  
│   └── services/
│       ├── search_service.py
│       └── economics_service.py
├── 💼 domain/                 # Business Logic
│   ├── entities/
│   │   └── tender.py
│   └── value_objects/
│       └── economics.py
├── 🏗️ infrastructure/         # External Dependencies
│   ├── parsers/
│   │   ├── parser_interface.py
│   │   └── http_parser.py
│   ├── cache/
│   └── database/
└── 🔧 core/                   # Cross-cutting Concerns
    ├── config.py
    └── exceptions.py
```

## 🚀 Быстрый старт

### Установка зависимостей

```bash
pip install -r requirements.txt
```

### Настройка

```bash
# Копируем конфигурацию
cp .env.example .env

# Создаем необходимые директории
make setup-dirs
```

### Запуск

```bash
# Режим разработки (Streamlit)
python main.py --mode streamlit

# Или с помощью Make
make run-dev

# Docker
docker-compose up --build
```

## 💰 Модуль расчета экономики

Ключевая функция приложения - расчет экономики проектов:

### Возможности:
- ✅ Конфигурация команды по ролям и процентам
- ✅ Расчет прибыльности, ROI, маржи
- ✅ Анализ рисков проекта
- ✅ Сравнение с рыночными показателями
- ✅ Шаблоны команд для разных типов проектов
- ✅ Сценарии "что если"

### Пример использования:

```python
from application.services.economics_service import EconomicsService
from domain.value_objects.economics import ProjectConfig, TeamRole, ProjectType
from decimal import Decimal

# Создание конфигурации проекта
config = ProjectConfig(
    project_name="Благоустройство территории",
    total_amount=Decimal("5000000"),
    duration_months=6,
    project_type=ProjectType.LANDSCAPING,
    team={
        "ГИП": TeamRole("ГИП", 0.15, 3000, 80),
        "Архитектор": TeamRole("Архитектор", 0.25, 2500, 120),
        "Инженер": TeamRole("Инженер", 0.16, 2000, 100)
    },
    overhead_costs={
        "office_rent": Decimal("300000"),  # 6 месяцев * 50к
        "software": Decimal("50000")
    },
    taxes={
        "income_tax": 0.20,
        "social": 0.30
    }
)

# Расчет экономики
service = EconomicsService()
result = service.calculate_project_economics(Decimal("5000000"), config)

print(f"Чистая прибыль: {result.net_profit:,.2f} руб.")
print(f"Маржа: {result.profit_margin:.1f}%")
print(f"ROI: {result.roi:.1f}%")
print(f"Уровень риска: {result.risk_level}")
```

## 🔧 Разработка

### Структура конфигурации

Настройки приложения организованы иерархически:

```python
# core/config.py
class AppSettings:
    app_name: str = "Tender Analyzer"
    version: str = "2.0.0"
    
    database: DatabaseSettings
    parser: ParserSettings
    cache: CacheSettings
    files: FileStorageSettings
```

### Парсинг

Заменили Selenium на быстрый HTTP-парсинг:

```python
# infrastructure/parsers/http_parser.py
async with HttpTenderParser() as parser:
    results = await parser.search_tenders(
        query="благоустройство",
        limit=20,
        filters={"price_from": 1000000}
    )
```

### Тестирование

```bash
# Запуск всех тестов
make test

# Только unit тесты
pytest tests/unit/ -v

# С покрытием кода
pytest --cov=. --cov-report=html
```

## 📋 План миграции

### Фаза 1: Рефакторинг (1-2 недели) ✅
- [x] Конфигурационный файл
- [x] Выделение сервисного слоя
- [x] Модуль расчета экономики
- [x] Улучшенные модели данных

### Фаза 2: UI улучшения (1-2 недели) 🔄
- [x] Улучшенный Streamlit с состоянием
- [x] Интерфейс расчета экономики
- [ ] Прогресс-бары и кеширование
- [ ] Визуализация результатов

### Фаза 3: Замена парсинга (2-3 недели) ⏳
- [x] HTTP парсер (замена Selenium)
- [ ] Асинхронность и retry логика
- [ ] База данных SQLite
- [ ] Улучшенная обработка документов

### Фаза 4: Масштабирование (3-4 недели) 📋
- [ ] FastAPI + React фронтенд
- [ ] PostgreSQL + Redis
- [ ] Продвинутая аналитика
- [ ] Полное тестирование

## 🤝 Участие в разработке

1. **Fork репозиторий**
2. **Создайте feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit изменения** (`git commit -m 'Add amazing feature'`)
4. **Push в branch** (`git push origin feature/amazing-feature`)
5. **Откройте Pull Request**

### Стандарты кода

```bash
# Форматирование кода
make format

# Проверка качества
make lint

# Перед commit
pre-commit run --all-files
```

## 📖 Документация API

После запуска FastAPI версии документация будет доступна по адресу:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔐 Безопасность

- ✅ Конфигурация через переменные окружения
- ✅ Rate limiting для парсинга
- ✅ Валидация входных данных
- ⏳ JWT аутентификация (в планах)
- ⏳ HTTPS и CORS (в планах)

## 📊 Мониторинг

- ✅ Структурированное логирование
- ⏳ Prometheus метрики (в планах)
- ⏳ Health checks (в планах)
- ⏳ Error tracking (в планах)

## 🐳 Docker

```bash
# Сборка образа
docker build -t tender-analyzer .

# Запуск с docker-compose
docker-compose up -d

# Просмотр логов
docker-compose logs -f tender-analyzer
```

## 📄 Лицензия

MIT License - подробности в файле [LICENSE](LICENSE)

## 👥 Команда

- **Backend разработка** - Парсинг, бизнес-логика, API
- **Frontend разработка** - UI/UX, визуализация данных
- **DevOps** - Инфраструктура, CI/CD, мониторинг

---

## 🎯 Roadmap

- **Q1 2025**: Базовая функциональность (поиск + экономика)
- **Q2 2025**: FastAPI + React, продвинутая аналитика
- **Q3 2025**: ML для предсказания успешности тендеров
- **Q4 2025**: Мобильное приложение, интеграции

---

**⚡ Tender Analyzer 2.0** - превращаем анализ госзакупок в конкурентное преимущество!