import hashlib
import hmac
import time
import requests


class Bybit_connector:
    def __init__(self, API_key=None, secret_key=None, base_url=None):
        self.session = None
        self.type_of_request = dict()
        self.API_key = API_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.recv_window = "50000"

        self.initialize_session(API_key)

    def initialize_session(self, API_key):
        """
        Initialize a session that provides an HTTP connection to the Bybit API
        :param API_key: API key of the Bybit exchange
        """
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json;charset=utf-8",
                "X-MBX-APIKEY": API_key,
            }
        )

        self.type_of_request["GET"] = self.session.get
        self.type_of_request["POST"] = self.session.post
        self.type_of_request["PUT"] = self.session.put
        self.type_of_request["DELETE"] = self.session.delete

    @staticmethod
    def format_parameters(params=None):
        """
        Convert parameters in the form of a dictionary to string
        :param params: dictionary of parameters
        :return: string format of the parameters
        """
        if params is None:
            return ""
        string_parameters = ""
        for name, param in params.items():
            if len(string_parameters) == 0:
                string_parameters += name + '=' + str(param)
            else:
                string_parameters += '&' + name + '=' + str(param)
        return string_parameters

    # source https://github.com/CryptoFacilities/REST-v3-Python/blob/ee89b9b324335d5246e2f3da6b\-52485eb8391d50/cfRestApiV3.py
    # inspired by the method make_request_raw(self, requestType, endpoint, postUrl="", postBody="")
    def send_request(self, request_url=None, http_method=None, params=None, headers=None):
        """
        Format and send the query to the Binance API with processing of the response
        :param request_url: URL of the endpoint
        :param http_method: HTTP method required
        :param params: provided parameters
        :param headers: attributes of the HTTP header
        :return: json with returned data or None in case of API's error
        """
        if params is None:
            params = {}
        if headers is None:
            headers = {}

        url_path = self.base_url + request_url
        if http_method == "GET":
            url_path += '?' + self.format_parameters(params)

        parameters = {
            "url": url_path,
            "headers": headers
        }
        if http_method == "POST":
            parameters["data"] = params

        response = None
        try:
            response = self.type_of_request.get(http_method, "GET")(**parameters)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            self.send_request(request_url, params, http_method, headers)
        except (requests.exceptions.TooManyRedirects, requests.exceptions.RequestException,
                requests.exceptions.HTTPError):
            return None

        try:
            return response.json()
        except ValueError:
            return response.text

    # source https://github.com/bybit-exchange/api-usage-examples/blob/master/V3_demo/api_demo/contract/Encryption_HMAC.py
    # inspired by the method genSignature(payload)
    def sign_query(self, params, timestamp, http_method):
        """
        Append a signature based on the secret key to endpoints that require authentication
        :param params: provided parameters
        :param timestamp: current time of the exchange
        :param http_method: HTTP method required
        :return: generated signature
        """
        param_str = ""
        if http_method == "GET":
            param_str = str(timestamp) + self.API_key + self.recv_window + self.format_parameters(params)
        if http_method == "POST":
            param_str = str(timestamp) + self.API_key + self.recv_window + params
        query_hash = hmac.new(bytes(self.secret_key, "utf-8"), param_str.encode("utf-8"), hashlib.sha256)
        signature = query_hash.hexdigest()
        return signature

    # source https://github.com/bybit-exchange/api-usage-examples/blob/master/V3_demo/api_demo/contract/Encryption_HMAC.py
    # inspired by the method HTTP_Request(endPoint,method,payload,Info)
    def process_query(self, request_url=None, http_method=None, params=None):
        """
        Process the authenticated query by summarizing the required attributes of the header and signature based on the
        secret key
        :param request_url: URL of the endpoint
        :param http_method: HTTP method required
        :param params: provided parameters
        :return: response to sending the request
        """
        if params is None:
            params = {}
        timestamp = str(int(time.time() * 10 ** 3) + 500)
        signature = self.sign_query(params, timestamp, http_method)
        headers = {
            "X-BAPI-API-KEY": self.API_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": '2',
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": self.recv_window
        }

        return self.send_request(request_url, http_method, params, headers)
