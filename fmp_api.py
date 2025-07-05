import yaml
from yaml.loader import SafeLoader
from urllib.request import urlopen
import certifi
import json
import time

from info_logger import Info_Logger as il

'''
Use this code to connect to our market data provider,
Financial Modeling Prep,
API documentation: https://site.financialmodelingprep.com/developer/docs

Modules:
api_key = Fmp_Api.key() -> start with this one to import the API Key
Fmp_Api.quote('AAPL','volume') -> get specific data on specific equity
Fmp_Api.multiple_quotes(['AAPL','META','JAJA']) -> get data on multiple equities
Fmp_Api.check_internet_connection() -> returns True if internet is connected

'''

class Fmp_Api():

    def __init__(self):
        pass

    @staticmethod
    def key():
        '''Retrive the API key from yaml file.'''
        with open('secret.yml') as f:
            data = yaml.load(f, Loader=SafeLoader)
            api_key = data.get('fmp')
            return api_key
    
    @staticmethod
    def get_jsonparsed_data(url : str):
        '''
        Receive the content of ``url``, parse it as JSON and return the object.
        Parameters
        ----------
        url : str
        Returns
        -------
        dict
        '''
        response = urlopen(url, cafile=certifi.where())
        data = response.read().decode("utf-8")
        return json.loads(data)
    
    @staticmethod
    def quote(ticker : str, parameter : str):
        '''This function is used to retrice specific data piece for
        specific equity. Recives: ticker and specified parameter,
        Returns: the specified parameter value.
        
        The params you can use, example:
        {'symbol': 'AAPL', 'name': 'Apple Inc.', 'price': 178.24, 
        'changesPercentage': -0.6798, 'change': -1.22, 'dayLow': 177.38,
        'dayHigh': 179.47, 'yearHigh': 198.23,'yearLow': 124.17,
        'marketCap': 2803483562148, 'priceAvg50': 187.43,
        'priceAvg200': 160.9734, 'exchange': 'NASDAQ', 'volume': 21109601,
        'avgVolume': 57404717, 'open': 178.88, 'previousClose': 179.46, 'eps': 5.89,
        'pe': 30.26, 'earningsAnnouncement': '2023-10-25T00:00:00.000+0000',
        'sharesOutstanding': 15728700416, 'timestamp': 1692116501}'''

        success_flag = 0
        tries_count = 0
        while success_flag !=1:
            while tries_count < 3:
                try:
                    url = (f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={api_key}")
                    respons = Fmp_Api.get_jsonparsed_data(url)
                    value = respons[0].get(parameter)
                    success_flag = 1
                    return value
                except Exception:
                    il.ghost_log(f'Failed to retrive data from provider FMP (attempt:{tries_count+1})',30)
                    tries_count +=1
                    time.sleep(5)
            tries_count = 0
            while not Fmp_Api.check_internet_connection():
                time.sleep(5)

    @staticmethod
    def pre_post_market(ticker : str,parameter : str ):
        '''This function fatched pre-post market data
        the keys you can use: {'symbol': 'META', 'ask': 280.45,
        'bid': 280.22, 'asize': 1, 'bsize': 1, 'timestamp': 1692361098978}'''
        
        success_flag = 0
        tries_count = 0
        while success_flag !=1:
            while tries_count < 3:
                try:
                    url = (f"https://financialmodelingprep.com/api/v4/pre-post-market/{ticker}?apikey={api_key}")
                    respons = Fmp_Api.get_jsonparsed_data(url)
                    value = respons.get(parameter)
                    success_flag = 1
                    return value
                except Exception:
                    il.ghost_log(f'Failed to retrive data from provider FMP (attempt:{tries_count+1})',30)
                    tries_count +=1
                    time.sleep(3)
            tries_count = 0
            while not Fmp_Api.check_internet_connection():
                time.sleep(5)


    @staticmethod
    def multiple_quotes(tickers):
        '''This function is used to get all the quote information available.
        Recives a list of tickers.
        Returns list of tubles of the form:
        (ticker, market_pice, market_cap, volume, average_volume)
        Or an Empty list [].
        '''

        if len(tickers) == 0:
            return []
        elif len(tickers) == 1:
            ticker = tickers[0]
            url = (f"https://financialmodelingprep.com/api/v3/quote/{ticker}?apikey={api_key}")
        else:
            token = tickers[0] + ','
            for ticker in tickers[1:]:
                token = token + ticker + ','
            token = token[:-1]
            url = (f"https://financialmodelingprep.com/api/v3/quote/{token}?apikey={api_key}")

        success_flag = 0
        tries_count = 0
        while success_flag !=1:
            while tries_count < 3:
                try:
                    respons = Fmp_Api.get_jsonparsed_data(url)
                    parsed_list = []
                    for quote_dict in respons:
                        ticker = quote_dict.get('symbol')
                        price = quote_dict.get('price')
                        market_cap = quote_dict.get('marketCap')
                        volume = quote_dict.get('volume')
                        average_volume = quote_dict.get('avgVolume')
                        data_pack = ticker, price, market_cap,volume,average_volume
                        parsed_list.append(data_pack)
                        success_flag = 1
                    
                    return parsed_list
                
                except Exception:
                    il.ghost_log(f'Failed to retrive data from provider FMP (attempt:{tries_count+1})',30)
                    tries_count += 1
                    time.sleep(5)
            
            tries_count = 0
            while not Fmp_Api.check_internet_connection():
                time.sleep(5)
       
    @staticmethod
    def check_internet_connection():
        '''returns True if internet is connected, False otherwise.'''
        try:
            response = urlopen('https://www.google.com/', timeout=5)
            il.ghost_log(f'Internet is connected',20)
            return True
        except:
            il.ghost_log(f'Internet is not connected',30)
            return False

api_key = Fmp_Api.key()