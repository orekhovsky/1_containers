FROM postgres:15-alpine

# Устанавливаем psql для выполнения SQL скриптов
RUN apk add --no-cache postgresql-client

# Копируем SQL скрипт инициализации
COPY init.sql /tmp/init.sql

# Копируем скрипт запуска
COPY init.sh /init.sh
RUN chmod +x /init.sh

CMD ["/init.sh"]
