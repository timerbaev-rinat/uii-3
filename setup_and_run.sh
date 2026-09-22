#!/bin/bash

# =============================================================================
# Скрипт первоначальной настройки и запуска системы "Учет имущества школы"
# Стек: Python/Django (Backend), React (Frontend), MySQL
# =============================================================================

set -e  # Остановка при ошибке

echo "============================================================"
echo "  ЗАПУСК НАСТРОЙКИ И ПЕРВОГО ЗАПУСКА СИСТЕМЫ"
echo "============================================================"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# 1. Проверка наличия необходимых инструментов
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[1/8] Проверка необходимых инструментов...${NC}"

command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Ошибка: Python3 не найден.${NC}"; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo -e "${RED}Ошибка: pip3 не найден.${NC}"; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}Ошибка: Node.js не найден.${NC}"; exit 1; }
command -v npm >/dev/null 2>&1 || { echo -e "${RED}Ошибка: npm не найден.${NC}"; exit 1; }
command -v mysql >/dev/null 2>&1 || { echo -e "${RED}Ошибка: MySQL клиент не найден.${NC}"; exit 1; }

echo -e "${GREEN}Все необходимые инструменты найдены.${NC}"

# -----------------------------------------------------------------------------
# 2. Настройка переменных окружения (.env)
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[2/8] Настройка переменных окружения...${NC}"

ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Создание файла .env..."
    cat > $ENV_FILE <<EOF
# Django Settings
SECRET_KEY=django-insecure-change-this-in-production-$(openssl rand -base64 32)
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings (MySQL)
DB_NAME=school_assets_db
DB_USER=school_user
DB_PASSWORD=school_secure_password_123
DB_HOST=localhost
DB_PORT=3306

# Frontend Settings
REACT_APP_API_URL=http://localhost:8000/api
EOF
    echo -e "${GREEN}Файл .env создан.${NC}"
else
    echo -e "${YELLOW}Файл .env уже существует. Пропускаем создание.${NC}"
fi

# Загрузка переменных в текущую сессию
export $(grep -v '^#' $ENV_FILE | xargs)

# -----------------------------------------------------------------------------
# 3. Создание базы данных MySQL
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[3/8] Настройка базы данных MySQL...${NC}"

echo "Введите пароль root пользователя MySQL (если требуется):"
read -s MYSQL_ROOT_PASSWORD
echo ""

# Попытка создания БД и пользователя
mysql -u root -p"$MYSQL_ROOT_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" || {
    echo -e "${RED}Не удалось создать базу данных. Проверьте пароль root и наличие MySQL.${NC}"
    exit 1
}

mysql -u root -p"$MYSQL_ROOT_PASSWORD" -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';" || true
mysql -u root -p"$MYSQL_ROOT_PASSWORD" -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';" || true
mysql -u root -p"$MYSQL_ROOT_PASSWORD" -e "FLUSH PRIVILEGES;" || true

echo -e "${GREEN}База данных '$DB_NAME' и пользователь '$DB_USER' созданы/проверены.${NC}"

# -----------------------------------------------------------------------------
# 4. Установка зависимостей Backend (Django)
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[4/8] Установка зависимостей Backend (Python)...${NC}"

if [ ! -d "venv" ]; then
    echo "Создание виртуального окружения..."
    python3 -m venv venv
    echo -e "${GREEN}Виртуальное окружение создано.${NC}"
else
    echo -e "${YELLOW}Виртуальное окружение уже существует.${NC}"
fi

echo "Активация виртуального окружения и установка пакетов..."
source venv/bin/activate

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}Зависимости Backend установлены.${NC}"
else
    echo -e "${RED}Файл requirements.txt не найден!${NC}"
    exit 1
fi

# -----------------------------------------------------------------------------
# 5. Миграции и начальная настройка Django
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[5/8] Выполнение миграций и настройка Django...${NC}"

cd backend 2>/dev/null || { echo -e "${RED}Папка backend не найдена!${NC}"; exit 1; }

# Применение миграций
python manage.py migrate

# Сбор статических файлов
python manage.py collectstatic --noinput

# Создание суперпользователя (интерактивно)
echo -e "${YELLOW}Создание суперпользователя (администратора)...${NC}"
echo "Введите данные для администратора (login, email, password)."
python manage.py createsuperuser --noinput --username admin --email admin@school.ru || {
    # Если пользователь уже есть или ввод интерактивный
    echo "Суперпользователь 'admin' уже существует или создан вручную."
}

# Загрузка начальных данных (фикстур), если есть
if [ -f "fixtures/initial_data.json" ]; then
    echo "Загрузка начальных данных..."
    python manage.py loaddata initial_data.json
fi

cd ..

echo -e "${GREEN}Backend настроен и готов к запуску.${NC}"

# -----------------------------------------------------------------------------
# 6. Установка зависимостей Frontend (React)
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[6/8] Установка зависимостей Frontend (React)...${NC}"

cd frontend 2>/dev/null || { echo -e "${RED}Папка frontend не найдена!${NC}"; exit 1; }

if [ -f "package.json" ]; then
    npm install
    echo -e "${GREEN}Зависимости Frontend установлены.${NC}"
else
    echo -e "${RED}Файл package.json не найден в папке frontend!${NC}"
    exit 1
fi

cd ..

# -----------------------------------------------------------------------------
# 7. Запуск серверов (в фоне)
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[7/8] Запуск серверов разработки...${NC}"

# Запуск Django
echo "Запуск Django сервера на порту 8000..."
cd backend
source ../venv/bin/activate
nohup python manage.py runserver 0.0.0.0:8000 > ../django.log 2>&1 &
DJANGO_PID=$!
cd ..

# Запуск React
echo "Запуск React сервера на порту 3000..."
cd frontend
nohup npm start > ../react.log 2>&1 &
REACT_PID=$!
cd ..

echo -e "${GREEN}Серверы запущены:${NC}"
echo "  - Backend (Django): http://localhost:8000"
echo "  - Admin Panel:      http://localhost:8000/admin"
echo "  - Frontend (React): http://localhost:3000"
echo ""
echo "Логи процессов:"
echo "  - Django: django.log"
echo "  - React:  react.log"

# -----------------------------------------------------------------------------
# 8. Финальное сообщение
# -----------------------------------------------------------------------------
echo -e "${YELLOW}[8/8] Завершение настройки...${NC}"

sleep 5 # Даем время серверам подняться

echo ""
echo "============================================================"
echo -e "${GREEN}  СИСТЕМА УСПЕШНО ЗАПУЩЕНА!${NC}"
echo "============================================================"
echo ""
echo "Доступные адреса:"
echo "  🔹 Frontend:  http://localhost:3000"
echo "  🔹 Backend API: http://localhost:8000/api"
echo "  🔹 Admin DJango: http://localhost:8000/admin"
echo ""
echo "Учетные данные администратора:"
echo "  Логин: admin"
echo "  Email: admin@school.ru"
echo "  Пароль: тот, который вы задали при создании"
echo ""
echo "Чтобы остановить серверы, выполните:"
echo "  kill $DJANGO_PID $REACT_PID"
echo "  или просто закройте терминал."
echo "============================================================"
