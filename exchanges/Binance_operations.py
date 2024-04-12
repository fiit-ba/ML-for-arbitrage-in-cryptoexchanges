class Binance_operations:
    def __init__(self, Binance_client=None):
        self.Binance_client = Binance_client

    def get_exchange_info(self):
        """
        :return: information about rate limits, available symbols, and server time
        """
        request_url = "/fapi/v1/exchangeInfo"
        return self.Binance_client.send_request(request_url, "GET")

    def get_pair_data(self, pair=None):
        """
        :param pair: cryptocurrency pair to be analyzed
        :return: the current price data of the provided cryptocurrency
        """
        request_url = "/fapi/v1/ticker/bookTicker"
        pair = pair.split("_")[0]
        params = {"pair": pair}
        return self.Binance_client.send_request(request_url, "GET", params)

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
        request_url = "/fapi/v1/order"
        params = {"symbol": symbol, "side": side, "type": order_type, "quantity": quantity, "price": price,
                  "timeInForce": "GTC"}
        return self.Binance_client.process_query(request_url, "POST", params)

    def get_portfolio(self):
        """
        :return: the balance of every asset available on the exchange
        """
        request_url = "/fapi/v1/balance"
        return self.Binance_client.process_query(request_url, "GET")

    def get_historical_klines(self, symbol=None, interval=None, start_date=None, limit=None):
        """
        :param symbol: cryptocurrency symbol required
        :param interval: interval between individual records
        :param start_date: timestamp of the first record
        :param limit: maximal number of the records
        :return: historical information about the evolution of currency prices
        """
        request_url = "/fapi/v1/klines"
        if limit is None:
            limit = 200
        params = {"symbol": symbol, "interval": interval, "startTime": start_date, "limit": limit}
        return self.Binance_client.send_request(request_url, "GET", params)

    def set_leverage(self, symbol=None):
        """
        Set leverage for all executed limit trades on the futures market
        :param symbol: cryptocurrency symbol to be analyzed
        :return: the success of setting leverage
        """
        request_url = "/fapi/v1/leverage"
        params = {"symbol": symbol, "leverage": 1}
        return self.Binance_client.process_query(request_url, "POST", params)

    def get_taker_fee(self, symbol=None):
        """
        :param symbol: cryptocurrency pair to be analyzed
        :return: current transaction fees for both takers and markers of the market
        """
        request_url = "/fapi/v1/commissionRate"
        params = {"symbol": symbol}
        return self.Binance_client.process_query(request_url, "GET", params)

    def get_open_positions(self, symbol=None):
        """
        :param symbol: cryptocurrency pair to be analyzed
        :return: list of currently opened posistions
        """
        if symbol is None:
            raise ValueError("Required information about open positions not provided.")

        request_url = "/fapi/v2/positionRisk"
        params = {"symbol": symbol}
        return self.Binance_client.process_query(request_url, "GET", params)
