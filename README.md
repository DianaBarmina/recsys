## Структура репозитория

- course_recs: модули Django, связанные с бэк-логикой приложения и UI сервиса;
- fastapi_als_wrapper: модули на fastapi с использованием ALS для обучения и формирования рекомендаций;

## Как запустить сервис?

Запуск необходимо сделать в 2 команды: первая создаст базу данных в контейнере. Вторая применит миграции, заполнит базу данными из датасетов и запустит приложения на Django и fastapi.

```
docker compose up -d db
docker compose up --build
```

Сервис будет доступен на 8000 порту.