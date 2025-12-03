# Инструкция по применению миграции вариаций

## ⚠️ ВАЖНО: Остановите бота перед миграцией!

Перед применением миграции обязательно остановите работающий бот, иначе возникнут ошибки.

## Способ 1: Через Alembic (рекомендуется)

1. Остановите бота (Ctrl+C в терминале где он запущен)

2. Откройте PowerShell в папке проекта и выполните:

```powershell
.venv\Scripts\activate
alembic upgrade head
```

## Способ 2: Через Python скрипт

1. Остановите бота

2. Запустите скрипт миграции:

```powershell
.venv\Scripts\python.exe migrate_sync.py
```

## Способ 3: Через SQL (если предыдущие не работают)

1. Остановите бота

2. Подключитесь к PostgreSQL:

```powershell
psql -U postgres -d shop
```

3. Выполните следующие SQL команды:

```sql
-- 1. Создать таблицу вариаций
CREATE TABLE IF NOT EXISTS variations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE
);

-- 2. Заполнить таблицу вариаций из Products
INSERT INTO variations (name)
SELECT DISTINCT variation 
FROM products 
WHERE variation IS NOT NULL AND variation != ''
ON CONFLICT (name) DO NOTHING;

-- 3. Добавить новый столбец
ALTER TABLE products 
ADD COLUMN IF NOT EXISTS variation_id INTEGER;

-- 4. Создать внешний ключ
ALTER TABLE products 
ADD CONSTRAINT fk_products_variation_id 
FOREIGN KEY (variation_id) REFERENCES variations(id);

-- 5. Мигрировать данные
UPDATE products 
SET variation_id = v.id
FROM variations v
WHERE products.variation = v.name;

-- 6. Удалить старый constraint
ALTER TABLE products 
DROP CONSTRAINT IF EXISTS uq_product_combination;

-- 7. Удалить старый столбец
ALTER TABLE products 
DROP COLUMN IF EXISTS variation;

-- 8. Создать новый constraint
ALTER TABLE products 
ADD CONSTRAINT uq_product_combination 
UNIQUE (category_id, accessory_brand_id, device_model_id, series_id, variation_id, color_id);

-- 9. Обновить версию миграции
UPDATE alembic_version 
SET version_num = 'add_variations_202512';
```

## После применения миграции

1. Проверьте что миграция применилась успешно:

```sql
-- Проверить наличие таблицы variations
SELECT COUNT(*) FROM variations;

-- Проверить наличие столбца variation_id
SELECT column_name 
FROM information_schema.columns 
WHERE table_name='products' AND column_name='variation_id';
```

2. Запустите бота заново:

```powershell
.venv\Scripts\python.exe main.py
```

## Проверка

После запуска бота попробуйте выбрать товар - теперь должен появиться дополнительный шаг выбора вариации (если у товаров есть вариации).

## Если что-то пошло не так

Для отката миграции:

```powershell
alembic downgrade -1
```

Или через SQL:

```sql
-- Это вернёт всё к предыдущему состоянию
-- (команды отката см. в файле миграции)
```

