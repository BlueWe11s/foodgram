# Foodgram
### Описание:
Проект foodgram -дает возможность пользователям создавать и хранить рецепты на онлайн-платформе. Кроме того, можно скачать список продуктов, необходимых для приготовления блюда, просмотреть рецепты друзей и добавить любимые рецепты в список избранных.

### Технологии:

## Python--3.9.13
## Django--3.2

### Как запустить проект:

Запуск проекта на удаленном сервере
Установить docker compose на сервер:
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt-get install docker-compose-plugin
Скачать файл docker-compose.production.yml на свой сервер.

На сервере в директории с файлом docker-compose.production.yml создать файл .env:

POSTGRES_DB=имя базы
POSTGRES_USER=владелец базы
POSTGRES_PASSWORD=пароль базы
DB_HOST=db
DB_PORT=5432
SECRET_KEY=ключ приложения django
DEBUG=True/False
ALLOWED_HOSTS=разрешенные хосты(your.domain.com)
Запустить Docker compose:
sudo docker compose -f docker-compose.production.yml up -d
На сервере настроить и запустить Nginx:
открыть файлы конфигурации
sudo nano /etc/nginx/sites-enabled/default
внести изменения, заменив <your.domain.com> на свое доменное имя
server {
    listen 80;
    server_name <your.domain.com>;

    location / {
        proxy_set_header Host $http_host;        
        proxy_pass http://127.0.0.1:9090;
        client_max_body_size 5M;
        
    }
}
убедиться, что в файле конфигурации нет ошибок
sudo nginx -t
перезагрузить конфигурацию
sudo service nginx reload

### Проект
- [Foodgram](https://bboi.hopto.org)

### Авторы
- [Юрий Крылов](https://github.com/BlueWe11s)
