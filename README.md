# Wallpaper-AI

## Описание
Проект Wallpaper-AI создает обои для комнаты, используя технологии искусственного интеллекта. 

## Технологии
- FastAPI
- PostgreSQL

## Установка
1. Создайте виртуальное окружение:
   python -m venv venv
Активируйте виртуальное окружение:

На Windows:
venv\Scripts\activate

На macOS/Linux:
source venv/bin/activate

Установите зависимости:
pip install -r requirements.txt

Запуск приложения
Для запуска приложения используйте следующую команду:
uvicorn app.main:app

Использование
Вы можете взаимодействовать с API, используя Postman или документацию, доступную по адресу http://localhost:8000/docs.

Авторизация
Для авторизации необходимо создать аккаунт, пройти верификацию через почту и активировать аккаунт. На данный момент доступна только функция авторизации.