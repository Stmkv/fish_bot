from io import BytesIO

import requests
from environs import Env


def get_products(token_strapi_api, base_url):
    product_list = []
    headers = {"Authorization": f"bearer {token_strapi_api}"}
    url = f"{base_url}/api/products"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    response_products = response.json()["data"]

    for product in response_products:
        product_list.append(product)
    return product_list


def get_picture_url(token_strapi_api, id_product, base_url):
    url = f"{base_url}/api/products"
    params = {
        "filters[documentId][$eq]": id_product,
        "fields": "title",
        "populate[picture][fields]": "url",
    }
    headers = {"Authorization": f"bearer {token_strapi_api}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    image_url = response.json()["data"][0]["picture"][0]["url"]
    return image_url


def get_image(token_strapi_api, picture_url, base_url):
    url = f"{base_url}{picture_url}"
    headers = {"Authorization": f"bearer {token_strapi_api}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    image_bytes = BytesIO(response.content)
    return image_bytes


def create_cart(token_strapi_api, tg_id, base_url):
    url = f"{base_url}/api/carts"
    headers = {
        "Authorization": f"bearer {token_strapi_api}",
        "Content-Type": "application/json",
    }
    data = {
        "data": {
            "tg_id": tg_id,
        }
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["documentId"]


def get_cart_id(token_strapi_api, tg_id, base_url):
    url = f"{base_url}/api/carts"
    params = {"filters[tg_id][$eq]": tg_id}
    headers = {"Authorization": f"bearer {token_strapi_api}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    if data["data"]:
        return data["data"][0]["documentId"]
    return None


def add_to_cart_item(token_strapi_api, tg_id, product_id, base_url, quantity=1):
    cart_id = get_cart_id(token_strapi_api, tg_id, base_url)

    if not cart_id:
        cart_id = create_cart(token_strapi_api, tg_id, base_url)

    url = f"{base_url}/api/cart-items"
    headers = {
        "Authorization": f"bearer {token_strapi_api}",
        "Content-Type": "application/json",
    }
    data = {
        "data": {
            "Product": {"connect": [{"documentId": product_id}]},
            "quantity": quantity,
        }
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    return response.json()["data"]["documentId"]


def connect_cart_to_cart_item(token_strapi_api, cart_id, cart_item_id, base_url):
    url = f"{base_url}/api/carts/{cart_id}"
    headers = {
        "Authorization": f"bearer {token_strapi_api}",
    }
    data = {
        "data": {
            "cart_items": {
                "connect": [cart_item_id],
            },
        }
    }
    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def get_products_cart(token_strapi_api, tg_id, base_url):
    url = f"{base_url}/api/carts"
    params = {
        "filters[tg_id][$eq]": tg_id,
        "populate[cart_items][populate]": "Product",
    }
    headers = {"Authorization": f"bearer {token_strapi_api}"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()

    cart_products = response.json()
    cart_products = cart_products["data"][0]["cart_items"]
    user_cart = []
    for product in cart_products:
        user_cart.append(product)

    return user_cart


def delete_product_items(token_strapi_api, tg_id, user_cart, base_url):
    headers = {"Authorization": f"bearer {token_strapi_api}"}

    for item in user_cart:
        cart_item_id = item["documentId"]
        delete_url = f"{base_url}/api/cart-items/{cart_item_id}"
        delete_response = requests.delete(delete_url, headers=headers)
        delete_response.raise_for_status()
    return True


def create_client(token_strapi_api, tg_id, email, base_url):
    url = f"{base_url}/api/clients"
    headers = {
        "Authorization": f"bearer {token_strapi_api}",
        "Content-Type": "application/json",
    }
    data = {
        "data": {
            "email": email,
            "tg_id": tg_id,
        }
    }
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    client_id = response.json()["data"]["documentId"]
    return client_id


def connect_client_to_cart(token_strapi_api, client_id, cart_id, base_url):
    url = f"{base_url}/api/clients/{client_id}"
    headers = {
        "Authorization": f"bearer {token_strapi_api}",
    }
    data = {
        "data": {
            "carts": {
                "connect": [cart_id],
            },
        }
    }
    response = requests.put(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    env = Env()
    env.read_env()
    token_strapi_api = env.str("TOKEN_STRAPI_API")
