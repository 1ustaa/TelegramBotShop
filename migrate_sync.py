"""
Синхронное применение миграции вариаций
"""
import psycopg2
from config_reader import db_link

# Преобразуем async URL в sync
sync_url = db_link.replace('postgresql+asyncpg://', 'postgresql://')

print(f"Подключение к БД...")

conn = psycopg2.connect(sync_url)
cur = conn.cursor()

try:
    # 1. Создаем таблицу variations
    print("1. Создание таблицы variations...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS variations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(200) NOT NULL UNIQUE
        )
    """)
    conn.commit()
    print("   ✓ Таблица variations создана")
    
    # 2. Проверяем наличие полей
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='products' AND column_name='variation'
    """)
    has_old_variation = cur.fetchone() is not None
    
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='products' AND column_name='variation_id'
    """)
    has_new_variation_id = cur.fetchone() is not None
    
    print(f"   Старое поле variation: {'ДА' if has_old_variation else 'НЕТ'}")
    print(f"   Новое поле variation_id: {'ДА' if has_new_variation_id else 'НЕТ'}")
    
    if has_old_variation and not has_new_variation_id:
        print("\n2. Извлечение уникальных вариаций...")
        cur.execute("""
            SELECT DISTINCT variation 
            FROM products 
            WHERE variation IS NOT NULL AND variation != ''
        """)
        unique_variations = [row[0] for row in cur.fetchall()]
        print(f"   Найдено: {len(unique_variations)} уникальных вариаций")
        
        # 3. Вставляем вариации
        print("\n3. Добавление вариаций в таблицу...")
        for variation_name in unique_variations:
            cur.execute(
                "INSERT INTO variations (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                (variation_name,)
            )
        conn.commit()
        print(f"   ✓ Добавлено {len(unique_variations)} вариаций")
        
        # 4. Добавляем столбец variation_id
        print("\n4. Добавление столбца variation_id...")
        cur.execute("""
            ALTER TABLE products 
            ADD COLUMN IF NOT EXISTS variation_id INTEGER
        """)
        conn.commit()
        print("   ✓ Столбец добавлен")
        
        # 5. Создаем внешний ключ
        print("\n5. Создание внешнего ключа...")
        try:
            cur.execute("""
                ALTER TABLE products 
                ADD CONSTRAINT fk_products_variation_id 
                FOREIGN KEY (variation_id) REFERENCES variations(id)
            """)
            conn.commit()
            print("   ✓ Внешний ключ создан")
        except psycopg2.errors.DuplicateObject:
            conn.rollback()
            print("   ! Внешний ключ уже существует")
        
        # 6. Мигрируем данные
        print("\n6. Миграция данных...")
        for variation_name in unique_variations:
            cur.execute("""
                UPDATE products 
                SET variation_id = (SELECT id FROM variations WHERE name = %s)
                WHERE variation = %s
            """, (variation_name, variation_name))
        conn.commit()
        print(f"   ✓ Данные мигрированы")
        
        # 7. Удаляем старый constraint
        print("\n7. Удаление старого constraint...")
        try:
            cur.execute("""
                ALTER TABLE products 
                DROP CONSTRAINT IF EXISTS uq_product_combination
            """)
            conn.commit()
            print("   ✓ Старый constraint удален")
        except Exception as e:
            conn.rollback()
            print(f"   ! Предупреждение: {e}")
        
        # 8. Удаляем старый столбец
        print("\n8. Удаление старого столбца variation...")
        cur.execute("""
            ALTER TABLE products 
            DROP COLUMN IF EXISTS variation
        """)
        conn.commit()
        print("   ✓ Столбец variation удален")
        
        # 9. Создаем новый constraint
        print("\n9. Создание нового constraint...")
        try:
            cur.execute("""
                ALTER TABLE products 
                ADD CONSTRAINT uq_product_combination 
                UNIQUE (category_id, accessory_brand_id, device_model_id, series_id, variation_id, color_id)
            """)
            conn.commit()
            print("   ✓ Новый constraint создан")
        except psycopg2.errors.DuplicateTable:
            conn.rollback()
            print("   ! Constraint уже существует")
        
        # 10. Обновляем версию миграции
        print("\n10. Обновление версии миграции...")
        cur.execute("""
            UPDATE alembic_version 
            SET version_num = 'add_variations_202512'
        """)
        conn.commit()
        print("   ✓ Версия обновлена")
        
        print("\n" + "="*50)
        print("✅ МИГРАЦИЯ УСПЕШНО ПРИМЕНЕНА!")
        print("="*50)
        print("\nТеперь перезапустите бота.")
        
    elif has_new_variation_id:
        print("\n✓ Миграция уже применена - variation_id существует")
    else:
        print("\n⚠ Неожиданное состояние БД")
        
except Exception as e:
    conn.rollback()
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()

