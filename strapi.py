from io import BytesIO

import requests
from environs import Env

env = Env()
env.read_env()
api_token_salt = env.str("API_TOKEN_SALT")


def get_products(api_token_salt):
    product_list = []
    headers = {"Authorization": f"bearer {api_token_salt}"}
    url = "http://localhost:1337/api/products"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    response_products = response.json()["data"]

    for product in response_products:
        product_list.append(product)
    print(product_list)
    return product_list


def get_picture_url(api_token_salt, id_product):
    url = "http://localhost:1337/api/products"
    params = {
        "filters[id][$eq]": id_product,
        "fields": "title",
        "populate[picture][fields]": "url",
    }
    headers = {"Authorization": f"bearer {api_token_salt}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    image_url = response.json()["data"][0]["picture"][0]["url"]
    return image_url


def get_image(api_token_salt, picture_url):
    url = f"http://localhost:1337{picture_url}"
    headers = {"Authorization": f"bearer {api_token_salt}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    image_bytes = BytesIO(response.content)
    return image_bytes


def create_cart(api_token_salt, tg_id):
    url = "http://localhost:1337/api/carts"
    headers = {
        "Authorization": f"bearer {api_token_salt}",
        "Content-Type": "application/json",
    }
    data = {
        "data": {
            "tg_id": tg_id,
        }
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["id"]


def get_cart_id(api_token_salt, tg_id):
    url = f"http://localhost:1337/api/carts?filters[tg_id][$eq]={tg_id}"
    headers = {"Authorization": f"bearer {api_token_salt}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()
    if data["data"]:
        return data["data"][0]["id"]
    return None


def add_to_cart_item(api_token_salt, tg_id, product_id, quantity=1):
    cart_id = get_cart_id(api_token_salt, tg_id)

    if not cart_id:
        cart_id = create_cart(api_token_salt, tg_id)

    url = "http://localhost:1337/api/cart-items"
    headers = {
        "Authorization": f"bearer {api_token_salt}",
        "Content-Type": "application/json",
    }
    print(product_id)
    data = {
        "data": {
            "Product": {"connect": [{"id": product_id}]},
            "quantity": quantity,
        }
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()


get_products(api_token_salt)
