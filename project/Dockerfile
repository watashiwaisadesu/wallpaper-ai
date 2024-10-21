# Используем официальный Python образ
FROM python:3.9

# Устанавливаем рабочую директорию
WORKDIR /usr/src/app

# Копируем зависимости (например, requirements.txt)
COPY requirements.txt ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# Выполняем миграцию базы данных
RUN alembic upgrade head

# Запускаем приложение
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
