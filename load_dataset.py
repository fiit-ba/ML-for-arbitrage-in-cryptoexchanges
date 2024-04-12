from os import listdir
import pandas as pd


class Load_dataset:
    def __init__(self, pairs):
        self.pairs = pairs
        self.datasets = {}

    def load_datasets(self):
        """
        Load gathered datasets for further preprocessing, divided according to pair, time interval, and exchange
        :return: loaded datasets
        """
        for pair in self.pairs:
            self.datasets[pair] = {}

        for pair in self.datasets:
            self.datasets[pair] = {"1m": {"Binance": None, "Bybit": None}, "5m": {"Binance": None, "Bybit": None},
                                   "15m": {"Binance": None, "Bybit": None}}

        for file in listdir("./dataset"):
            first_underscore = file.find('_')
            exchange = file[0:first_underscore]
            second_underscore = file.find('_', first_underscore + 1)
            pair = file[(second_underscore + 1):(second_underscore + 8)]
            third_underscore = file.find('_', second_underscore + 1)
            interval = file[(third_underscore + 1):(third_underscore + 3)]
            if interval[-1] != 'm':
                interval += file[third_underscore + 3]

            dataset = pd.read_csv("./dataset/" + file, index_col=False)
            self.datasets[pair][interval][exchange] = dataset

        return self.datasets

    def load_preprocessed_datasets(self):
        """
        Load preprocessed datasets divided according to pair and time interval
        :return: loaded datasets
        """
        for pair in self.pairs:
            self.datasets[pair] = {}

        for pair in self.datasets:
            self.datasets[pair] = {"1m": None, "5m": None, "15m": None}

        for file in listdir("./dataset_preprocessed"):
            underscore = file.find('_')
            pair = file[0:underscore]
            dot = file.find('.')
            interval = file[(underscore + 1):dot]

            dataset = pd.read_csv("./dataset_preprocessed/" + file, index_col=False)
            self.datasets[pair][interval] = dataset

        return self.datasets

    def load_preprocessed_datasets_for_training(self):
        """
        Load preprocessed datasets divided according to pair and time interval without index and date columns
        :return: loaded datasets
        """
        self.load_preprocessed_datasets()

        for pair_key, pair in self.datasets.items():
            for interval_key in pair.keys():
                self.datasets[pair_key][interval_key] = self.datasets[pair_key][interval_key].iloc[:, 2:]

        return self.datasets
