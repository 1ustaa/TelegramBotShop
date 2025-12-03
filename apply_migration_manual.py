"""
Ручное применение миграции для вариаций
"""
import asyncio
from sqlalchemy import text
from data.model import AsyncSessionLocal

async def apply_migration():
    async with AsyncSessionLocal() as session:
        try:
            # 1. Создаем таблицу variations если её нет
            await session.execute(text("""
                CREATE TABLE IF NOT EXISTS variations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(200) NOT NULL UNIQUE
                )
            """))
            print("✓ Таблица variations создана")
            
            # 2. Проверяем наличие старого поля variation
            check_column = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='variation'
            """))
            has_old_variation = check_column.scalar() is not None
            
            check_new_column = await session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='products' AND column_name='variation_id'
            """))
            has_new_variation_id = check_new_column.scalar() is not None
            
            if has_old_variation and not has_new_variation_id:
                print("Начинаю миграцию данных...")
                
                # 3. Извлекаем уникальные вариации
                result = await session.execute(text("""
                    SELECT DISTINCT variation 
                    FROM products 
                    WHERE variation IS NOT NULL AND variation != ''
                """))
                unique_variations = [row[0] for row in result]
                print(f"Найдено {len(unique_variations)} уникальных вариаций")
                
                # 4. Вставляем их в таблицу variations
                for variation_name in unique_variations:
                    await session.execute(
                        text("INSERT INTO variations (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"),
                        {"name": variation_name}
                    )
                print(f"✓ Добавлено {len(unique_variations)} вариаций")
                
                # 5. Добавляем новый столбец variation_id
                await session.execute(text("""
                    ALTER TABLE products 
                    ADD COLUMN IF NOT EXISTS variation_id INTEGER
                """))
                print("✓ Добавлен столбец variation_id")
                
                # 6. Создаем внешний ключ
                await session.execute(text("""
                    ALTER TABLE products 
                    ADD CONSTRAINT fk_products_variation_id 
                    FOREIGN KEY (variation_id) REFERENCES variations(id)
                """))
                print("✓ Создан внешний ключ")
                
                # 7. Мигрируем данные
                for variation_name in unique_variations:
                    await session.execute(text("""
                        UPDATE products 
                        SET variation_id = (SELECT id FROM variations WHERE name = :vname)
                        WHERE variation = :vname
                    """), {"vname": variation_name})
                print("✓ Данные мигрированы")
                
                # 8. Удаляем старый constraint
                try:
                    await session.execute(text("""
                        ALTER TABLE products 
                        DROP CONSTRAINT IF EXISTS uq_product_combination
                    """))
                    print("✓ Старый constraint удален")
                except Exception as e:
                    print(f"Предупреждение при удалении constraint: {e}")
                
                # 9. Удаляем старый столбец
                await session.execute(text("""
                    ALTER TABLE products 
                    DROP COLUMN IF EXISTS variation
                """))
                print("✓ Старый столбец variation удален")
                
                # 10. Создаем новый constraint
                await session.execute(text("""
                    ALTER TABLE products 
                    ADD CONSTRAINT uq_product_combination 
                    UNIQUE (category_id, accessory_brand_id, device_model_id, series_id, variation_id, color_id)
                """))
                print("✓ Новый constraint создан")
                
                # 11. Обновляем версию миграции
                await session.execute(text("""
                    UPDATE alembic_version 
                    SET version_num = 'add_variations_202512'
                """))
                print("✓ Версия миграции обновлена")
                
                await session.commit()
                print("\n✅ Миграция успешно применена!")
                
            elif has_new_variation_id:
                print("✓ Миграция уже применена - variation_id существует")
            else:
                print("⚠ Неожиданное состояние БД")
                
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Ошибка миграции: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(apply_migration())

