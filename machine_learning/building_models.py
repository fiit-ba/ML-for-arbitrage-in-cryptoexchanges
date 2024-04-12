import json
import pickle
import numpy as np

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier, BaggingClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn import svm
from sklearn.neural_network import MLPClassifier
from sklearn.feature_selection import SelectKBest
from imblearn.over_sampling import SMOTE

from hypothesis_testing import Hypothesis_testing
from load_dataset import Load_dataset


class Building_models:
    def __init__(self, pairs):
        self.pairs = pairs
        self.load_dataset = Load_dataset(pairs)
        self.datasets = self.load_dataset.load_preprocessed_datasets_for_training()
        self.best_models = {}
        self.hypothesis_testing = Hypothesis_testing("train")

        self.initialize_best_models()
        self.train_datasets, self.test_datasets, self.train_arbitrages, self.test_arbitrages = self.divide_datasets()

        self.logistic_regression()
        self.random_forest()
        self.support_vector_machine()
        self.multilayer_perceptron()

        self.hypothesis_testing.perform_tests()
        self.save_best_models()

    def initialize_best_models(self):
        """
        Initialize the dictionary for the further saving of the best model
        """
        for pair in self.pairs:
            self.best_models[pair] = {"accuracy": None, "precision": None, "recall": None, "f1": None,
                                      "model": None, "interval": None}

    def divide_datasets(self):
        """
        Divide datasets into training and testing parts, considering the arbitrage column as a target variable separately,
        resampling due to the imbalance of the dataset is handled as well
        :return: lists of training and testing datasets
        """
        train_datasets, test_datasets, train_arbitrages, test_arbitrages = list(), list(), list(), list()
        for pair_key, pair in self.datasets.items():
            for interval_key, interval in pair.items():
                x = np.array((interval.drop(columns=["arbitrage"])).values)
                y = np.array(interval["arbitrage"].values)
                train_dataset, test_dataset, train_arbitrage, test_arbitrage = train_test_split(x, y, test_size=0.2,
                                                                                                random_state=2)
                sm = SMOTE(random_state=2)
                train_dataset, train_arbitrage = sm.fit_resample(train_dataset, train_arbitrage)

                train_datasets.append({"pair": pair_key, "interval": interval_key, "dataset": train_dataset})
                test_datasets.append({"pair": pair_key, "interval": interval_key, "dataset": test_dataset})
                train_arbitrages.append({"pair": pair_key, "interval": interval_key, "dataset": train_arbitrage})
                test_arbitrages.append({"pair": pair_key, "interval": interval_key, "dataset": test_arbitrage})

        return train_datasets, test_datasets, train_arbitrages, test_arbitrages

    def record_for_hypothesis(self, f1=None, interval=None, pair=None):
        """
        Saving the F1 score for further hypothesis testing
        :param f1: F1 score of the trained model
        :param interval: time interval of the dataset used for the training
        :param pair: cryptocurrency pair of the dataset used for the training
        """
        if interval == "1m":
            self.hypothesis_testing.add_time_interval(f1, "1m")
        elif interval == "5m":
            self.hvypothesis_testing.add_time_interval(f1, "5m")
        else:
            self.hypothesis_testing.add_time_interval(f1, "15m")

        if pair == "BTCUSDT":
            self.hypothesis_testing.add_volatility(f1, "more")
        elif pair == "ETHUSDT":
            self.hypothesis_testing.add_volatility(f1, "less")

    def check_best_model(self, accuracy, precision, recall, f1, model, pair, interval):
        """
        Check if the currently trained model is better than the saved best one based on accuracy and F1 score
        :param accuracy: accuracy of the model
        :param precision: precision of the model
        :param recall: recall of the model
        :param f1: F1 score of the model
        :param model: name of the trained model
        :param pair: cryptocurrency pair of the dataset used for the training
        :param interval: time interval of the dataset used for the training
        """
        self.record_for_hypothesis(f1, interval, pair)
        best_model = self.best_models[pair]
        if None in best_model.values():
            self.best_models[pair] = {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1,
                                      "model": model, "interval": interval}
            return

        if 0.99 > accuracy > best_model["accuracy"]:
            if f1 > best_model["f1"]:
                self.best_models[pair] = {"accuracy": accuracy, "precision": precision, "recall": recall, "f1": f1,
                                          "model": model, "interval": interval}

    def logistic_regression(self):
        """
        Training Logistic Regression with standard scaling, selecting the k-best features, and hyperparameters
        penalty="l2", solver="lbfgs", C=10, max_iter=500
        """
        print("\nLOGISTIC REGRESSION\n")
        pipe = Pipeline([("scaling", StandardScaler()),
                         ("features", SelectKBest()),
                         ("model", LogisticRegression(penalty="l2",
                                                      solver="lbfgs",
                                                      C=10,
                                                      max_iter=500))])

        for index in range(len(self.train_datasets)):
            pipe.fit(self.train_datasets[index]["dataset"], self.train_arbitrages[index]["dataset"])
            prediction = pipe.predict(self.test_datasets[index]["dataset"])

            accuracy = accuracy_score(self.test_arbitrages[index]["dataset"], prediction)
            precision = precision_score(self.test_arbitrages[index]["dataset"], prediction)
            recall = recall_score(self.test_arbitrages[index]["dataset"], prediction)
            f1 = f1_score(self.test_arbitrages[index]["dataset"], prediction)

            print(f"\nLogistic Regression for {self.train_datasets[index]['pair']} for "
                  f"{self.train_datasets[index]['interval']} interval")
            print(f"Accuracy: {accuracy} \nPrecision: {precision} \nRecall: {recall}\nF1 score: {f1}")

            self.check_best_model(accuracy, precision, recall, f1, pipe, self.train_datasets[index]['pair'],
                                  self.train_datasets[index]['interval'])

    def random_forest(self):
        """
        Training Random Forest with standard scaling, selecting the k-best features, and hyperparameters
        n_estimators=150, criterion="gini", min_samples_split=10, max_features="sqrt", bootstrap=True
        """
        print("\nRANDOM FOREST\n")
        pipe = Pipeline([("scaling", StandardScaler()),
                         ("features", SelectKBest()),
                         ("model", RandomForestClassifier(n_estimators=150,
                                                          criterion="gini",
                                                          min_samples_split=10,
                                                          max_features="sqrt",
                                                          bootstrap=True))])

        for index in range(len(self.train_datasets)):
            pipe.fit(self.train_datasets[index]["dataset"], self.train_arbitrages[index]["dataset"])
            prediction = pipe.predict(self.test_datasets[index]["dataset"])

            accuracy = accuracy_score(self.test_arbitrages[index]["dataset"], prediction)
            precision = precision_score(self.test_arbitrages[index]["dataset"], prediction)
            recall = recall_score(self.test_arbitrages[index]["dataset"], prediction)
            f1 = f1_score(self.test_arbitrages[index]["dataset"], prediction)

            print(f"\nRandom Forest for {self.train_datasets[index]['pair']} for "
                  f"{self.train_datasets[index]['interval']} interval")
            print(f"Accuracy: {accuracy} \nPrecision: {precision} \nRecall: {recall}\nF1: {f1}")

            self.check_best_model(accuracy, precision, recall, f1, pipe, self.train_datasets[index]['pair'],
                                  self.train_datasets[index]['interval'])

    def support_vector_machine(self):
        """
        Training Support Vector Machine with standard scaling, selecting the k-best features, and hyperparameters C=10,
        penalty="l2", max_iter=1500
        """
        print("\nSUPPORT VECTOR MACHINE\n")
        pipe = Pipeline([("scaling", StandardScaler()),
                         ("features", SelectKBest()),
                         ("model", svm.LinearSVC(C=10,
                                                 penalty="l2",
                                                 max_iter=1500))])

        for index in range(len(self.train_datasets)):
            pipe.fit(self.train_datasets[index]["dataset"], self.train_arbitrages[index]["dataset"])
            prediction = pipe.predict(self.test_datasets[index]["dataset"])

            accuracy = accuracy_score(self.test_arbitrages[index]["dataset"], prediction)
            precision = precision_score(self.test_arbitrages[index]["dataset"], prediction)
            recall = recall_score(self.test_arbitrages[index]["dataset"], prediction)
            f1 = f1_score(self.test_arbitrages[index]["dataset"], prediction)

            print(f"\nSupport vector machine for {self.train_datasets[index]['pair']} for "
                  f"{self.train_datasets[index]['interval']} interval")
            print(f"Accuracy: {accuracy} \nPrecision: {precision} \nRecall: {recall}\nF1: {f1}")

            self.check_best_model(accuracy, precision, recall, f1, pipe, self.train_datasets[index]['pair'],
                                  self.train_datasets[index]['interval'])

    def multilayer_perceptron(self):
        """
        Training Multilayer Perceptron with standard scaling, selecting the k-best features, and hyperparameters
        activation="relu", solver="sgd", learning_rate_init=0.01, max_iter=100, hidden_layer_sizes=(5, 5)
        """
        print("\nMULTILAYER PERCEPTRON\n")
        pipe = Pipeline([("scaling", StandardScaler()),
                         ("features", SelectKBest()),
                         ("model", MLPClassifier(activation="relu",
                                                 solver="sgd",
                                                 learning_rate_init=0.01,
                                                 max_iter=100,
                                                 hidden_layer_sizes=(5, 5)))])

        for index in range(len(self.train_datasets)):
            pipe.fit(self.train_datasets[index]["dataset"], self.train_arbitrages[index]["dataset"])
            prediction = pipe.predict(self.test_datasets[index]["dataset"])

            accuracy = accuracy_score(self.test_arbitrages[index]["dataset"], prediction)
            precision = precision_score(self.test_arbitrages[index]["dataset"], prediction)
            recall = recall_score(self.test_arbitrages[index]["dataset"], prediction)
            f1 = f1_score(self.test_arbitrages[index]["dataset"], prediction)

            print(f"\nMultilayer perceptron for {self.train_datasets[index]['pair']} for "
                  f"{self.train_datasets[index]['interval']} interval")
            print(f"Accuracy: {accuracy} \nPrecision: {precision} \nRecall: {recall}\nF1: {f1}")

            self.check_best_model(accuracy, precision, recall, f1, pipe, self.train_datasets[index]['pair'],
                                  self.train_datasets[index]['interval'])

    def save_best_models(self):
        """
        Saving the best-trained models into .sav files and their parameters and metrics into .json file
        """
        json_models = {}
        exclude_keys = {"model"}
        for key, pair in self.best_models.items():
            json_models[key] = {key: pair[key] for key in set(list(pair.keys())) - exclude_keys}
        with open("../best_models/best_models.json", "w") as file:
            json.dump(json_models, file)

        with open("../best_models/best_model_BTCUSDT.sav", "wb") as file:
            pickle.dump(self.best_models["BTCUSDT"]["model"], file)

        with open("../best_models/best_model_ETHUSDT.sav", "wb") as file:
            pickle.dump(self.best_models["ETHUSDT"]["model"], file)
