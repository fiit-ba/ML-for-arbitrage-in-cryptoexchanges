import pandas as pd
import numpy as np
import csv

from load_dataset import Load_dataset

MIN_PERCENTAGE_PROFIT = 0.01


class Data_preprocessing:
    def __init__(self, pairs):
        self.pairs = pairs
        self.load_dataset = Load_dataset(self.pairs)
        self.datasets = self.load_dataset.load_datasets()

        self.align_datasets()
        self.concentrate_datasets()
        for pair_key, pair in self.datasets.items():
            for interval_key, interval in pair.items():
                print(f"Preprocessing {pair_key} for {interval_key}")
                self.datasets[pair_key][interval_key] = self.handle_outliers(interval)
                self.datasets[pair_key][interval_key] = self.add_change(interval)
                self.datasets[pair_key][interval_key] = \
                    self.identify_arbitrage(self.datasets[pair_key][interval_key], pair_key)

        self.save_preprocessed_datasets()

    def align_datasets(self):
        """
        Align datasets with the same cryptocurrency pair and time interval to start and end with the same timestamp
        """
        for pair_key, pair in self.datasets.items():
            start_date, end_date = None, None
            for interval_key, interval in pair.items():
                for exchange_key, exchange in interval.items():
                    self.datasets[pair_key][interval_key][exchange_key] = self.clean_data(exchange, pair_key,
                                                                                          interval_key, exchange_key)

                    for currency_pair in self.pairs:
                        start = self.datasets[currency_pair][interval_key][exchange_key].iloc[-1, 2]
                        end = self.datasets[currency_pair][interval_key][exchange_key].iloc[0, 2]

                        if start_date is None or start < start_date:
                            start_date = start
                        if end_date is None or end > end_date:
                            end_date = end

                for exchange_key, exchange in interval.items():
                    for currency_pair in self.pairs:
                        data = self.datasets[currency_pair][interval_key][exchange_key]
                        self.datasets[currency_pair][interval_key][exchange_key] = \
                            data.drop(data[data["dateTime"] < end_date].index).reset_index(drop=True)

                        data = self.datasets[currency_pair][interval_key][exchange_key]
                        self.datasets[currency_pair][interval_key][exchange_key] = \
                            data.drop(data[data["dateTime"] > start_date].index).reset_index(drop=True)

    def concentrate_datasets(self):
        """
        Concentrate datasets with the same cryptocurrency pair and time interval into one file and rename the columns
        """
        for pair_key, pair in self.datasets.items():
            for interval_key, interval in pair.items():
                Binance_dataset = interval["Binance"]
                rename = {"Unnamed: 0": "Index", "date": "date", "dateTime": "dateTime", "open": "open_Binance",
                          "high": "high_Binance", "low": "low_Binance", "close": "close_Binance",
                          "volume": "volume_Binance"}
                Binance_dataset.rename(columns=rename, inplace=True)

                Bybit_dataset = interval["Bybit"].loc[:, ["open", "high", "low", "close", "volume"]]
                Binance_dataset = pd.concat([Binance_dataset, Bybit_dataset], axis=1)

                rename = {"open": "open_Bybit", "high": "high_Bybit", "low": "low_Bybit", "close": "close_Bybit",
                          "volume": "volume_Bybit"}
                Binance_dataset.rename(columns=rename, inplace=True)

                self.datasets[pair_key][interval_key] = Binance_dataset

    @staticmethod
    def clean_data(dataset, pair, interval, exchange):
        """
        Clean the dataset of null values if any of them occur
        :param dataset: dataset to be analyzed
        :param pair: name of the cryptocurrency pair in the dataset
        :param interval: name of the time interval of the dataset
        :param exchange: name of the exchange of the dataset
        :return: dataset without null values
        """
        for column in dataset.columns:
            if column != "date":
                dataset[column] = pd.to_numeric(dataset[column], errors="coerce")

        null_sum = dataset.isnull().sum()
        if null_sum.any() > 0:
            null_percentage = max(null_sum)/dataset.shape[0]
            print(f"NULL DATA FOUND\n{pair} for {interval} interval on {exchange} exchange contains {null_sum} "
                  f"({null_percentage}%) NULL values")

            if null_percentage < 0.1:
                dataset = dataset.dropna(how="any", axis=0)
            else:
                dataset = dataset.fillna(dataset.mean())

        return dataset

    @staticmethod
    def handle_outliers(dataset):
        """
        Delete extreme outliers lower than the 0,1% quantile or higher than the 99,9% quantile that indicate an error
        in the dataset
        :param dataset: dataset to be analyzed
        :return: dataset without outliers
        """
        for col_index in range(dataset.shape[1]):
            if dataset.columns[col_index] in ["open_Binance", "high_Binance", "low_Binance", "close_Binance"]:
                difference = []

                if col_index + 5 < dataset.shape[1]:
                    difference = dataset.iloc[:, col_index] - dataset.iloc[:, col_index + 5]

                low_quantile = difference.quantile(0.001)
                high_quantile = difference.quantile(0.999)
                for row_index in range(len(difference)):
                    if difference[row_index] < low_quantile or difference[row_index] > high_quantile:
                        if row_index < dataset.shape[0]:
                            dataset.iloc[row_index, :] = np.nan

        dataset.dropna(inplace=True)
        dataset.reset_index(drop=True, inplace=True)
        return dataset

    @staticmethod
    def add_change(dataset):
        """
        Add the percentage change between two consecutive records in the dataset, considering open prices on both
        exchanges
        :param dataset: dataset to be analyzed
        :return: dataset with appended change on Binance and Bybit
        """
        Binance_change = pd.Series(0, index=np.arange(dataset.shape[0]), name="change_Binance")
        Bybit_change = pd.Series(0, index=np.arange(dataset.shape[0]), name="change_Bybit")
        for index, row in dataset.iterrows():
            if index + 1 < dataset.shape[0]:
                Binance_change[index] = pd.Series((dataset.loc[index + 1, "open_Binance"] - row["open_Binance"]) /
                                                  row["open_Binance"]) * 100
                Bybit_change[index] = pd.Series((dataset.loc[index + 1, "open_Bybit"] - row["open_Bybit"]) /
                                                row["open_Bybit"]) * 100

        dataset = pd.concat([dataset, Binance_change], axis=1)
        dataset = pd.concat([dataset, Bybit_change], axis=1)
        return dataset

    @staticmethod
    def check_for_arbitrage(Binance_value, Bybit_value, pair):
        """
        Check if an occurrence of arbitrage is likely for the provided values
        :param Binance_value: price value on Binance
        :param Bybit_value: price value on Bybit
        :param pair: cryptocurrency pair analyzed
        :return: True if an occurrence of arbitrage is likely; False otherwise
        """
        taker_fee = 0.04
        percentage_profit = 0
        traded_amount = 0
        if pair == "BTCUSDT":
            traded_amount = 0.01
        if pair == "ETHUSDT":
            traded_amount = 1

        Binance_opportunity = Binance_value - Bybit_value
        Bybit_opportunity = Bybit_value - Binance_value

        if Binance_opportunity < 0 and Bybit_opportunity < 0 and abs(Binance_opportunity) < abs(Bybit_opportunity):
            Binance_opportunity = 0

        if Binance_opportunity < 0:
            fee = taker_fee * Binance_value * traded_amount + taker_fee * Bybit_value * traded_amount
            profit = abs(Binance_opportunity * traded_amount) - fee
            percentage_profit = profit / Binance_value * 100

        if Bybit_opportunity < 0:
            fee = taker_fee * Bybit_value * traded_amount + taker_fee * Binance_value * traded_amount
            profit = abs(Bybit_opportunity * traded_amount) - fee
            percentage_profit = profit / Bybit_value * 100

        if percentage_profit > MIN_PERCENTAGE_PROFIT:
            return True
        return False

    def identify_arbitrage(self, dataset, pair):
        """
        Identify an occurrence of probable arbitrage for each record and each pair of prices in the dataset
        :param dataset: dataset to be analyzed
        :param pair: cryptocurrency pair to be analyzed
        :return: dataset with the probable occurrence of an arbitrage
        """
        arbitrage = pd.Series(0, index=np.arange(dataset.shape[0]), name="arbitrage")

        for line in range(dataset.shape[0] - 1):
            Binance_columns = ["open_Binance", "high_Binance", "low_Binance", "close_Binance"]
            Bybit_columns = ["open_Bybit", "low_Bybit", "high_Bybit", "close_Bybit"]
            for Binance_value, Bybit_value in zip(dataset.loc[line, Binance_columns], dataset.loc[line, Bybit_columns]):
                if self.check_for_arbitrage(Binance_value, Bybit_value, pair):
                    arbitrage[line + 1] = pd.Series(1)
                    break

        dataset = pd.concat([dataset, arbitrage], axis=1)
        return dataset

    def save_preprocessed_datasets(self):
        """
        Save datasets after the pre-processing phase into the dataset_preprocessed dictionary
        """
        for pair_key, pair in self.datasets.items():
            for interval_key, interval in pair.items():
                filename = "./dataset_preprocessed/" + pair_key + "_" + interval_key + ".csv"
                interval.to_csv(filename, index=False)
