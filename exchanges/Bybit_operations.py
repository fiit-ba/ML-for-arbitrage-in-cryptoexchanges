class Bybit_operations:
    def __init__(self, Bybit_client=None):
        self.Bybit_client = Bybit_client

    def get_exchange_info(self):
        """
        :return: information about all available cryptocurrency pairs and all current prices
        """
        request_url = "/derivatives/v3/public/tickers"
        return self.Bybit_client.send_request(request_url, "GET")

    def get_portfolio(self):
        """
        :return: the balance of every asset available on the exchange
        """
        request_url = "/contract/v3/private/account/wallet/balance"
        return self.Bybit_client.process_query(request_url, "GET")

    def get_pair_data(self, symbol):
        """
        :param symbol: cryptocurrency symbol to be analyzed
        :return: the current price data and stage of the order book for the provided cryptocurrency
        """
        request_url = "/derivatives/v3/public/order-book/L2"
        params = {"symbol": symbol}
        return self.Bybit_client.send_request(request_url, "GET", params)

    def get_historical_klines(self, symbol=None, interval=None, start_date=None, limit=None):
        """
        :param symbol: cryptocurrency symbol required
        :param interval: interval between individual records
        :param start_date: timestamp of the first record
        :param limit: maximal number of the records
        :return: historical information about the evolution of currency prices
        """
        request_url = "/v5/market/kline"
        if limit is None:
            limit = 200
        params = {"category": "linear", "symbol": symbol, "interval": interval, "start": int(start_date),
                  "limit": limit}
        response = self.Bybit_client.send_request(request_url, "GET", params)

        if response is None or "result" not in response or "list" not in response["result"]:
            return None
        return response["result"]["list"]

    def place_order(self, symbol=None, side=None, order_type=None, quantity=None, price=None):
        """
        Place the new order with the provided attributes
        :param symbol: cryptocurrency pair to be traded
        :param side: side of the trade
        :param order_type: type of order
        :param quantity: traded amount
        :param price: limit price to be met
        :return: the success of placing a new order
        """
        request_url = "/contract/v3/private/order/create"
        params = '{"symbol": "' + symbol + '","side": "' + side + '","orderType": "' + order_type + '","qty": "' + \
                 str(quantity) + '","price": "' + str(price) + '","timeInForce": "GoodTillCancel"}'
        response = self.Bybit_client.process_query(request_url, "POST", params)
        if response is None or "result" not in response or len(response["result"]) == 0:
            return None
        return response

    def set_leverage(self, symbol=None):
        """
        Set leverage for all executed limit trades on the futures market
        :param symbol: cryptocurrency symbol to be analyzed
        :return: the success of setting leverage
        """
        request_url = "/v5/position/set-leverage"
        params = '{"category: "linear", ""symbol": "' + symbol + '"buyLeverage: 1, sellLeverage: 1"}'
        return self.Bybit_client.process_query(request_url, "POST", params)

    def get_taker_fee(self, symbol=None):
        """
        :param symbol: cryptocurrency pair to be analyzed
        :return: current transaction fees for both takers and markers of the market
        """
        request_url = "/v5/account/fee-rate"
        params = {"category": "linear", "symbol": symbol}
        return self.Bybit_client.process_query(request_url, "GET", params)

    def get_open_positions(self, symbol=None):
        """
        :param symbol: cryptocurrency pair to be analyzed
        :return: list of currently opened positions
        """
        if symbol is None:
            raise ValueError("Required information about open positions not provided.")

        request_url = "/v5/position/list"
        params = {"category": "linear", "symbol": symbol}
        response = self.Bybit_client.process_query(request_url, "GET", params)

        if response is None or "result" not in response or "list" not in response["result"]:
            return None
        return response["result"]["list"]
