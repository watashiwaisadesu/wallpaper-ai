# Используем официальный Python образ
FROM python:3.9

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements.txt file into the container
COPY requirements.txt ./

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Expose the port that the FastAPI app will run on
EXPOSE 8000

# Set environment variables for Alembic
ENV PYTHONUNBUFFERED=1
ENV APP_MODULE=app.main:app
ENV HOST=0.0.0.0
ENV PORT=8000

# Run Alembic migrations
RUN alembic upgrade head

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

#CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
