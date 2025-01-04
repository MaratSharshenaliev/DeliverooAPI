import json
import os
import queue
import time
import uuid

import requests
from dotenv import load_dotenv
from colorama import Fore, init

load_dotenv()
init()

X_ROO_STICKY_GUID = os.getenv('X_ROO_STICKY_GUID')
X_ROO_GUID = os.getenv('X_ROO_GUID')
AUTHORIZATION = os.getenv('AUTHORIZATION')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_MESSAGE_TEMPLATE = os.getenv('TELEGRAM_MESSAGE_TEMPLATE', "")
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
USE_PROXY = os.getenv('USE_PROXY')

RESTAURANT_ID = os.getenv('RESTAURANT_ID')

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
LOGIN = os.getenv('LOGIN')
PASSWORD = os.getenv('PASSWORD')


def count_time(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Function '{func.__name__}' executed in {elapsed_time:.4f} seconds")
        return result

    return wrapper


class DeliverooAPI:
    def __init__(self):
        self.waiting_time = 5
        self.headers = {
            "Host": "co-m.ae.deliveroo.com",
            "User-Agent": "Deliveroo-OrderApp/3.256.0 (Android; Android 12; Pixel 5; Release; en_US; 85123)",
            "X-Roo-App-Version": "3.256.0",
            "X-APOLLO-OPERATION-NAME": "get_menu_page",
            "X-Roo-Rooblocks-Version": "1.1.9",
            "apollographql-client-name": "com.deliveroo.orderapp-apollo-android",
            "X-Roo-Country": "ae",
            "apollographql-client-version": "3.252.0-84322",
            "Connection": "keep-alive",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "multipart/mixed;deferSpec=20220824,application/json",
            "Content-Type": "application/json",
            "X-Roo-Platform": "Android",
            "X-APOLLO-OPERATION-TYPE": "query",
            "Accept-Encoding": "gzip, deflate, br",
            "Authorization": AUTHORIZATION,
            "X-Roo-Sticky-Guid": X_ROO_STICKY_GUID,
            "X-Roo-AppsFlyerUID": "1727956408971-4679142",
            "X-Roo-Guid": X_ROO_GUID,
        }

        self.restaurant_id = RESTAURANT_ID
        self.store_url = 'https://co-m.ae.deliveroo.com'
        self.current_page = 'CHECK_IP' if USE_PROXY == "True" else "CLEAN_BASKET"
        self.checkout_id = str(uuid.uuid4())
        self.force_new = False
        self.payment_plan = None

        self.queue = queue.Queue()
        for item in json.loads(self.query_parse("items.json")):
            self.queue.put(item)

        self.session = requests.Session()
        if USE_PROXY == "True":
            self.session.proxies = {
                'http': f'http://{LOGIN}:{PASSWORD}@{HOST}:{PORT}',
                'https': f'http://{LOGIN}:{PASSWORD}@{HOST}:{PORT}',
            }

    @staticmethod
    def query_parse(path):
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()

    def get_current_page(self):
        return self.current_page

    @staticmethod
    def sleep(seconds):
        print("Waiting:", end=" ", flush=True)
        for i in range(seconds):
            time.sleep(1)
            print(f"\rWaiting: {i + 1}/{seconds} s", end="", flush=True)
        print(" Done!")

    # @count_time
    def clear_basket(self):
        try:
            query = self.query_parse(os.path.join(os.path.dirname(__file__), 'graphql', 'clear_basket.graphql'))
            payload = {
                "query": query,
                "variables": {
                    "options": {
                        "fulfillment_method": "DELIVERY",
                        "delivery_time": {
                            "time": "ASAP",
                            "day": "TODAY"
                        },
                        "location": {
                            "lat": 25.10998786703184,
                            "lon": 55.203825496137142
                        },
                        "branch_id": self.restaurant_id
                    }
                }
            }
            r = self.session.post(
                f'{self.store_url}/consumer/basket/graphql',
                headers=self.headers,
                json=payload,
            )

            if r.status_code == 429:
                self.current_page = 'COLLECTING_PRODUCTS'
                print(Fore.RED + '[-] Too many requests')
                self.sleep(self.waiting_time)
            if r.status_code == 401:
                print(Fore.RED + "[-] Unauthorized")
            if r.status_code == 200:
                response = r.json()
                if response.get('data', {}).get('clear_basket', {}).get('success'):
                    print(Fore.GREEN + '[+] Basket is clean...')
                    self.current_page = 'COLLECTING_PRODUCTS'
        except Exception as e:
            print(e)

    def error_handler(self, errors):
        for error in errors:
            if 'Payment declined' == error.get("extensions", {}).get("title", ""):
                print(Fore.RED + "[-] Payment declined")
            else:
                print(Fore.RED + f'[-] {json.dumps(error)}')

    # @count_time
    def add_item_to_basket(self, item):
        try:
            query = self.query_parse(os.path.join(os.path.dirname(__file__), 'graphql', 'addBasket.graphql'))
            variables = {
                "capabilities": {
                    "ui_action_types": [
                        "CHANGE_ADDRESS",
                        "GO_TO_PLUS_SIGN_UP"
                    ],
                    "ui_list_components": [
                        "UI_CHARITY_DONATION_OPTIONS"
                    ],
                    "ui_icons": [
                        "COOP_LOGO"
                    ]
                },
                "clientConfig": {
                    "use_accessible_layout": False
                },
                "options": {
                    "delivery_time": {
                        "day": "TODAY",
                        "time": "ASAP"
                    },
                    "force_new": self.force_new,
                    "branch_id": self.restaurant_id,
                    "fulfillment_method": "DELIVERY",
                    "location": {
                        "lat": 25.10998786703184,
                        "lon": 55.203825496137142
                    }
                },
                "item": item,
                "skipUI": False
            }
            payload = {
                "operation_name": "AddBasketItem",
                "query": query,
                "variables": variables,
            }

            r = self.session.post(
                f'{self.store_url}/consumer/basket/graphql',
                headers=self.headers,
                json=payload
            )
            if r.status_code == 422:
                print(Fore.RED + f"[-] {r.text} ")

            if r.status_code == 429:
                print(Fore.RED + '[-] Too many requests')
                self.sleep(self.waiting_time)
            if r.status_code == 200:
                response = r.json()
                add_basket_item: dict = response.get('data', {}).get("add_basket_item", {})
                modals_on_load: [] = add_basket_item.get("modals_on_load", [])
                # Проверка если в корзине что то есть то нужно удалять
                if len(modals_on_load) > 0:
                    for modal in modals_on_load:

                        if 'Create new basket?' in modal.get('header', {}).get('title'):
                            print(Fore.GREEN + "[+] New Basket Created")
                            self.force_new = True
                        if 'Sorry, looks like there was a problem' in modal.get('header', {}).get('title'):
                            print(Fore.RED + "[-] Sorry, looks like there was a problem")
                        else:
                            print(Fore.RED + "[-] " + modal.get('header', {}).get('title'))

                errors = response.get("errors", [])
                if len(errors) > 0:
                    self.error_handler(errors)
                    return []

                return add_basket_item.get("meta", {}).get("basket").get("items", [])
        except Exception as e:
            print(e)
            return []

    # @count_time
    def create_payment_plan(self):
        try:
            if self.payment_plan:
                return

            query = self.query_parse(os.path.join(os.path.dirname(__file__), 'graphql', 'createPaymentPlan.graphql'))
            payload = {
                "operation_name": "create_payment_plan",
                "query": query,
                "variables": {
                    "capabilities": {
                        "wallets": [
                            {
                                "is_configured": False,
                                "type": "APPLE_PAY"
                            }
                        ],
                        "payment_capabilities": [
                            "RETURN_PAYPAL_PAYMENT_OPTIONS",
                            "PAYPAL_UPSELL",
                            "RETURN_PAYMENT_TOKEN_TYPE",
                            "RETURN_IDEAL",
                            "PAYMENT_TOKEN_UPSELL",
                            "SHOW_CORPORATE_MEAL_PROGRAM_ALLOWANCE_OPTION"
                        ],
                        "ui_blocks_capabilities": [
                            "TERMS_AND_CONDITIONS_SECTION",
                            "PAYMENT_SECTION",
                            "LOYALTY_CARD_SECTION",
                            "VOUCHERS",
                            "FULFILLMENT_DETAILS_SECTION"
                        ]
                    },
                    "payment_limitations": [],
                    "client_event": "INITIAL_PLAN_LOAD",
                    "params": [],
                    "checkout_id": self.checkout_id
                }
            }

            print("=======================  Creating payment plan =======================")

            r = self.session.post(
                f'{self.store_url}/checkout-api/graphql-query',
                headers=self.headers,
                json=payload
            )

            if r.status_code == 422:
                print(Fore.RED + f"[-] {r.text} ")

            if r.status_code == 429:
                print(Fore.RED + '[-] Too many requests')
                self.sleep(self.waiting_time)
            if r.status_code == 200:
                response = r.json()
                errors = response.get("errors", [])
                if len(errors) > 0:
                    self.error_handler(errors)

                self.payment_plan = response.get("data", {}).get("payment_plan", None)
                print(Fore.GREEN + f"[+] Payment plan id: {self.payment_plan.get('id')}")
                self.current_page = "EXECUTE_PAYMENT"
        except Exception as e:
            print(e)

    def web_challenge(self, url):
        try:
            headers = {
                "Host": "deliveroo.ae",
                "Sec-Fetch-Mode": "none",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Origin": "null",
                "Content-Length": "0",
                "Connection": "keep-alive",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
                "Sec-Fetch-Dest": "document",
            }
            response = self.session.post(url, headers=headers)
            if response.status_code == 421:
                print(f"URL: {response.url}")
                self.send_telegram(response.url)
                self.current_page = "HALAS"
        except Exception as e:
            print(f"An error occurred: {e}")

    def execute_payment_plan(self):
        try:
            if not self.payment_plan: self.current_page = "CHECKOUT"
            print('=======================  Executing payment plan =======================')
            query = self.query_parse(os.path.join(os.path.dirname(__file__), 'graphql', 'executePaymentPlan.graphql'))
            payload = {
                "operation_name": "execute_payment_plan",
                "query": query,
                "variables": {
                    "payment_plan_id": self.payment_plan["id"],
                    "params": [],
                    "checkout_id": self.checkout_id,
                    "marketing_preference_results": {
                        "results": []
                    }
                }
            }

            r = self.session.post(
                f'{self.store_url}/checkout-api/graphql-query',
                headers=self.headers,
                json=payload
            )

            if r.status_code == 422:
                print(Fore.RED + f"[-] {r.text} ")
                return None, None

            if r.status_code == 429:
                print(Fore.RED + f'[-] {r.text.replace(" ", "")}')
                self.sleep(self.waiting_time)
                return None, None

            if r.status_code == 200:
                response = r.json()

                errors = response.get("errors", [])
                if len(errors) > 0:
                    self.error_handler(errors)
                    return None, None
                payment_plan_execution_result = response.get("data", {}).get("payment_plan_execution_result", {})
                print(Fore.GREEN + f"[+] Payment plan order id: {payment_plan_execution_result.get('order_id')}")

                return (
                    payment_plan_execution_result.get("order_id", None),
                    payment_plan_execution_result.get("challenge", {}).get("url", None)
                )

        except Exception as e:
            print(e)

    @staticmethod
    def send_telegram(url_auth):
        try:
            domain = "https://api.telegram.org"
            text = f"""
                {TELEGRAM_MESSAGE_TEMPLATE}
                {url_auth}
            """
            r = requests.post(f"{domain}/{TELEGRAM_BOT_TOKEN}/sendMessage?chat_id={TELEGRAM_CHAT_ID}&text={text}")
            if r.status_code == 200:
                print(Fore.GREEN + "[+] Telegram sent successfully")
        except Exception as e:
            print(e)

    def get_ip(self):
        print(Fore.GREEN + "[+] Started on proxy: " + self.session.get("http://httpbin.org/ip").json()["origin"])
        self.current_page = "CLEAN_BASKET"

    @staticmethod
    def find_item_by_id(item_id, basket):
        for basket_item in basket:
            if basket_item.get("menu_item_drn_id", "") == item_id:
                return True
        return False

    def collect_items(self):
        item = self.queue.get()
        basket = self.add_item_to_basket(item)
        if not self.find_item_by_id(item.get("menu_item_drn_id", "1"), basket):
            self.queue.put(item)

        if self.queue.empty():
            self.current_page = "CHECKOUT"

    def run(self):
        while True:
            if self.current_page == "CHECK_IP":
                self.get_ip()
            elif self.current_page == 'CLEAN_BASKET':
                self.clear_basket()
            elif self.current_page == 'COLLECTING_PRODUCTS':
                self.collect_items()
            elif self.current_page == 'CHECKOUT':
                self.create_payment_plan()
            elif self.current_page == 'EXECUTE_PAYMENT':
                order_id, url = self.execute_payment_plan()
                if order_id and url:
                    self.web_challenge(url)
            elif self.current_page == 'HALAS':
                return;


if __name__ == '__main__':
    app = DeliverooAPI()
    app.run()
