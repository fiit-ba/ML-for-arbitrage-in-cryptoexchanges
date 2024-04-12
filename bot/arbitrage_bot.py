import time
from datetime import datetime
import re
from tabulate import tabulate
from pynput import keyboard
import json
import pickle

from exchanges.Binance_operations import Binance_operations
from exchange_connection import Exchange_connection


class Arbitrage_bot:
    def __init__(self, cryptocurrency_pairs):
        self.cryptocurrency_pairs = cryptocurrency_pairs
        self.exchange_connection = Exchange_connection()
        self.Binance_crypto_pairs, self.Bybit_crypto_pairs, self.portfolio, self.Binance_position_counter, \
            self.Bybit_position_counter = [], [], None, 0, 0
        self.running = True
        self.min_percentage_profit = 0.01

        self.Binance_client = self.exchange_connection.Binance_client
        self.Bybit_client = self.exchange_connection.Bybit_client
        if self.Binance_client is None or self.Bybit_client is None or self.cryptocurrency_pairs is None:
            raise ValueError("Required data for starting of arbitrage bot not provided.")

        self.get_Binance_pairs(self.cryptocurrency_pairs.copy())
        self.get_Bybit_pairs()

        if len(self.Binance_crypto_pairs) != len(self.Bybit_crypto_pairs) or \
                len(self.Bybit_crypto_pairs) != len(self.cryptocurrency_pairs):
            raise ValueError("Provided cryptocurrency pairs are not available for trading on both exchanges.")

        machine_learning = input("Do you want to include Machine Learning model? (Y/N) ").lower()
        if machine_learning == "y":
            self.machine_learning_inclusion = True
        if machine_learning == "n":
            self.machine_learning_inclusion = False
        self.arbitrage_search()

    def get_Binance_pairs(self, required_pairs):
        """
        Check if all required pairs are available on the Binance exchange
        :param required_pairs: pairs that are supposed to be traded
        """
        exchange_info = self.Binance_client.get_exchange_info()
        if exchange_info is None:
            return []

        for symbol in exchange_info["symbols"]:
            for pair in required_pairs:
                if re.search(r'^' + str(pair), symbol["symbol"]):
                    taker_fee = self.Binance_client.get_taker_fee(symbol["symbol"])
                    self.Binance_crypto_pairs.append(
                        dict({"symbol": symbol["symbol"], "base_asset": symbol["baseAsset"],
                              "quote_asset": symbol["quoteAsset"],
                              "taker_fee": float(taker_fee["takerCommissionRate"]) * 100}))
                    required_pairs.remove(pair)
                    self.Binance_client.set_leverage(symbol["symbol"])

    def get_Bybit_pairs(self):
        """
        Check if all the required pairs found on Binance are also available on Bybit
        """
        exchange_info = self.Bybit_client.get_exchange_info()
        if exchange_info is None or "result" not in exchange_info or "list" not in exchange_info["result"]:
            return
        tickers = exchange_info["result"]["list"]

        for pair in self.Binance_crypto_pairs:
            for ticker in tickers:
                if ticker["symbol"] == pair["symbol"]:
                    taker_fee = self.Bybit_client.get_taker_fee(pair["symbol"])
                    if taker_fee is None or "result" not in taker_fee or "list" not in taker_fee["result"]:
                        return
                    taker_fee = taker_fee["result"]["list"]
                    if len(taker_fee) == 0:
                        return
                    taker_fee = taker_fee[0]["takerFeeRate"]
                    self.Bybit_crypto_pairs.append(pair)
                    self.Bybit_crypto_pairs[len(self.Bybit_crypto_pairs) - 1]["taker_fee"] = float(taker_fee) * 100
                    self.Bybit_client.set_leverage(pair["symbol"])
                    break

    def display_portfolio(self, start=None):
        """
        Display the current stage of the portfolio summarizing the available balance of BTC, ETH, and USDT on both exchanges
        :param start: time when the execution of the bot started
        :return: current balance of assets on the exchanges
        """
        runtime = str(datetime.now() - start)
        date = datetime.now().strftime("%d.%m.%Y, %H:%M:%S")
        print("\n////////////////////////////////////////////////////////////////////////////////////////////////\n"
              f"Arbitrage bot running for {runtime}.\n"
              f"Current date and time: {date}\n"
              "Current stage of portfolio:")
        Binance_portfolio = self.Binance_client.get_portfolio()
        Bybit_portfolio = self.Bybit_client.get_portfolio()
        if Binance_portfolio is None or Bybit_portfolio is None or "result" not in Bybit_portfolio or "list" not in \
                Bybit_portfolio["result"]:
            return dict()
        currencies = dict()

        for asset in Binance_portfolio:
            if float(asset["balance"]) != 0:
                asset_name = asset["asset"]
                currencies[asset_name] = list()
                currencies[asset_name].append(round(float(asset["balance"]), 3))
                currencies[asset_name].append(0)

        for asset in Bybit_portfolio["result"]["list"]:
            if float(asset["walletBalance"]) != 0:
                asset_name = asset["coin"]
                if asset_name not in currencies.keys():
                    currencies[asset_name] = list()
                    currencies[asset_name].append(0)
                    currencies[asset_name].append(round(float(asset["walletBalance"]), 3))
                else:
                    currencies[asset_name][1] = round(float(asset["walletBalance"]), 3)

        currencies_arr = list()
        index = 0
        for currency_key, currency_values in currencies.items():
            currencies_arr.append(list())
            currencies_arr[index].append(currency_key)
            currencies_arr[index].append(currency_values[0])
            currencies_arr[index].append(currency_values[1])
            currencies_arr[index].append(currency_values[0] + currency_values[1])

            percentage_change = ""
            if self.portfolio is not None:
                percentage_change = ((currency_values[0] + currency_values[1]) / sum(
                    self.portfolio[currency_key])) * 100 - 100
            currencies_arr[index].append(percentage_change)
            index += 1

        print(tabulate(currencies_arr, headers=["ASSET", "BINANCE", "BYBIT", "TOTAL", "PERCENTAGE CHANGE"],
                       floatfmt=".3f"))
        return currencies

    def load_portfolio(self):
        """
        Load the stage of the portfolio saved from the previous run
        """
        with open("../portfolio.json", "r") as file:
            self.portfolio = json.load(file)

    def save_portfolio(self):
        """
        Save the current stage of the portfolio after the execution is stopped
        """
        with open("../portfolio.json", "w") as file:
            json.dump(self.portfolio, file)

    @staticmethod
    def get_traded_amount(bid_qty=None, ask_qty=None, base_asset=None, quote_asset=None, price=None, fee=None):
        """
        Obtain the minimal traded amount based on the current stage of the order book
        :param bid_qty: quantity of bid
        :param ask_qty: quantity of ask
        :param base_asset: base asset of the traded cryptocurrency pair
        :param quote_asset: quote asset of the traded cryptocurrency pair
        :param price: ask price
        :param fee: transaction fee
        :return: minimal traded amount
        """
        if bid_qty is None or ask_qty is None or base_asset is None or quote_asset is None or price is None or \
                fee is None:
            raise ValueError("Not enough values for the calculation of the traded amount provided.")

        quote_asset = quote_asset / ((1 + fee) * price)
        return min(base_asset, quote_asset, bid_qty, ask_qty)

    def check_Binance_margin(self, asset=None, amount=None):
        """
        Check if Binance provides sufficient trading margin for the specified asset
        :param asset: asset to be traded
        :param amount: amount of the asset
        :return: True if the margin is sufficient; False otherwise
        """
        if asset is None or amount is None:
            raise ValueError("Not enough information to check margin on Binance were provided.")

        portfolio = self.Binance_client.get_portfolio()
        if portfolio is None:
            return False

        for portfolio_asset in portfolio:
            if portfolio_asset["asset"] == asset:
                if float(portfolio_asset["withdrawAvailable"]) < amount:
                    return False
                return True
        return False

    def check_Bybit_margin(self, asset=None, amount=None):
        """
        Check if Bybit provides sufficient trading margin for the specified asset
        :param asset: asset to be traded
        :param amount: amount of the asset
        :return: True if the margin is sufficient; False otherwise
        """
        if asset is None or amount is None:
            raise ValueError("Not enough information to check margin on Bybit were provided.")

        portfolio = self.Bybit_client.get_portfolio()
        if portfolio is None or "result" not in portfolio or "list" not in portfolio["result"]:
            return Flase

        portfolio = portfolio["result"]["list"]
        for portfolio_asset in portfolio:
            if portfolio_asset["coin"] == asset:
                if float(portfolio_asset["availableBalance"]) < amount:
                    return False
                return True
        return False

    def check_sufficient_margin(self, buying_client=None, selling_client=None, base_asset=None, quote_asset=None,
                                traded_amount=None, price=None):
        """
        Check if both exchanges provide sufficient trading margin for the specified asset
        :param buying_client: exchange, where the asset is to be bought
        :param selling_client: exchange, where the asset is to be sold
        :param base_asset: base asset of the cryptocurrency pair
        :param quote_asset: quote asset of the cryptocurrency pair
        :param traded_amount: traded amount of the asset
        :param price: ask price on the exchange, where the asset is to be bought
        :return: True if the margin is sufficient; False otherwise with the corresponding traded amount
        """
        if buying_client is None or selling_client is None or base_asset is None or quote_asset is None or \
                traded_amount is None or price is None:
            raise ValueError("Not enough information to check sufficient margin were provided.")

        if base_asset == "BTC" and traded_amount > 0.33:
            traded_amount = 0.33
        if base_asset == "ETH" and traded_amount > 5:
            traded_amount = 5

        if isinstance(buying_client, type(Binance_operations)):
            try:
                if not self.check_Binance_margin(quote_asset, (traded_amount * price)):
                    return False, traded_amount
            except ValueError:
                return False, traded_amount
        else:
            try:
                if not self.check_Bybit_margin(quote_asset, (traded_amount * price)):
                    return False, traded_amount
            except ValueError:
                return False, traded_amount

        if isinstance(selling_client, type(Binance_operations)):
            try:
                return self.check_Binance_margin(base_asset, traded_amount), traded_amount
            except ValueError:
                return False, traded_amount
        else:
            try:
                return self.check_Bybit_margin(base_asset, traded_amount), traded_amount
            except ValueError:
                return False, traded_amount

    def on_press(self, key):
        """
        Keyboard listener waiting for Esc to be pressed
        :param key: pressed key
        """
        if key == keyboard.Key.esc:
            self.running = False
            return

    def start_listener(self):
        """
        Start of the keyboard listener
        """
        listener = keyboard.Listener(on_press=self.on_press)
        listener.start()

    def check_open_positions(self, client=None, counter=None, prices=None):
        """
        Check if there are open positions for the provided exchange
        :param client: provided exchange
        :param counter: counter of position checking
        :param prices: bid and ask prices and quantities
        :return: new value of counter
        """
        counter = self.get_open_positions(client, counter)
        if counter == 5:
            self.cancel_open_positions(client, prices)
            return 0
        return counter

    def get_open_positions(self, client=None, counter=None):
        """
        Get open positions on the provided exchange
        :param client: provided exchange
        :param counter: counter of position checking
        :return: new value of counter
        """
        positions = list()
        for pair in self.Binance_crypto_pairs:
            pair_positions = client.get_open_positions(pair["symbol"])
            for position in pair_positions:
                if "positionAmt" in position.keys() and float(position["positionAmt"]) != 0:
                    positions.extend(position)
                if "size" in position.keys() and float(position["size"]) != 0:
                    positions.extend(position)

        if len(positions) > 0:
            counter += 1
        return counter

    def cancel_open_positions(self, client=None, prices=None):
        """
        Cancel open positions when they are opened for too long
        :param client: provided exchange
        :param prices: bid and ask prices and quantities
        """
        positions = list()
        for pair in self.Binance_crypto_pairs:
            pair_positions = client.get_open_positions(pair["symbol"])
            for position in pair_positions:
                if "positionAmt" in position.keys() and float(position["positionAmt"]) != 0:
                    positions.append(position)
                if "size" in position.keys() and float(position["size"]) != 0:
                    positions.append(position)

        for position in positions:
            if "positionAmt" in position.keys():
                if float(position["positionAmt"]) < 0:
                    purchase = client.place_order(position["symbol"], "BUY", "LIMIT",
                                                  abs(float(position["positionAmt"])), prices["ask_price_Binance"])
                    if purchase is None:
                        return
                if float(position["positionAmt"]) > 0:
                    purchase = client.place_order(position["symbol"], "SELL", "LIMIT",
                                                  abs(float(position["positionAmt"])), prices["bid_price_Binance"])
                    if purchase is None:
                        return
            else:
                if position["side"] == "Sell":
                    purchase = client.place_order(position["symbol"], "Buy", "Limit", position["size"],
                                                  prices["ask_price_Bybit"])
                    if purchase is None:
                        return
                if position["side"] == "Buy":
                    purchase = client.place_order(position["symbol"], "Sell", "Limit", position["size"],
                                                  prices["bid_price_Bybit"])
                    if purchase is None:
                        return

    def summarize_price_data(self, Binance_pair=None):
        """
        Obtain bid and ask prices and quantities from both exchanges
        :return: bod and ask prices and quantities
        """
        prices = {"bid_price_Binance": 0, "ask_price_Binance": 0, "bid_qty_Binance": 0, "ask_qty_Binance": 0,
                  "bid_price_Bybit": 0, "ask_price_Bybit": 0, "bid_qty_Bybit": 0, "ask_qty_Bybit": 0}

        Binance_pair_data = self.Binance_client.get_pair_data(Binance_pair["symbol"])
        if Binance_pair_data is None:
            return None
        for data in Binance_pair_data:
            if data["symbol"] == Binance_pair["symbol"]:
                prices["bid_price_Binance"] = float(data["bidPrice"])
                prices["ask_price_Binance"] = float(data["askPrice"])
                prices["bid_qty_Binance"] = float(data["bidQty"])
                prices["ask_qty_Binance"] = float(data["askQty"])

        Bybit_pair = self.Bybit_crypto_pairs[self.Binance_crypto_pairs.index(Binance_pair)]
        Bybit_pair_data = self.Bybit_client.get_pair_data(Bybit_pair["symbol"])
        if Bybit_pair_data is None or "result" not in Bybit_pair_data or "a" not in Bybit_pair_data["result"] \
                or "b" not in Bybit_pair_data["result"]:
            return None
        if len(Bybit_pair_data["result"]["b"]) == 0 or len(Bybit_pair_data["result"]["b"][0]) < 2 or len(
                Bybit_pair_data["result"]["a"]) == 0 or len(Bybit_pair_data["result"]["a"][0]) < 2:
            return None

        prices["bid_price_Bybit"] = float(Bybit_pair_data["result"]["b"][0][0])
        prices["bid_qty_Bybit"] = float(Bybit_pair_data["result"]["b"][0][1])
        prices["ask_price_Bybit"] = float(Bybit_pair_data["result"]["a"][0][0])
        prices["ask_qty_Bybit"] = float(Bybit_pair_data["result"]["a"][0][1])

        if (prices["ask_price_Binance"] == 0 and prices["ask_price_Bybit"] == 0) or \
                (prices["bid_price_Binance"] == 0 and prices["bid_price_Bybit"] == 0):
            return None
        return prices

    def check_traded_amount(self, prices=None, pair=None):
        """
        Check if the traded amount can be obtained and meets the given requirements
        :param prices: bid and ask prices and quantities
        :param pair: cryptocurrency pair to be analyzed
        :return: traded amount
        """
        base_asset_qty = self.portfolio[pair["base_asset"]][1]
        quote_asset_qty = self.portfolio[pair["quote_asset"]][0]

        try:
            traded_amount = self.get_traded_amount(prices["bid_qty_Bybit"], prices["ask_qty_Binance"], base_asset_qty,
                                                   quote_asset_qty, prices["ask_price_Binance"], pair["taker_fee"])
        except ValueError:
            return None

        if (pair["base_asset"] == "BTC" and traded_amount > 0.33) or (pair["base_asset"] == "ETH" and traded_amount > 5):
            return None
        return traded_amount

    def perform_trade(self, buying_client=None, selling_client=None, pair=None, traded_amount=None, ask_price=None,
                      bid_price=None, profit=None, percentage_profit=None, prices=None, start=None):
        """
        Perform both sides of the purchase with a check of sufficient amount for the trade and an update of the portfolio
        :param buying_client: exchange where the cryptocurrency is bought
        :param selling_client: exchange where the cryptocurrency is sold
        :param pair: traded cryptocurrency pair
        :param traded_amount: traded amount
        :param ask_price: ask price on buying exchange
        :param bid_price: bid price on selling exchange
        :param profit: numerical profit of arbitrage
        :param percentage_profit: percentage profit of arbitrage
        :param prices: bid and ask prices and quantities
        :param start: datetime of start of the bot
        """
        self.Binance_position_counter = self.check_open_positions(self.Binance_client, self.Binance_position_counter,
                                                                  prices)
        self.Bybit_position_counter = self.check_open_positions(self.Bybit_client, self.Bybit_position_counter, prices)

        try:
            sufficient_margin, traded_amount = \
                self.check_sufficient_margin(buying_client, selling_client, pair["base_asset"], pair["quote_asset"],
                                             traded_amount, ask_price)
            if not sufficient_margin:
                return
        except ValueError:
            return

        if profit is None and percentage_profit is None:
            print("Arbitrage possible with Random Forest for {:0.2f} amount".format(traded_amount))
        else:
            print("Arbitrage possible, {}, profit of {:0.2f}$ ({:0.2f}%)".format(pair["symbol"], profit, percentage_profit))

        purchase_success = buying_client.place_order(pair["symbol"], "BUY", "LIMIT", traded_amount, ask_price)
        if purchase_success is None:
            purchase_success = buying_client.place_order(pair["symbol"], "Buy", "Limit", traded_amount, ask_price)
            if purchase_success is None:
                return

        purchase_success = selling_client.place_order(pair["symbol"], "SELL", "LIMIT", traded_amount, bid_price)
        if purchase_success is None:
            purchase_success = selling_client.place_order(pair["symbol"], "Sell", "Limit", traded_amount, bid_price)
            if purchase_success is None:
                return

        self.display_portfolio(start)
        if not self.portfolio:
            return

    def machine_learning_bot(self, start=None):
        """
        Execution of the arbitrage bot with Machine Learning inclusion
        :param start: datetime of start of the bot
        """
        Binance_pair = self.Binance_crypto_pairs[1]
        Bybit_pair = self.Bybit_crypto_pairs[self.Binance_crypto_pairs.index(Binance_pair)]

        Binance_OHLCV = self.Binance_client.get_historical_klines(Binance_pair["symbol"], "1m",
                                                                  datetime.now().timestamp() * 1000, 2)
        Bybit_OHLCV = self.Bybit_client.get_historical_klines(Binance_pair["symbol"], 1, datetime.now().timestamp()
                                                              * 1000 - 60 * 1000 * 2, 2)
        if Binance_OHLCV is None or Bybit_OHLCV is None or len(Binance_OHLCV) < 2 or len(Bybit_OHLCV) < 2 or \
                len(Binance_OHLCV[1]) < 6 or len(Bybit_OHLCV[1]) < 6:
            return

        Binance_change = (float(Binance_OHLCV[1][1]) - float(Binance_OHLCV[0][1])) / float(
            Binance_OHLCV[0][1]) * 100
        Bybit_change = (float(Bybit_OHLCV[1][1]) - float(Bybit_OHLCV[0][1])) / float(Bybit_OHLCV[0][1]) * 100
        dataset_row = [int(datetime.now().timestamp() * 1000), Binance_OHLCV[1][1], Binance_OHLCV[1][2],
                       Binance_OHLCV[1][3], Binance_OHLCV[1][4], Binance_OHLCV[1][5],
                       Bybit_OHLCV[1][1], Bybit_OHLCV[1][2], Bybit_OHLCV[1][3], Bybit_OHLCV[1][4],
                       Bybit_OHLCV[1][5], Binance_change, Bybit_change]

        Binance_opportunity = float(Binance_OHLCV[1][1]) - float(Bybit_OHLCV[1][1])
        Bybit_opportunity = float(Bybit_OHLCV[1][1]) - float(Binance_OHLCV[1][1])
        if Binance_opportunity < 0 and Bybit_opportunity < 0 and abs(Binance_opportunity) < abs(
                Bybit_opportunity):
            Binance_opportunity = 0

        with open("D:/FIIT/BakalarskaPraca/arbitrage_bot/best_models/best_model_ETHUSDT.sav", "rb") as file:
            model = pickle.load(file)
            prediction = model.predict([dataset_row])

            if prediction[0] == 1:
                print("Profitable arbitrage in next time interval predicted.")
                time.sleep(300)
                prices = self.summarize_price_data(Binance_pair)

                if Binance_opportunity < 0:
                    traded_amount = self.check_traded_amount(prices, Bybit_pair)
                    if traded_amount is None:
                        return

                    self.perform_trade(self.Binance_client, self.Bybit_client, Binance_pair, traded_amount,
                                       prices["ask_price_Binance"], prices["bid_price_Bybit"], None, None, prices,
                                       start)

                if Bybit_opportunity < 0:
                    traded_amount = self.check_traded_amount(prices, Binance_pair)
                    if traded_amount is None:
                        return

                    self.perform_trade(self.Bybit_client, self.Binance_client, Binance_pair, traded_amount,
                                       prices["ask_price_Bybit"], prices["bid_price_Binance"], None, None, prices,
                                       start)

            else:
                print("Profitable arbitrage in next time interval not predicted.")

    # source https://github.com/kelvinau/crypto-arbitrage/blob/2f8956fe37b62002985edfba84006f19490697de/engines/exchange_arbitrage.py#L6
    # inspired by the method start_engine(self)
    def arbitrage_search(self):
        """
        Execution of the simple arbitrage bot
        """
        start = datetime.now()
        self.load_portfolio()
        self.display_portfolio(start)

        while self.running:
            self.start_listener()
            # self.display_portfolio(start)
            if not self.portfolio:
                continue

            if self.machine_learning_inclusion:
                self.machine_learning_bot(start)
                time.sleep(60)
                continue

            for Binance_pair in self.Binance_crypto_pairs:
                prices = self.summarize_price_data(Binance_pair)
                if prices is None:
                    continue

                Bybit_pair = self.Bybit_crypto_pairs[self.Binance_crypto_pairs.index(Binance_pair)]
                Binance_opportunity = prices["ask_price_Binance"] - prices["bid_price_Bybit"]
                Bybit_opportunity = prices["ask_price_Bybit"] - prices["bid_price_Binance"]
                if Binance_opportunity < 0 and Bybit_opportunity < 0 and abs(Binance_opportunity) < abs(
                        Bybit_opportunity):
                    Binance_opportunity = 0

                # buy crypto on Binance, sell it on Bybit
                if Binance_opportunity < 0:
                    traded_amount = self.check_traded_amount(prices, Bybit_pair)
                    if traded_amount is None:
                        continue

                    fee = Binance_pair["taker_fee"] / 100 * traded_amount * prices["ask_price_Binance"] + \
                          Bybit_pair["taker_fee"] / 100 * traded_amount * prices["bid_price_Bybit"]
                    profit = abs(Binance_opportunity * traded_amount) - fee
                    percentage_profit = profit / prices["ask_price_Binance"] * 100

                    if percentage_profit > self.min_percentage_profit:
                        self.perform_trade(self.Binance_client, self.Bybit_client, Binance_pair, traded_amount,
                                           prices["ask_price_Binance"], prices["bid_price_Bybit"], profit,
                                           percentage_profit, prices, start)

                # buy crypto on Bybit, sell it on Binance
                if Bybit_opportunity < 0:
                    traded_amount = self.check_traded_amount(prices, Binance_pair)
                    if traded_amount is None:
                        continue

                    fee = Bybit_pair["taker_fee"] / 100 * traded_amount * prices["ask_price_Bybit"] + \
                          Binance_pair["taker_fee"] / 100 * traded_amount * prices["bid_price_Binance"]
                    profit = abs(Bybit_opportunity * traded_amount) - fee
                    percentage_profit = profit / prices["ask_price_Bybit"] * 100

                    if percentage_profit > self.min_percentage_profit:
                        self.perform_trade(self.Bybit_client, self.Binance_client, Binance_pair, traded_amount,
                                           prices["ask_price_Bybit"], prices["bid_price_Binance"], profit,
                                           percentage_profit, prices, start)

            time.sleep(60)
        self.portfolio = self.display_portfolio(start)
        self.save_portfolio()
