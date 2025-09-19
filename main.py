# main.py - точка входа приложения
"""
Точка входа в приложение Tender Analyzer 2.0
Поддерживает запуск как Streamlit приложения (переходный период)
так и FastAPI сервера (будущее)
"""

import argparse
import sys
import logging
from pathlib import Path

# Добавляем корневую директорию в Python path
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('tender_analyzer.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_streamlit():
    """Запуск Streamlit приложения"""
    import streamlit.web.cli as stcli
    from web.streamlit_app import main
    
    # Настройка Streamlit
    sys.argv = [
        "streamlit", 
        "run", 
        str(ROOT_DIR / "web" / "streamlit_app.py"),
        "--server.port=8501",
        "--server.address=0.0.0.0"
    ]
    
    stcli.main()

def run_fastapi():
    """Запуск FastAPI сервера (в будущем)"""
    import uvicorn
    
    # TODO: Реализовать FastAPI приложение
    print("❌ FastAPI версия пока не реализована")
    print("📌 Используйте --mode streamlit для запуска")
    
    # uvicorn.run(
    #     "web.fastapi_app:app",
    #     host="0.0.0.0",
    #     port=8000,
    #     reload=True
    # )

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="Tender Analyzer 2.0")
    parser.add_argument(
        "--mode",
        choices=["streamlit", "fastapi"],
        default="streamlit",
        help="Режим запуска приложения"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Режим отладки"
    )
    
    args = parser.parse_args()
    
    # Настройка логирования
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"🚀 Запуск Tender Analyzer 2.0 в режиме: {args.mode}")
    
    try:
        if args.mode == "streamlit":
            run_streamlit()
        elif args.mode == "fastapi":
            run_fastapi()
    except KeyboardInterrupt:
        logger.info("👋 Приложение остановлено пользователем")
    except Exception as e:
        logger.error(f"❌ Ошибка запуска приложения: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()