FROM python:3.12-slim

WORKDIR /bot


COPY requirements.txt .


RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .
COPY bot/ .

EXPOSE 7111
ENV TZ=Europe/Moscow


CMD ["python", "-u", "main.py"]
