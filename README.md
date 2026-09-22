# Система учёта имущества школы (School Asset Management System)

Прототип (MVP) системы для автоматизации учёта имущества в школах. Разработана на основе технического задания из `chek list.md`.

## 📋 Описание проекта

Система предназначена для:
- Учёта основных средств (оборудование, мебель, транспорт)
- Контроля материальных запасов (канцелярия, расходники)
- Оформления операций (приёмка, перемещение, списание, инвентаризация)
- Генерации отчётов и выгрузок (Excel, PDF, CSV)
- Работы с QR-кодами и штрихкодами
- Уведомлений о событиях (гарантия, инвентаризация)

### Роли пользователей:
- **Администратор** — полное управление системой
- **Завхоз** — управление имуществом и операциями
- **Бухгалтер** — финансовый учёт и отчёты
- **Педагог** — просмотр и заявки
- **Тех. специалист** — обслуживание и ремонт

## 🛠 Технологический стек

- **Backend:** Python 3.10+, Django 5.x, Django REST Framework
- **Frontend:** React 18+, Vite, Material-UI (MUI)
- **Database:** MySQL 8.0+
- **API:** REST API с JWT-аутентификацией
- **QR/Штрихкоды:** qrcode, python-barcode
- **Отчёты:** openpyxl (Excel), reportlab (PDF)

## 🚀 Как запустить проект

### Предварительные требования
- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Git

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd school-asset-mgmt
```

### 2. Настройка базы данных (MySQL)

Создайте базу данных и пользователя:
```sql
CREATE DATABASE school_assets CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'school_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON school_assets.* TO 'school_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Настройка Backend (Django)

#### Создание виртуального окружения
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

#### Установка зависимостей
```bash
pip install -r requirements.txt
```

#### Настройка переменных окружения
Создайте файл `.env` в папке `backend`:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=school_assets
DB_USER=school_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# JWT
JWT_EXPIRATION_HOURS=24
```

#### Миграции и запуск сервера
```bash
python manage.py migrate
python manage.py createsuperuser  # Создание администратора
python manage.py runserver
```
Backend доступен по адресу: http://localhost:8000

### 4. Настройка Frontend (React)

#### Установка зависимостей
```bash
cd frontend
npm install
```

#### Настройка переменных окружения
Создайте файл `.env` в папке `frontend`:
```env
VITE_API_URL=http://localhost:8000/api
VITE_APP_TITLE=Учёт имущества школы
```

#### Запуск development-сервера
```bash
npm run dev
```
Frontend доступен по адресу: http://localhost:5173

### 5. Первый вход в систему

1. Откройте http://localhost:5173
2. Войдите под учётной записью суперпользователя
3. Назначьте роли другим пользователям через админ-панель Django (http://localhost:8000/admin)

## 📁 Структура проекта

```
school-asset-mgmt/
├── backend/                 # Django backend
│   ├── apps/
│   │   ├── assets/         # Модели имущества
│   │   ├── operations/     # Операции (приёмка, перемещение и т.д.)
│   │   ├── reports/        # Генерация отчётов
│   │   ├── notifications/  # Уведомления
│   │   └── users/          # Пользователи и роли
│   ├── manage.py
│   └── requirements.txt
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # UI компоненты
│   │   ├── pages/         # Страницы приложения
│   │   ├── services/      # API сервисы
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── chek list.md           # Техническое задание
└── README.md              # Этот файл
```

## 🔑 Основные возможности MVP

- ✅ CRUD операции для всех типов активов
- ✅ Проведение операций (приёмка, перемещение, списание)
- ✅ Генерация QR-кодов для объектов
- ✅ Базовые отчёты (список активов, инвентаризация)
- ✅ Ролевая модель доступа
- ✅ Аудит действий пользователей
- ✅ Выгрузка в Excel/CSV

## 📝 Следующие шаги (Roadmap)

1. Интеграция сканеров штрихкодов
2. Расширенная система уведомлений (email, Telegram)
3. Электронный документооборот с ЭП
4. Мобильное приложение для инвентаризации
5. Интеграция с 1С:Бухгалтерия

## 📄 Лицензия

Проект разработан в учебных целях. Все права на использование принадлежат заказчику.

## 📞 Контакты

По вопросам разработки обращайтесь к команде проекта.
