import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from load_dataset import Load_dataset

N_BINS = 50


class Data_visualization:
    def __init__(self, pairs):
        self.load_dataset = Load_dataset(pairs)
        self.datasets = self.load_dataset.load_preprocessed_datasets()

        self.visualize_prices()
        self.visualize_volume()
        self.visualize_change()

        self.visualize_correlations()

    def visualize_prices(self):
        """
        Visualize and compare open prices on both exchanges and for both cryptocurrency pairs
        """
        figure, axis = plt.subplots(2, 3, figsize=(10, 6), layout="constrained")
        x, y = 0, 0

        for pair_key, pair in self.datasets.items():
            for interval_key, interval in pair.items():
                date_list = pd.date_range(start='2022-9-22', end='2023-03-23', periods=7).tolist()
                date_labels = [date.strftime('%d.%m.%Y') for date in date_list]

                axis[x, y].plot(interval["open_Binance"], label="Binance", linewidth=2, color='#141c2c')
                axis[x, y].plot(interval["open_Bybit"], label="Bybit", linestyle=(0, (5, 10)), linewidth=1,
                                color='#f3ba2c')
                axis[x, y].set_title(f"{pair_key}, {interval_key}")

                axis[x, y].set_xticklabels(date_labels)
                axis[x, y].tick_params(axis='x', rotation=45)

                if pair_key == "BTCUSDT":
                    axis[x, y].set_ylim([10000, 30000])
                if pair_key == "ETHUSDT":
                    axis[x, y].set_ylim([0, 3000])
                y += 1
            x += 1
            y = 0

        figure.suptitle("Comparison of prices development on Binance and Bybit exchanges")
        plt.legend()
        plt.savefig('./images/open_prices.png')

    def visualize_volume(self):
        """
        Visualize a histogram of traded volume from both exchanges and for both cryptocurrency pairs
        """
        figure, axis = plt.subplots(2, 3, figsize=(10, 6), layout="constrained")
        x, y = 0, 0

        for pair_key, pair in self.datasets.items():
            for interval_key, interval in pair.items():
                volume_summary = [int(interval.loc[index, "volume_Binance"]) + int(interval.loc[index, "volume_Bybit"])
                                  for index in range(interval.shape[0])
                                  if (int(interval.loc[index, "volume_Binance"])
                                      + int(interval.loc[index, "volume_Bybit"])) > 0]
                volume_summary.sort()
                outliers = int(len(volume_summary) / 10)
                volume_summary = volume_summary[outliers:len(volume_summary) - outliers]

                axis[x, y].hist(volume_summary, bins=N_BINS, color='#ec9f04')
                axis[x, y].set_title(f"{pair_key}, {interval_key}")
                y += 1

            x += 1
            y = 0

        figure.suptitle("Histogram of traded volume on Binance and Bybit exchanges")
        plt.savefig('./images/traded_volume.png')

    def visualize_change(self):
        """
        Visualize and compare the percentage change between open prices on bot exchanges and for both cryptocurrency
        pairs
        """
        figure, axis = plt.subplots(2, 3, figsize=(10, 6), layout="constrained")
        x, y = 0, 0

        for pair_key, pair in self.datasets.items():
            for interval_key, interval in pair.items():
                date_list = pd.date_range(start='2022-9-22', end='2023-03-23', periods=7).tolist()
                date_labels = [date.strftime('%d.%m.%Y') for date in date_list]

                axis[x, y].plot(interval["change_Binance"], label="Binance", linewidth=2, color='#141c2c')
                axis[x, y].plot(interval["change_Bybit"], label="Bybit", linestyle=(0, (5, 10)), linewidth=1,
                                color='#f3ba2c')
                axis[x, y].set_title(f"{pair_key}, {interval_key}")

                axis[x, y].set_xticklabels(date_labels)
                axis[x, y].tick_params(axis='x', rotation=45)
                axis[x, y].set_ylim([-50, 50])
                y += 1
            x += 1
            y = 0

        figure.suptitle("Comparison of changes in prices on Binance and Bybit exchanges")
        plt.legend()
        plt.savefig('./images/change.png')

    def visualize_correlations(self):
        """
        Visualize a pairplot of each dataset with OHLCV price data from both exchanges separately
        """
        for pair_key, pair in self.datasets.items():
            for interval_key, interval in pair.items():
                print(f"\nCorrelation matrix for {pair_key} for {interval_key} interval on Binance exchange")
                print(interval[["open_Binance", "high_Binance", "low_Binance", "close_Binance", "volume_Binance",
                                "change_Binance"]].corr())

                graph = sns.pairplot(interval[["open_Binance", "high_Binance", "low_Binance", "close_Binance"]],
                                     height=1.5)
                graph.fig.suptitle(f"Pair plot for {pair_key} for {interval_key} interval on Binance exchange")
                plt.show()

                print(f"\nCorrelation matrix for {pair_key} for {interval_key} interval on Bybit exchange")
                print(interval[["open_Bybit", "high_Bybit", "low_Bybit", "close_Bybit", "volume_Bybit",
                                "change_Bybit"]].corr())

                graph = sns.pairplot(interval[["open_Bybit", "high_Bybit", "low_Bybit", "close_Bybit"]],
                                     height=1.5)
                graph.fig.suptitle(f"Pair plot for {pair_key} for {interval_key} interval on Bybit exchange")
                plt.show()
