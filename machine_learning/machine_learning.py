from building_models import Building_models
from data_description import Data_description
from data_gathering import Data_gathering
from data_preprocessing import Data_preprocessing
from data_visualization import Data_visualization
from hypothesis_testing import Hypothesis_testing
from exchange_connection import Exchange_connection


class Machine_learning:
    def __init__(self, cryptocurrency_pairs):
        self.cryptocurrency_pairs = cryptocurrency_pairs
        self.exchange_connection = Exchange_connection()

        self.Binance_client = self.exchange_connection.Binance_client
        self.Bybit_client = self.exchange_connection.Bybit_client
        if self.Binance_client is None or self.Bybit_client is None or self.cryptocurrency_pairs is None:
            raise ValueError("Required data for starting of arbitrage bot not provided.")

        self.machine_learning_process()

    def machine_learning_process(self):
        """
        Execute all steps of the Machine Learnig process
        """
        Data_gathering(self.Binance_client, self.Bybit_client, self.cryptocurrency_pairs)
        Data_preprocessing(self.cryptocurrency_pairs)
        Data_description(self.cryptocurrency_pairs)
        Data_visualization(self.cryptocurrency_pairs)
        Building_models(self.cryptocurrency_pairs)
        hypothesis_testing = Hypothesis_testing("file")
        hypothesis_testing.perform_tests()


currency_pairs = ["BTCUSDT", "ETHUSDT"]
try:
    Machine_learning(currency_pairs)
except ValueError:
    quit()
