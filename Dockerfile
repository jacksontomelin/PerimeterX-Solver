FROM python:3.12-slim

WORKDIR /app

# Deps do sistema para Chromium/Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libatspi2.0-0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libx11-xcb1 wget ca-certificates fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instalar Chromium do Playwright
RUN playwright install --with-deps chromium

# Código
COPY . .

ENV PORT=3000
EXPOSE 3000

CMD ["python", "solve.py"]
