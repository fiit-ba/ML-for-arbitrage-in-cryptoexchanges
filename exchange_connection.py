import json
from exchanges.Binance_connector import Binance_connector
from exchanges.Bybit_connector import Bybit_connector
from exchanges.Binance_operations import Binance_operations
from exchanges.Bybit_operations import Bybit_operations


class Exchange_connection:
    def __init__(self):
        self.Binance_client, self.Bybit_client, self.keys = None, None, None
        self.load_keys()
        self.connect()

    def load_keys(self):
        """
        Load API and secret keys from keys.json; in the case of a missing key, the user is asked to provide the key
        """
        with open("bot/keys.json", "r") as file:
            self.keys = json.load(file)

        if self.keys["Binance_API_key"] == "":
            self.keys["Binance_API_key"] = input("Binance API key: ")
        if self.keys["Binance_secret_key"] == "":
            self.keys["Binance_secret_key"] = input("Binance secret key: ")
        if self.keys["Bybit_API_key"] == "":
            self.keys["Bybit_API_key"] = input("Bybit API key: ")
        if self.keys["Bybit_secret_key"] == "":
            self.keys["Bybit_secret_key"] = input("Bybit secret key: ")

        with open("bot/keys.json", "w") as file:
            json.dump(self.keys, file)

    def connect(self):
        """
        Connect to both exchanges based on the loaded keys
        """
        Binance = Binance_connector(API_key=self.keys["Binance_API_key"],
                                    secret_key=self.keys["Binance_secret_key"],
                                    base_url="https://testnet.binancefuture.com")

        Bybit = Bybit_connector(API_key=self.keys["Bybit_API_key"],
                                secret_key=self.keys["Bybit_secret_key"],
                                base_url="https://api-testnet.bybit.com")

        self.Binance_client = Binance_operations(Binance)
        self.Bybit_client = Bybit_operations(Bybit)
