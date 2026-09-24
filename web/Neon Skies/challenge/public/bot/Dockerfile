FROM node:22-bookworm

ENV NODE_ENV=production

WORKDIR /app

COPY package.json package-lock.json ./
RUN PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci --omit=dev && npm cache clean --force

COPY conf.js index.js ./
COPY views ./views

RUN apt-get update \
 && apt-get install -y --no-install-recommends wget \
 && npx playwright install-deps chromium \
 && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
 && { dpkg -i /tmp/chrome.deb || true; } \
 && apt-get -y --fix-broken install \
 && rm -f /tmp/chrome.deb \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && google-chrome-stable --version

USER node

EXPOSE 3001

CMD ["node", "index.js"]
