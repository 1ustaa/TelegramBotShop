"""
Скрипт для проверки и применения миграции вариаций
"""
import asyncio
from sqlalchemy import text, inspect
from data.model import AsyncSessionLocal, engine

async def check_and_migrate():
    async with AsyncSessionLocal() as session:
        # Проверяем текущую версию миграции
        try:
            result = await session.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar()
            print(f"Текущая версия миграции: {current_version}")
        except Exception as e:
            print(f"Ошибка получения версии миграции: {e}")
        
        # Проверяем структуру таблицы products
        async with engine.begin() as conn:
            def check_columns(conn):
                inspector = inspect(conn)
                columns = inspector.get_columns('products')
                column_names = [col['name'] for col in columns]
                print(f"\nКолонки таблицы products:")
                for col_name in column_names:
                    print(f"  - {col_name}")
                
                if 'variation_id' in column_names:
                    print("\n✓ Колонка variation_id существует")
                else:
                    print("\n✗ Колонка variation_id НЕ существует")
                
                if 'variation' in column_names:
                    print("✗ Старая колонка variation ещё существует")
                else:
                    print("✓ Старая колонка variation удалена")
                
                # Проверяем наличие таблицы variations
                tables = inspector.get_table_names()
                if 'variations' in tables:
                    print("✓ Таблица variations существует")
                else:
                    print("✗ Таблица variations НЕ существует")
            
            await conn.run_sync(check_columns)

if __name__ == "__main__":
    asyncio.run(check_and_migrate())

