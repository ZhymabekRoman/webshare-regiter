# Ported from https://github.com/imvast/Webshare-Creator
import json
import os
import random
import string
import time
from functools import wraps
from typing import Callable, Tuple

import requests
from fake_useragent import UserAgent
from faker import Faker
from loguru import logger

standart_header = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json",
    "Connection": "keep-alive",
    "Host": "proxy.webshare.io",
    "Origin": "https://proxy2.webshare.io",
    "Referer": "https://proxy2.webshare.io/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "TE": "trailers",
}

fake_useragent = UserAgent()
fake = Faker()
request_session = requests.Session()
request_session.headers = standart_header


def _update_random_proxy(proxy_file_name: str = "1", proxy_type: str = "socks5"):
    return
    if not os.path.isfile(proxy_file_name):
        logger.warning(
            "No proxy file list was found. Using Webshare without proxy can lead to multiple throttle ban."
        )
        return
    with open(proxy_file_name) as file:
        proxy_list = file.readlines()
        random_proxy = random.choice(proxy_list)
    proxy = f"{proxy_type}://{random_proxy}"
    request_session.proxies.update({"http": proxy, "https": proxy})


def temporary_cache(access_count: int = 2):
    def decorator(func):
        func.cache = None
        func.call_count = 0

        @wraps(func)
        def inner(*args, **kwargs):
            if not func.cache or func.call_count == access_count:
                func.cache = func(*args, **kwargs)
                func.call_count = 1
            else:
                func.call_count += 1
            return func.cache

        return inner

    return decorator


def _update_random_user_agent():
    request_session.headers = {"User-Agent": fake_useragent.random}


def _random_char(char_num) -> str:
    return "".join(random.choice(string.ascii_letters) for _ in range(char_num))


def _random_email(email_site: str = None) -> str:
    famous_email_site_list = ["google.com", "yandex.com", "mail.com"]

    if not email_site:
        email_site = random.choice(famous_email_site_list)

    return f"{_random_char(12)}@{email_site}"


@temporary_cache(2)
def _recaptcha_token_manual() -> str:
    token = input("Enter Recaptcha token for Webshare: ")
    return token


def _random_password() -> str:
    return _random_char(15)


def register_acc(
    _recaptcha_token_provider: Callable = _recaptcha_token_manual,
    _random_email_provider: Callable = _random_email,
    _random_password_provider: Callable = _random_password,
) -> Tuple[str, str, str]:
    random_email = _random_email_provider()
    random_password = _random_password_provider()
    while True:
        try:
            recaptcha_code = _recaptcha_token_provider()
            response = request_session.post(
                "https://proxy.webshare.io/api/v2/register/",
                json={
                    "email": random_email,
                    "password": random_password,
                    "recaptcha": recaptcha_code,
                    "tos_accepted": True,
                    "marketing_email_accepted": False,
                },
            )
            response_json = response.json()
            if response.status_code != 200:
                if response_json.get("recaptcha"):
                    if response_json["recaptcha"][0]["code"] == "captcha_invalid":
                        logger.error(f"Invalid Recaptcha token: {response_json}")
                        _recaptcha_token_provider.cache = None
                elif response.status_code == 429:
                    logger.debug(f"Possible rate limit error. Info: {response_json}")
                    # wait_time = re.findall(r"\d+", response_json["detail"])[0]
                    # wait_time = int(wait_time)
                    # wait_time += 15
                    # logger.warning(f"Throttle limiter block. Wait {wait_time} secconds")
                    # time.sleep(wait_time)
                    _update_random_proxy()
                    continue
                raise ValueError(
                    f"Error: can't register account. Status code: {response.status_code}. Info: {response_json}"
                )

            return response_json["token"], random_email, random_password
        except Exception as ex:
            logger.exception(ex)
            _update_random_proxy()


def get_proxy_download_token(account_token: str) -> str:
    auth_header = {"Authorization": f"Token {account_token}"}
    response = request_session.get(
        "https://proxy.webshare.io/api/v2/proxy/config/", headers=auth_header
    )
    response_json = response.json()

    if not response_json.get("proxy_list_download_token"):
        raise ValueError(
            f"Error: can't parse proxy download token. Info: {response_json}"
        )

    return response_json["proxy_list_download_token"]


def get_proxy(proxy_download_token: str) -> str:
    response = requests.get(
        f"https://proxy.webshare.io/api/v2/proxy/list/download/{proxy_download_token}/-/any/username/direct/-/"
    )
    return response.text.split("\n")


def main():
    _update_random_proxy()
    account_count = int(input("How much Webshare account to create: "))
    account_list = []
    try:
        for i in range(1, account_count + 1):
            logger.debug(f"[{i}/{account_count}]: Create Webshare account")
            account_token, email, password = register_acc()
            proxy_download_token = get_proxy_download_token(account_token)
            proxy_list = get_proxy(proxy_download_token)

            output = {
                "token": account_token,
                "email": email,
                "password": password,
                "proxy_list": proxy_list,
            }
            account_list.append(output)
            logger.debug(output)
    except Exception as ex:
        raise ex
    finally:
        if account_list:
            logger.debug("File dump...")
            with open(f"webshare-{int(time.time())}.txt", "w") as file:
                json.dump(account_list, file)


if __name__ == "__main__":
    main()
