import json
from scipy import stats
import numpy as np

SIGNIFICANCE_LEVEL = 0.05
FILE_MODE = "file"
TRAIN_MODE = "train"


class Hypothesis_testing:
    def __init__(self, mode=None):
        if mode is None or (mode != FILE_MODE and mode != TRAIN_MODE):
            raise ValueError("Correct mode for hypothesis testing has to be provided.")

        if mode == FILE_MODE:
            self.load_hypothesis_data()
        else:
            self.time_interval = {"1m": [], "5m": [], "15m": []}
            self.volatility = {"less": [], "more": []}

    def load_hypothesis_data(self):
        """
        Load hypothesis data consisting of obtained F1 scores from a JSON file
        """
        with open("../hypothesis_testing/hypothesis_data.json") as file:
            data = json.load(file)

            for key, value in data.items():
                if key == "time_interval":
                    self.time_interval = value
                if key == "volatility":
                    self.volatility = value

    def save_hypothesis_data(self):
        """
        Save the results of hypothesis testing
        """
        with open("../hypothesis_testing/hypothesis_data.json", "w") as file:
            hypothesis_data = {"time_interval": self.time_interval, "volatility": self.volatility}
            json.dump(hypothesis_data, file)

    def add_time_interval(self, f1_score=None, time=None):
        """
        Add a record of the time interval to the corresponding category
        :param f1_score: obtained F1 score
        :param time: corresponding time category
        """
        self.time_interval[time].append(f1_score)

    def add_volatility(self, f1_score=None, volatility=None):
        """
        Add a record of volatility to the corresponding category
        :param f1_score: obtained F1 score
        :param volatility: corresponding volatility category
        """
        self.volatility[volatility].append(f1_score)

    @staticmethod
    def test_independence(variable1=None, variable2=None, variable3=None):
        """
        Test the independence of the samples by a chi-squared test based on the contingency table
        :param variable1: the first sample
        :param variable2: the second sample
        :param variable3: the third sample
        :return: True if the samples are independent; False otherwise
        """
        if variable1 is None or variable2 is None:
            raise ValueError("For independence test two variables are required.")

        if len(variable1) != len(variable2):
            return True
        if variable3 is None:
            observations = np.array([variable1, variable2])
        else:
            observations = np.array([variable1, variable2, variable3])
        chi2, p, dof, expected = stats.chi2_contingency(observations)

        with open("../hypothesis_testing/hypothesis_results.json", "a") as file:
            file.write("Independence test\n")
            file.write(str(chi2) + " " + str(p) + "\n\n")

        if p < SIGNIFICANCE_LEVEL:
            return False
        else:
            return True

    @staticmethod
    def test_variance(sample1=None, sample2=None, sample3=None):
        """
        Test the similarity of variances among the samples by the Levene test
        :param sample1: the first sample
        :param sample2: the second sample
        :param sample3: the third sample
        :return: True if the variances of the samples are similar; False otherwise
        """
        if sample1 is None or sample2 is None:
            raise ValueError("For variance test two samples are required.")

        if sample3 is None:
            result = stats.levene(sample1, sample2)
        else:
            result = stats.levene(sample1, sample2, sample3)

        with open("../hypothesis_testing/hypothesis_results.json", "a") as file:
            file.write("Variance test\n")
            json.dump(result, file)
            file.write("\n\n")

        if result.pvalue < SIGNIFICANCE_LEVEL:
            return False
        else:
            return True

    @staticmethod
    def test_normality(data1=None, data2=None, data3=None):
        """
        Test the normality of the distribution of samples by the Shapiro test
        :param data1: the first sample
        :param data2: the second sample
        :param data3: the third sample
        :return: True if all samples are normally distributed; False otherwise
        """
        if data1 is None or data2 is None:
            raise ValueError("For normality test data are required.")

        result1 = stats.shapiro(data1)
        result2 = stats.shapiro(data2)
        result3 = None
        if data3 is not None:
            result3 = stats.shapiro(data3)

        with open("../hypothesis_testing/hypothesis_results.json", "a") as file:
            file.write("Normality test\n")
            json.dump(result1, file)
            file.write("\n")
            json.dump(result2, file)
            if result3 is not None:
                file.write("\n")
                json.dump(result3, file)
            file.write("\n\n")

        if result1.pvalue < SIGNIFICANCE_LEVEL or result2.pvalue < SIGNIFICANCE_LEVEL:
            return False
        elif result3 is not None and result3.pvalue < SIGNIFICANCE_LEVEL:
            return False
        else:
            return True

    def test_time_interval_3_groups(self):
        """
        Test the first hypothesis about time intervals in a one-way ANOVA test in the case of the assumptions of the
        parametric test being met, or by a Kruskal-Wallis H test otherwise
        """
        try:
            independence = self.test_independence(self.time_interval["1m"], self.time_interval["5m"], self.time_interval["15m"])
            variance = self.test_variance(self.time_interval["1m"], self.time_interval["5m"], self.time_interval["15m"])
            normality = self.test_normality(self.time_interval["1m"], self.time_interval["5m"], self.time_interval["15m"])
        except ValueError:
            return

        if independence and variance and normality:
            print("One way ANOVA test for time interval for 3 groups")
            result = stats.f_oneway(self.time_interval["1m"], self.time_interval["5m"], self.time_interval["15m"])
        else:
            print("Kruskal-Wallis H test for time interval for 3 groups")
            result = stats.kruskal(self.time_interval["1m"], self.time_interval["5m"], self.time_interval["15m"])

        with open("../hypothesis_testing/hypothesis_results.json", "a") as file:
            file.write("Time interval test for 3 groups\n")
            json.dump(result, file)
            file.write("\n\n")

    def test_volatility(self):
        """
        Test the second hypothesis about volatility by independent t-test in case the assumptions of the parametric
        test are met, or by Wilcoxon Rank-Sum test otherwise
        """
        try:
            independence = self.test_independence(self.volatility["less"], self.volatility["more"])
            variance = self.test_variance(self.volatility["less"], self.volatility["more"])
            normality = self.test_normality(self.volatility["less"], self.volatility["more"])
        except ValueError:
            return

        if independence and variance and normality:
            print("Independent t-test for volatility")
            result = stats.ttest_ind(self.volatility["less"], self.volatility["more"])
        else:
            print("Wilcoxon Rank-Sum test for volatility")
            result = stats.ranksums(self.volatility["less"], self.volatility["more"])

        with open("../hypothesis_testing/hypothesis_results.json", "a") as file:
            file.write("Volatility test\n")
            json.dump(result, file)
            file.write("\n\n")

    def perform_tests(self):
        """
        Perform hypothesis testing on both hypotheses that were set
        """
        self.save_hypothesis_data()
        self.test_time_interval_3_groups()
        self.test_volatility()
