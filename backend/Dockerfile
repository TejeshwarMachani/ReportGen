FROM python:3.11-slim

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]