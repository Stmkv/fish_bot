# Бот для продажи рыбы

Бот предстовляет собой интернет магазин по продаже рыбы.

## Как запустить

Необходимо создать `.env`

```.env
STRAPI_API_TOKEN=<Token Strapi>
TG_BOT_TOKEN=<Token бота телеграм>
REDIS_ADDRESS=<Адрес Redis>
REDIS_PORT=<Порт Redis>
REDIS_PASSWORD=<пароль Redis>
URL_STARPI=<http://localhost:1337>

```

### Strapi

Работоспособность гарантирована на `python 3.12.X` и `node 22.12.X`

Также должен быть установлен `npm` любой версии

Для создания проекта выполните команды:

```cmd
npx create-strapi-app@latest
```

```cmd
npm run build
```

```cmd
npm run develop
```

В админ панели нужно создать:

Модель `Product` с полями: `titile`, `description` `picture`, `price`

Модель `Cart` с полем: `tg_id`, `cart_item` связанная с `CartItem`, `client` связанный с `Client`

Модель `CartItem` с полем `quantity`, `Product` связанная с `Product`

Модель `Client` с полем `tg_id`, `email` и `carts` связанную с `Cart`

### Tg_bot

Перейти в корневую папку проекта и выполнить:

```cmd
python3 pip install -r requirements.txt
```
