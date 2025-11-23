"""
Скрипт для создания всех таблиц в базе данных с нуля
Использовать ТОЛЬКО для первоначальной инициализации БД!
Запуск: python init_db.py
"""

import asyncio
from data.model import engine, Base


async def init_database():
    """Создать все таблицы в БД"""
    print("Начало создания таблиц в базе данных...")
    
    async with engine.begin() as conn:
        # Удалить все таблицы (осторожно! удаляет все данные)
        print("⚠️  Удаление существующих таблиц...")
        await conn.run_sync(Base.metadata.drop_all)
        
        # Создать все таблицы заново
        print("✅ Создание таблиц...")
        await conn.run_sync(Base.metadata.create_all)
    
    print("\n" + "="*50)
    print("✅ База данных успешно инициализирована!")
    print("="*50)
    print("\nТеперь выполните:")
    print("1. python seed_data.py  - заполнить тестовыми данными")
    print("2. python main.py       - запустить бота")


if __name__ == "__main__":
    print("="*50)
    print("ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ")
    print("="*50)
    print("⚠️  ВНИМАНИЕ: Это удалит все существующие данные!")
    print()
    
    asyncio.run(init_database())

