from datetime import datetime
from dateutil.relativedelta import relativedelta
import pandas as pd
import numpy as np

ONE_MINUTE_DIFFERENCE = 60 * 1000 * 200
FIVE_MINUTES_DIFFERENCE = 5 * ONE_MINUTE_DIFFERENCE
FIFTEEN_MINUTES_DIFFERENCE = 15 * ONE_MINUTE_DIFFERENCE


class Data_gathering:
    def __init__(self, Binance_client=None, Bybit_client=None, pairs=None):
        self.Binance_client = Binance_client
        self.Bybit_client = Bybit_client
        self.pairs = pairs

        self.start_date = self.get_start_date()
        self.end_date = self.get_end_date()
        try:
            self.check_params()
        except ValueError:
            return

        self.get_Binance_historical_data()
        self.get_Bybit_historical_data()

    def check_params(self):
        """
        Check the availability of the required parameters for data gathering
        """
        if self.Binance_client is None or self.Bybit_client is None:
            raise ValueError("Requested connection to exchange not provided.")
        if self.pairs is None:
            raise ValueError("At least one cryptocurrency pair has to be provided.")
        if self.start_date is None:
            raise ValueError("Date to set the starting of dataset is required.")
        if self.end_date is None:
            raise ValueError("Date to set the ending of dataset is required.")

    @staticmethod
    def get_end_date():
        """
        Get the end date of the gathered dataset, which is half a year from today's date
        :return: end date in milliseconds
        """
        half_year_ago = datetime.now() - relativedelta(days=183)
        half_year_ago = half_year_ago.strftime("%d.%m.%Y %H:%M:%S.%f")
        date_time = datetime.strptime(half_year_ago, "%d.%m.%Y %H:%M:%S.%f")
        return date_time.timestamp() * 1000

    @staticmethod
    def get_start_date():
        """
        Get the start date of the gathered dataset corresponding to today's date
        :return: start date in milliseconds
        """
        today = datetime.now().strftime("%d.%m.%Y %H:%M:%S.%f")
        date_time = datetime.strptime(today, "%d.%m.%Y %H:%M:%S.%f")
        return date_time.timestamp() * 1000

    @staticmethod
    def interpret_interval(interval=None, intervals=None):
        """
        Interpret the time interval as a millisecond difference between the timestamps of the two consecutive records
        :param interval: current time interval
        :param intervals: list of all available time intervals in ascending order
        :return: time interval in milliseconds
        """
        if interval is None:
            raise ValueError("Requested time interval not provided.")
        if intervals is None:
            raise ValueError("Requested list of available intervals not provided.")

        if interval == intervals[0]:
            return ONE_MINUTE_DIFFERENCE
        elif interval == intervals[1]:
            return FIVE_MINUTES_DIFFERENCE
        else:
            return FIFTEEN_MINUTES_DIFFERENCE

    @staticmethod
    def get_partial_historical_data(client=None, pair=None, interval=None, start_date=None, columns=None):
        """
        Obtain partial historical data from the specified exchange based on the provided start date
        :param client: exchange to be used
        :param pair: cryptocurrency pair to be analyzed
        :param interval: current time interval between individual records
        :param start_date: current start date of the partial dataset
        :param columns: names of the returned columns
        :return: partial dataset
        """
        data = client.get_historical_klines(pair, interval, start_date)
        if data is None:
            return []
        partial_historical_data = pd.DataFrame(data)
        partial_historical_data.columns = columns
        partial_historical_data["date"] = [datetime.fromtimestamp(int(d) / 1000) for d in
                                           partial_historical_data.iloc[:, 0]]
        return partial_historical_data.loc[:, ["date", "dateTime", "open", "high", "low", "close", "volume"]]

    def get_Binance_historical_data(self):
        """
        Obtain a dataset of historical prices from the Binance exchange
        """
        intervals = ["1m", "5m", "15m"]

        for interval in intervals:
            try:
                timestamp_interval = self.interpret_interval(interval, intervals)
            except ValueError:
                return

            for pair in self.pairs:
                historical_data = pd.DataFrame()
                current_start_date = self.start_date - timestamp_interval

                while current_start_date > (self.end_date - timestamp_interval):
                    partial_historical_data = self.get_partial_historical_data(self.Binance_client, pair, interval,
                                                                               current_start_date,
                                                                               ["dateTime", "open", "high", "low",
                                                                                "close", "volume", "closeTime",
                                                                                "quoteAssetVolume", "numberOfTrades",
                                                                                "takerBuyBaseVol", "takerBuyQuoteVol",
                                                                                "ignore"])
                    if partial_historical_data is None:
                        continue

                    historical_data = pd.concat([partial_historical_data, historical_data], axis=0, ignore_index=True, keys=None)
                    previous_start_date = current_start_date
                    current_start_date = historical_data.loc[0, "dateTime"] - timestamp_interval
                    if previous_start_date == current_start_date:
                        break

                filename = "./dataset/Binance_data_" + pair + "_" + interval + ".csv"
                historical_data.to_csv(filename, index=True)

    def get_Bybit_historical_data(self):
        """
        Obtain a dataset of historical prices from the Bybit exchange
        """
        intervals = [1, 5, 15]

        for interval in intervals:
            try:
                timestamp_interval = self.interpret_interval(interval, intervals)
            except ValueError:
                return

            for pair in self.pairs:
                historical_data = pd.DataFrame()
                current_start_date = self.start_date - timestamp_interval

                while current_start_date > (self.end_date - timestamp_interval):
                    partial_historical_data = self.get_partial_historical_data(self.Bybit_client, pair, interval,
                                                                               current_start_date,
                                                                               ["dateTime", "open", "high", "low",
                                                                                "close", "volume", "turnover"])
                    if partial_historical_data is None:
                        continue
                    partial_historical_data = partial_historical_data.reindex(np.arange(199, -1, -1)).set_index(np.arange(200))
                    historical_data = pd.concat([partial_historical_data, historical_data], axis=0, ignore_index=True, keys=None)
                    previous_start_date = current_start_date
                    current_start_date = int(historical_data.loc[0, "dateTime"]) - timestamp_interval
                    if previous_start_date == current_start_date:
                        break

                if interval == 1:
                    str_interval = "1m"
                elif interval == 5:
                    str_interval = "5m"
                else:
                    str_interval = "15m"

                filename = "./dataset/Bybit_data_" + pair + "_" + str_interval + ".csv"
                historical_data.to_csv(filename, index=True)
