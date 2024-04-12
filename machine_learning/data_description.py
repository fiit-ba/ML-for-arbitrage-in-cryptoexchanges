from load_dataset import Load_dataset


class Data_description:
    def __init__(self, pairs):
        self.load_dataset = Load_dataset(pairs)
        self.datasets = self.load_dataset.load_preprocessed_datasets()

        self.basic_data_description()
        self.descriptive_statistics()
        self.correlation_with_arbitrage()

    def basic_data_description(self):
        """
        Basic description of datasets, including number of records and attributes
        """
        for pair_key, pair in self.datasets.items():
            for interval_key, interval in pair.items():
                n_records = interval.shape[0]
                n_attributes = interval.shape[1]
                print(f"{pair_key} for {interval_key} interval:")
                print(f"\tnumber of records:\t\t{n_records}\n\tnumber of attributes:\t{n_attributes}")

    def descriptive_statistics(self):
        """
        Descriptive statistics of datasets include count, mean, standard deviation, minimum, maximum, and 25%, 50%, and
        75% quantiles
        """
        for pair_key, pair in self.datasets.items():
            for interval_key, interval in pair.items():
                print(interval.loc[:, "open_Binance":"change_Bybit"].describe())

    def correlation_with_arbitrage(self):
        """
        Correlation of all columns, including price data, with the arbitrage column and sorting them in descending order
        """
        for pair_key, pair in self.datasets.items():
            for interval_key, interval in pair.items():
                print(f"\n{pair_key} for {interval_key} interval on Binance")
                corr = interval.loc[:, "open_Binance":].corr().abs()["arbitrage"].sort_values(ascending=False)
                print(corr[1:])

                print(f"\n{pair_key} for {interval_key} interval on Bybit")
                corr = interval.loc[:, "open_Bybit":].corr().abs()["arbitrage"].sort_values(ascending=False)
                print(corr[1:])
