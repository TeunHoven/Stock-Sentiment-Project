from decouple import config
import requests
import time
from django.utils import timezone, dateformat, dateparse
from ..models import Company, CompanyStockData

API_KEY = config('API_KEY_ALPHAV')

# TODO
def get_equity():
    equity = 0
    return equity

# TODO
def get_debt():
    debt = 0
    return debt

# TODO
def get_ROE():
    ROE = 0
    return ROE

# TODO
def get_beta():
    beta = 0
    return beta

# TODO
def get_total_value():
    tot_val = 0
    return tot_val

# TODO
def get_last_DPS():
    DPS = 0
    return DPS

# TODO
def get_CMV():
    CMV = 0
    return CMV

def get_company_overview(ticker):
    overview_url = f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker}&apikey={API_KEY}' 
    overview_request = requests.get(overview_url)
    overview_data = overview_request.json()
    return overview_data

def get_stock_data(ticker, interval):
    stock_url = ''
    match interval:
        case 'daily':
            stock_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey={API_KEY}'
        case 'hourly':
            stock_url = f''
        case 'ftmin':
            stock_url = f''
        case 'fmin':
            stock_url = f''
        case 'omin':
            stock_url = f''
        case _:
            stock_url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={ticker}&outputsize=full&apikey={API_KEY}'
    stock_request = requests.get(stock_url)
    stock_data = stock_request.json()
    return stock_data

def get_balance_sheet_data(ticker):
    balance_sheet_url = f'https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={ticker}&apikey={API_KEY}'
    balance_sheet_request = requests.get(balance_sheet_url)
    balance_sheet_data = balance_sheet_request.json()
    return balance_sheet_data

def get_sma_data(ticker):
    sma_url = f'https://www.alphavantage.co/query?function=SMA&symbol={ticker}&interval=daily&time_period=10&series_type=close&apikey={API_KEY}'
    sma_request = requests.get(sma_url)
    sma_data = sma_request.json()
    return sma_data

def save_company_data(data):
    ticker = data['overview']['ticker']
    try:  
        company = Company.objects.get(ticker=ticker)
        print('Company already exists!')
    except Company.DoesNotExist:
        print('Saving Company!')
        company_name = data['overview']['name']
        company = Company(
            name=company_name, 
            ticker=ticker,
            description = data['overview']['description'],
            sector = data['overview']['sector'],
            industry = data['overview']['industry'],
            equity = data['overview']['equity'],
            debt = data['overview']['debt'],
            returnOnEquity = data['overview']['return_on_equity'],
            beta = data['overview']['beta'],
            value = data['overview']['value'],
            dividendPerShare = data['overview']['div_per_share'],
            lastModified = dateformat.format(timezone.now(), 'Y-m-d H:i:s')
            )
        company.save()
        print('Company Saved! \n')

def save_company_stock_data(stock_data, sma_data, overview_data):
    print('Saving company stock data!')
    company = Company.objects.get(ticker=overview_data['ticker'])
    for key, value in stock_data.items():
        if("Time Series" in key):
            for date, data in value.items():
                try:
                    sma = sma_data['Technical Analysis: SMA'][date]['SMA']
                except KeyError:
                    break
                stock_data = CompanyStockData(
                    company = company,
                    date = date,
                    open = data['1. open'],
                    high = data['2. high'],
                    low = data['3. low'],
                    close = data['4. close'],
                    adjustedClose = data['5. adjusted close'],
                    sma = sma,
                    interval = CompanyStockData.DAY,
                )
                stock_data.save()
    print('Company stock data saved! \n')

def get_company_data(ticker):
    api_calls = 0

    time.sleep(15)  # Makes sure that the API calls can be called
    api_calls = api_calls + 1
    overview_data = get_company_overview(ticker)

    time.sleep(15)  # Makes sure that the API calls can be called
    api_calls = api_calls + 1
    stock_data = get_stock_data(ticker, 'daily')

    time.sleep(15)  # Makes sure that the API calls can be called  
    api_calls = api_calls + 1
    balance_sheet_data = get_balance_sheet_data(ticker)
    try:    
        balance_sheet_data = balance_sheet_data['quarterlyReports'][0]
    except KeyError:
        balance_sheet_data = None

    time.sleep(15)
    api_calls = api_calls + 1
    sma_data = get_sma_data(ticker)

    if(len(overview_data) == 0):
        print(f'Company {ticker} has no Overview Data')
        return False
    if(stock_data == None):
        print(f'Company {ticker} has no Stock Data')
        return False
    if(balance_sheet_data == None):
        print(f'Company {ticker} has no Balance Sheet Data')
        return False

    data = {'overview': {}, 'stock_data': {}}

    shortTermDebt = balance_sheet_data['shortTermDebt']
    print(f'STD (before): {shortTermDebt}')
    if(shortTermDebt == 'None'):
        shortTermDebt = 0
    print(f'STD (before): {shortTermDebt} \n')

    currentLongTermDebt = balance_sheet_data['currentLongTermDebt']
    print(f'CLTD (before): {currentLongTermDebt}')
    if(currentLongTermDebt == 'None'):
        currentLongTermDebt = 0
    print(f'CLTD (before): {currentLongTermDebt} \n')

    data['overview']['name'] = overview_data['Name']
    data['overview']['ticker'] = overview_data['Symbol']
    data['overview']['description'] = overview_data['Description']
    data['overview']['sector'] = overview_data['Sector']
    data['overview']['industry'] = overview_data['Industry']
    data['overview']['equity'] = balance_sheet_data['totalShareholderEquity']
    data['overview']['debt'] = int(shortTermDebt) + int(currentLongTermDebt)
    data['overview']['return_on_equity'] = overview_data['ReturnOnEquityTTM']
    data['overview']['beta'] = overview_data['Beta']
    data['overview']['value'] = int(data['overview']['debt']) + int(data['overview']['equity'])
    data['overview']['div_per_share'] = overview_data['DividendPerShare']

    for key, value in data['overview'].items():
        if(key != 'name' or key != 'ticker' or key != 'description' or key != 'sector' or key != 'industry'):
            if(value == None or value == 'None'):
                print(f'Change {key} to 0!')
                data['overview'][key] = 0

    save_company_data(data)
    save_company_stock_data(stock_data, sma_data, data['overview'])

    return api_calls