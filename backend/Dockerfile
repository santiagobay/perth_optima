FROM python:3.12-slim

# CBC es el solver del modelo exacto: no se instala por pip, es un binario del SO.
RUN apt-get update && apt-get install -y --no-install-recommends coinor-cbc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5000
EXPOSE 5000

# Servidor WSGI de producción: el servidor de desarrollo de Flask no debe
# exponerse (es monohilo y, con debug, permite ejecutar codigo arbitrario).
CMD ["sh", "-c", "gunicorn -w 2 -t 120 -b 0.0.0.0:${PORT} app:app"]
