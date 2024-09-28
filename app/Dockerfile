FROM alpine:latest

RUN apk update && apk add \
    curl \
    python3 \
    py3-pip \
    py3-pyarrow \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app
RUN pip3 install --break-system-packages -r requirements.txt

COPY . /app/

EXPOSE 8000

HEALTHCHECK CMD curl --fail http://localhost:8000/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8000", "--server.address=0.0.0.0"]
