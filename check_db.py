import psycopg2
from config_reader import db_link

sync_url = db_link.replace('postgresql+asyncpg://', 'postgresql://')

try:
    conn = psycopg2.connect(sync_url)
    cur = conn.cursor()
    
    print("=" * 60)
    print("ПРОВЕРКА СОСТОЯНИЯ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    # Проверяем версию миграции
    print("\n1. Текущая версия миграции:")
    cur.execute("SELECT version_num FROM alembic_version")
    version = cur.fetchone()
    if version:
        print(f"   Версия: {version[0]}")
    else:
        print("   Не найдена")
    
    # Проверяем таблицу variations
    print("\n2. Таблица variations:")
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'variations'
        )
    """)
    exists = cur.fetchone()[0]
    if exists:
        cur.execute("SELECT COUNT(*) FROM variations")
        count = cur.fetchone()[0]
        print(f"   ✓ Существует ({count} записей)")
    else:
        print("   ✗ НЕ существует")
    
    # Проверяем колонки в products
    print("\n3. Колонки в таблице products:")
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'products' 
        AND column_name IN ('variation', 'variation_id')
        ORDER BY column_name
    """)
    columns = cur.fetchall()
    
    has_old = False
    has_new = False
    
    for col in columns:
        if col[0] == 'variation':
            print("   ✗ variation (старое поле) - ЕЩЁ СУЩЕСТВУЕТ")
            has_old = True
        elif col[0] == 'variation_id':
            print("   ✓ variation_id (новое поле) - существует")
            has_new = True
    
    if not has_old and not has_new:
        print("   ⚠ НИ ОДНО поле не найдено!")
    
    print("\n" + "=" * 60)
    if has_new and not has_old:
        print("✅ МИГРАЦИЯ ПРИМЕНЕНА УСПЕШНО!")
    elif has_old and not has_new:
        print("❌ МИГРАЦИЯ НЕ ПРИМЕНЕНА - нужно выполнить миграцию")
    elif has_old and has_new:
        print("⚠ МИГРАЦИЯ В ПРОЦЕССЕ - оба поля существуют")
    else:
        print("⚠ ПРОБЛЕМА С БАЗОЙ ДАННЫХ")
    print("=" * 60)
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()

