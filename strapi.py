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


# print(get_picture_url(api_token_salt, 4))
get_products(api_token_salt)


# "http://localhost:1337/api/products?filters[id][$eq]=6&fields=title&populate[picture][fields]=url"
