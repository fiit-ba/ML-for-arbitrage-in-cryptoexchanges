import hashlib
import hmac
import requests
from binance.lib.utils import cleanNoneValue, encoded_string, get_timestamp


class Binance_connector:
    def __init__(self, API_key=None, secret_key=None, base_url=None):
        self.session = None
        self.type_of_request = dict()
        self.API_key = API_key
        self.secret_key = secret_key
        self.base_url = base_url

        self.initialize_session(API_key)

    def initialize_session(self, API_key):
        """
        Initialize a session that provides an HTTP connection to the Binance API
        :param API_key: API key of Binance exchange
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

    # source https://github.com/CryptoFacilities/REST-v3-Python/blob/ee89b9b324335d5246e2f3da6b\-52485eb8391d50/cfRestApiV3.py
    # inspired by the method make_request_raw(self, requestType, endpoint, postUrl="", postBody="")
    def send_request(self, request_url=None, http_method=None, parameters=None):
        """
        Format and send the query to the Binance API with processing of the response
        :param request_url: URL of the endpoint
        :param http_method: HTTP method required
        :param parameters: provided parameters
        :return: json with returned data or None in case of API's error
        """
        if parameters is None:
            parameters = {}
        url_path = self.base_url + request_url
        params = cleanNoneValue(
            {
                "url": url_path,
                "params": encoded_string(cleanNoneValue(parameters))
            }
        )

        response = None
        try:
            response = self.type_of_request.get(http_method, "GET")(**params)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            self.send_request(request_url, params, http_method)
        except (requests.exceptions.TooManyRedirects, requests.exceptions.RequestException,
                requests.exceptions.HTTPError):
            return None

        try:
            return response.json()
        except ValueError:
            return response.text

    # source https://github.com/bybit-exchange/api-usage-examples/blob/master/V3_demo/api_demo/contract/Encryption_HMAC.py
    # inspired by the method HTTP_Request(endPoint,method,payload,Info)
    def process_query(self, request_url=None, http_method=None, parameters=None):
        """
        Process the authenticated query by appending the required attributes of the header and signature based on the
        secret key
        :param request_url: URL of the endpoint
        :param http_method: HTTP method required
        :param parameters: provided parameters
        :return: response to sending the request
        """
        if parameters is None:
            parameters = {}
        parameters["recvWindow"] = 60000
        parameters["timestamp"] = get_timestamp()
        query_data = encoded_string(cleanNoneValue(parameters))
        signature = (hmac.new(self.secret_key.encode("utf-8"), query_data.encode("utf-8"), hashlib.sha256)).hexdigest()
        parameters["signature"] = signature
        return self.send_request(request_url, http_method, parameters)
