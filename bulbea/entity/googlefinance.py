import urllib.request as request
from urllib.error import HTTPError
import json
from bs4 import BeautifulSoup
import csv
import datetime
import re

import pandas as pd
import requests
import codecs


DESCRIPTIVE_KEYS = {
    'id': 'ID',
    't': 'TickerSymbol',
    'e': 'Exchange',
    'l': 'LastTradePrice',
    'lt_dts': 'LastTradeDateTime',
    'c': 'Change',
    'cp': 'ChangePercent',
    'pcls_fix': 'PreviousCloseFix',
    'div': 'Dividend',
    'yld': 'Dividend Yield'
}

class Share2:

    """Class contains functions to pull current and historical pricing data from
        Google Finance

    Functions
    ---------
        get_quote: returns the most recent market quote of the stock
        get_historical_prices: retrieves historical close prices
        get_stock_news: returns recent relevant company news

    Parameters
    ----------
    ticker : str
        exchange ticker of public traded company

    Attributes
    ----------
        ticker : str
            market ticker

        valid : bool
            ticker is a valid ticker

        name : str
            long company name

        description : str
            Brief description of company

    """

    def __init__(self, ticker=None):

        self.ticker = ticker
        self.valid = self._validate_ticker()
        self.name, self.description = self._get_desc_details()
        self.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        
        now = datetime.datetime.now()
        today = "{}/{}/{}".format(now.month,now.day,now.year)
        self.datahs = self.get_historical_prices('1/1/2004', today)
        self.datart = self.get_google_finance_intraday(days=60)

    def get_quote(self):

        """Retrieves most recent stock price"""

        quote_url = ("http://finance.google.com/finance/info?client=ig"
                     + "&q={}"
                    ).format(self.ticker)

        if self.valid:
            with request.urlopen(quote_url) as quote_response:
                resp = quote_response.read()
                quotes = resp.decode('ascii', 'ignore').replace('\n', '')[3:]
                return self._replace_keys(json.loads(quotes))


    def get_google_finance_intraday(self, period=60, days=1):
        """
        Retrieve intraday stock data from Google Finance.

        Parameters
        ----------
        ticker : str
            Company ticker symbol.
        period : int
            Interval between stock values in seconds.
        days : int
            Number of days of data to retrieve.

        Returns
        -------
        df : pandas.DataFrame
            DataFrame containing the opening price, high price, low price,
            closing price, and volume. The index contains the times associated with
            the retrieved price values.
        """

        uri = 'https://finance.google.com/finance/getprices?'\
              'i={period}&p={days}d&f=d,o,h,l,c,v&df=cpct&q={ticker}'.format(ticker=self.ticker,
                                                                      period=period,
                                                                      days=days)

        page = requests.get(uri)
        reader = csv.reader(codecs.iterdecode(page.content.splitlines(), "utf-8"))
        

        rows = []
        times = []
        for row in reader:
            if re.match('^[a\d]', row[0]):
                if row[0].startswith('a'):
                    start = datetime.datetime.fromtimestamp(int(row[0][1:]))
                    times.append(start)
                else:
                    times.append(start+datetime.timedelta(seconds=period*int(row[0])))
                rows.append(map(float, row[1:]))
        if len(rows):
            return pd.DataFrame(rows, index=pd.DatetimeIndex(times, name='Date'),
                                columns=self.columns)
        else:
            return pd.DataFrame(rows, index=pd.DatetimeIndex(times, name='Date'))

    def get_historical_prices(self, start_date, end_date):

        """Class retrives historical stock prices between the two dates provided

        Parameters
        ------------
        start_date : str
            Older historical date to retrieve prices, '06/30/2017'

        end_date : str
            More recent historical date to retrive prices, '07/31/2017'

        """

        if self.valid is True:
            historic_url = ("https://finance.google.com/finance/historical?"
                            + "&q={0}"
                            + "&startdate={1}"
                            + "&enddate={2}"
                            + "&output=csv"
                           ).format(self.ticker, start_date, end_date)
            response_data = []
            try:
                with request.urlopen(historic_url) as response:
                    page = response.read().decode('utf-8-sig').splitlines()

                headers = page[0].split(',')
                response_data = self._parse_hist_data(page[1:], headers, ',')

            except HTTPError:

                more_data = True
                start = 0
                while more_data:
                    historic_url = ("https://finance.google.com/finance/historical?"
                                    + "&q={0}"
                                    + "&startdate={1}"
                                    + "&enddate={2}"
                                    + "&num=200"
                                    + "&start={3}"
                                   ).format(self.ticker, start_date, end_date, start)
                    with request.urlopen(historic_url) as response:
                        page = response.read()

                    soup = BeautifulSoup(page, 'html.parser')
                    table = soup.find("table", class_='gf-table historical_price')
                    text = table.text.split('\n\n')
                    headers = text[1].split('\n')

                    response_data = (response_data
                                     + self._parse_hist_data(
                                         text[2:],
                                         headers,
                                         '\n',
                                         date_format='%b %d, %Y',
                                         ))

                    if len(response_data) < 200:
                        more_data = False
                    elif len(response_data) % 200 != 0:
                        more_data = False
                    else:
                        start = start + 200

            #print(type(response_data))
            #return response_data

            #Convert Json to pd
            rows = []
            times = []
            for res in response_data:
                add = True
                
                row = []
                for attr in self.columns:
                    if res[attr].lstrip('-').replace('.','',1).isdigit():
                        row.append(float(res[attr]))
                    else:                        
                        add = False
                        break
                
                if add:
                    rows.insert(0, row)
                    times.insert(0, res['Date'])
                
            return pd.DataFrame(rows, index=pd.DatetimeIndex(times, name='Date'),
                                columns=self.columns)
            

    def get_stock_news(self):

        """function will scrape google news to pull relelvant news stories"""

        if self.valid is False:
            return "Invalid Stock"

        url = ("https://finance.google.com/finance/company_news?"
               + "q={0}"
               + "&start=0"
               + "&num=20"
              ).format(self.ticker)
        with request.urlopen(url) as response:
            res = response.read()

        soup = BeautifulSoup(res, 'html.parser')
        scraped_articles = []
        articles = soup.find(id='news-main')

        for article in articles.find_all(class_='g-section news sfe-break-bottom-16'):
            header = article.find(class_='name')
            details = header.select('a')
            headline = details[0].getText()
            url = details[0]['href']

            byline = article.find(class_='byline')
            src = byline.find(class_='src').getText()
            article_date = byline.find(class_='date').getText()

            scraped_articles.append(
                {
                    'headline': headline,
                    'url': url,
                    'src': src,
                    'date': article_date
                }
            )
        return scraped_articles

    def _get_desc_details(self):
        desc_url = 'https://finance.google.com/finance?q='
        try:
            with request.urlopen(desc_url + self.ticker) as response:
                soup = BeautifulSoup(response.read(), 'html.parser')

            try:
                title = soup.title.text
                company_name = title[:title.find(':')]
            except AttributeError:
                company_name = 'Company Name Unavailable'

            try:
                description = soup.find('div', class_='companySummary').text
            except AttributeError:
                description = 'Description Unavailable'
        except HTTPError as error:
            self.valid = False
            print(error.reason)
            return ('Unavailable', 'Unavailable')

        return (company_name, description)

    def _validate_ticker(self):
        url = 'https://finance.google.com/finance?'

        try:
            with request.urlopen(url + '&q=' + self.ticker) as _:
                return True
        except HTTPError as _:
            return False

    @staticmethod
    def _parse_hist_data(data, headers, delimiter, date_format='%d-%b-%y'):

        parsed_data = []
        for row in data:
            cell = row.split(delimiter)
            row_contents = {}
            row_contents[headers[0]] = datetime.datetime.strptime(cell[0], date_format)
            row_contents[headers[1]] = cell[1].replace(',', '')
            row_contents[headers[2]] = cell[2].replace(',', '')
            row_contents[headers[3]] = cell[3].replace(',', '')
            row_contents[headers[4]] = cell[4].replace(',', '')
            row_contents[headers[5]] = cell[5].replace(',', '')
            parsed_data.append(row_contents)

        return parsed_data

    @staticmethod
    def _replace_keys(quote):
        updated_quote = {}
        for key in quote[0]:
            if key in DESCRIPTIVE_KEYS:
                updated_quote[DESCRIPTIVE_KEYS[key]] = quote[0][key]
        return updated_quote
