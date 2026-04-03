FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads

ENV PORT=10000
EXPOSE 10000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120
