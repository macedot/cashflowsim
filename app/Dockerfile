FROM alpine:latest

RUN apk update && apk add \
    curl \
    python3 \
    py3-pip \
    py3-pyarrow \
    && rm -rf /var/lib/apt/lists/*

COPY . /app
WORKDIR /app

RUN pip3 install --break-system-packages -r requirements.txt

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
