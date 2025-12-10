# Лабораторная работа 2

## Описание проекта

Это веб-приложение для сокращения URL. Приложение состоит из четырёх сервисов: базы данных PostgreSQL, сервиса инициализации БД, бэкенда на FastAPI (Python) и фронтенда на Nginx (HTML/JS).

### Архитектура
- **db**: PostgreSQL 15 — хранит данные о URL
- **init-db**: Одноразовый сервис для инициализации БД
- **backend**: FastAPI приложение, которое предоставляет API.
- **frontend**: Nginx, обслуживает статические файлы, проксирует запросы к бэкенду.
- **Сеть**: Все сервисы подключены к bridge-сети `app-network` для внутренней коммуникации.
- **Volumes**: `db_data` для персистентности БД, `./logs` для логов.

## Запуск

1. **Запустите приложение**:
   ```bash
   docker-compose up --build
   ```

2. **Проверьте запуск**:
   - Фронтенд: http://localhost:${FRONTEND_PORT} (по умолчанию 8080)
   - Бэкенд API: http://localhost:${BACKEND_PORT} (по умолчанию 8000)
   - Логи: `docker-compose logs` или папка `./logs`


## Использование

### Через веб-интерфейс
- Откройте http://localhost:8080 в браузере.
- Введите URL в поле и нажмите "Shorten".
- Получите короткий URL.

### Через API
- Сокращение URL:
  ```bash
  curl -X POST http://localhost:8080/api/shorten \
       -H "Content-Type: application/json" \
       -d '{"url": "https://example.com"}'
  ```
- Ответ: JSON с коротким URL.

---

## Ответы на вопросы

### Можно ли ограничивать ресурсы (например, память или CPU) для сервисов в docker-compose.yml? Если нет, то почему, если да, то как?

Да, можно. Есть несколько вариантов:
1. В `docker-compose.yml` можно ограничивать ресурсы через параметры самого контейнера:
```bash
services:
  app:
    image: myapp
    mem_limit: 512m
    cpus: 0.5
```
Запуск: `docker-compose up`. Проверить использование ресурсов через `docker stats`.

2. **Docker Swarm mode** через секцию `deploy.resources`:
```bash
services:
  web:
    image: nginx
    deploy:
      resources:
        limits: # Жесткие ограничения
          cpus: "0.5"
          memory: 200M
        reservations: # Мягкие ограничения
          cpus: "0.25"
          memory: 100M
```
Запуск: `docker stack deploy`.

### Как можно запустить только определенный сервис из docker-compose.yml, не запуская остальные?

Можно запустить только один сервис из docker-compose.yml с помощью `docker-compose up <service_name>`:
  - Пример: `docker-compose up backend` - запустит только backend, но если есть `depends_on`, зависимые сервисы тоже запустятся автоматически.
  - Пример: `docker-compose up --no-deps backend` - запустит только backend, без учета зависимостей `depends_on`.

