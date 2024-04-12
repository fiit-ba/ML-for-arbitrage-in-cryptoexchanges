
# Cryptocurrency arbitrage trading bot with Machine Learning  

Cryptocurrency bot providing algorithmic execution of trading BTCUSDT  and ETHUSDT pairs on Binance and Bybit exchanges using an arbitrage strategy. This strategy consists of infinitely searching for arbitrage opportunities between the mentioned exchanges buying an asset on one exchange while simultaneously selling it on the second exchange with the calculation of the potential profit beforehead. The minimal profit for an arbitrage to be executed is 0.01%, and the trades are executed on the futures market, opening and closing limit positions when performing an arbitrage. 
  
### Requirements:  
1. User's account on Binance and Bybit exchanges  
2. API and secret keys from both exchanges  
3. A non-zero balance of the traded assets (BTC, ETH, and USDT) on both exchanges  
4. Python 3.8.2 or all compatible versions supporting the libraries listed in the next point
5. The following libraries are available:  
```text  
pandas~=1.5.1  
tabulate~=0.9.0  
pynput~=1.7.6  
numpy~=1.23.2  
scikit-learn~=1.1.3  
imblearn~=0.0  
requests~=2.25.1  
matplotlib~=3.5.3  
seaborn~=0.12.2  
scipy~=1.9.3  
```  
  
## Starting of the bot  
The arbitrage bot starts with the following command:  
```bash  
python3 main.py
```  
  
<div style="page-break-after: always;"></div>
Afterwards, the user is asked to choose between a standard run and a run with a Machine Learning model. In the first run, the user is asked to provide API and secret keys for both exchanges.  

```bash  
Binance API key: 𝘪𝘯𝘴𝘦𝘳𝘵 𝘺𝘰𝘶𝘳 𝘉𝘪𝘯𝘢𝘯𝘤𝘦 𝘈𝘗𝘐 𝘬𝘦𝘺  
Binance secret key: 𝘪𝘯𝘴𝘦𝘳𝘵 𝘺𝘰𝘶𝘳 𝘉𝘪𝘯𝘢𝘯𝘤𝘦 𝘴𝘦𝘤𝘳𝘦𝘵 𝘬𝘦𝘺  
Bybit API key: 𝘪𝘯𝘴𝘦𝘳𝘵 𝘺𝘰𝘶𝘳 𝘉𝘺𝘣𝘪𝘵 𝘈𝘗𝘐 𝘬𝘦𝘺  
Bybit secret key: 𝘪𝘯𝘴𝘦𝘳𝘵 𝘺𝘰𝘶𝘳 𝘉𝘺𝘣𝘪𝘵 𝘴𝘦𝘤𝘳𝘦𝘵 𝘬𝘦𝘺  
```  
  
### Execution of the bot  
The execution of the bot runs endlessly until stopped by pressing the Esc key. When a profitable arbitrage is found, the current stage of the portfolio with the percentage change is displayed in the following format:  
  
| Asset | Binance | Bybit | Total | Percentage change |  
|-------|---------|-------|-------|-------------------|  
| BTC   |   0.023 | 0.224 | 0.247 |             0.000 |  
| ETH   |   0.543 | 0.021 | 0.564 |             0.000 |  
| USDT  |   10245 |  8723 | 18968 |             0.234 |  
  
### Machine Learning process  
The whole machine learning process can be executed by running file _machine_learning.py_. The process consists of gathering historical data for the last half year, data pre-processing including cleaning data, alignment and concatenation of the datasets, outliers detection and appending of percentage change and arbitrage probability, data description and visualization and finally building of chosen Machine Learning models including training, testing and evaluating of the models supported by hyperparameter tuning. The chosen Machine Learning models are Logistic regression, Random Forest, Support Vector Machine and Multilayer Perceptron.

Namely, the code of the Machine Learning execution has the following format:
```bash  
Data_gathering(self.Binance_client, self.Bybit_client, self.cryptocurrency_pairs)  
Data_preprocessing(self.cryptocurrency_pairs)  
Data_description(self.cryptocurrency_pairs)  
Data_visualization(self.cryptocurrency_pairs)  
Building_models(self.cryptocurrency_pairs) 
```  

The program providing an arbitrage bot with related Machine Learning processes has the following structure:
```bash
arbitrage_bot/
    .gitignore
    exchange_connection.py
    load_dataset.py
    main.py
    portfolio.json
    README.md
    requirements.txt
    tree_output.py
    best_models/
        best_models.json
        best_model_BTCUSDT.sav
        best_model_ETHUSDT.sav
    bot/
        arbitrage_bot.py
        keys.json
    dataset/
        Binance_data_BTCUSDT_15m.csv
        Binance_data_BTCUSDT_1m.csv
        Binance_data_BTCUSDT_5m.csv
        Binance_data_ETHUSDT_15m.csv
        Binance_data_ETHUSDT_1m.csv
        Binance_data_ETHUSDT_5m.csv
        Bybit_data_BTCUSDT_15m.csv
        Bybit_data_BTCUSDT_1m.csv
        Bybit_data_BTCUSDT_5m.csv
        Bybit_data_ETHUSDT_15m.csv
        Bybit_data_ETHUSDT_1m.csv
        Bybit_data_ETHUSDT_5m.csv
    dataset_preprocessed/
        BTCUSDT_15m.csv
        BTCUSDT_1m.csv
        BTCUSDT_5m.csv
        ETHUSDT_15m.csv
        ETHUSDT_1m.csv
        ETHUSDT_5m.csv
    exchanges/
        Binance_connector.py
        Binance_operations.py
        Bybit_connector.py
        Bybit_operations.py
    hypothesis_testing/
        hypothesis_data.json
        hypothesis_results.json
    images/
        change.png
        open_prices.png
        traded_volume.png
    machine_learning/
        building_models.py
        data_description.py
        data_gathering.py
        data_preprocessing.py
        data_visualization.py
        hypothesis_testing.py
        machine_learning.py

```

where the directories contain a specific part of the program as described in the following list.
1. **best_models** = saved best-trained Machine Learning models  
2. **bot** = execution of the arbitrage bot with necessary keys  
3. **dataset** = gathered datasets for the past half year from Binance and Bybit for BTCUSDT and ETHUSDT cryptocurrency pairs at 1, 5, and 15-minute intervals  
4. **dataset_preprocessed** = preprocessed datasets, including percentage change and probable occurrence of an arbitrage  
5. **exchanges** = provide a connection to an exchange, format queries for the API, and call specific endpoints  
6. **hypothesis_testing** = data for hypotheses and results of hypothesis testing  
7. **images** = visualizations of the datasets  
8. **machine_learning** = all steps of the Machine Learning process
