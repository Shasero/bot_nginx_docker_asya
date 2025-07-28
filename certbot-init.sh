#!/bin/sh

# Проверяем доступность nginx
NGINX_PATH="/usr/sbin/nginx"
if [ ! -x "$NGINX_PATH" ]; then
    echo "Ошибка: nginx не найден или не исполняемый"
    exit 1
fi

# Ждем, пока nginx станет доступен
while ! curl -f http://nginx/.well-known/acme-challenge/healthcheck >/dev/null 2>&1; do
    echo "Ожидание доступности nginx..."
    sleep 5
done

# Проверяем наличие сертификата
if [ ! -f "/etc/letsencrypt/live/$NGINX_HOST/fullchain.pem" ]; then
    echo "Получаем новый сертификат..."
    certbot certonly --webroot -w /var/www/certbot -d "$NGINX_HOST" --email "$CERTBOT_EMAIL" --agree-tos --non-interactive --dry-run || exit 1
    certbot certonly --webroot -w /var/www/certbot -d "$NGINX_HOST" --email "$CERTBOT_EMAIL" --agree-tos --non-interactive || exit 1
fi

# Основной цикл
while :; do
    echo "Проверяем обновления сертификатов..."
    certbot renew --webroot -w /var/www/certbot --quiet --post-hook "$NGINX_PATH -s reload"
    sleep 12h
done