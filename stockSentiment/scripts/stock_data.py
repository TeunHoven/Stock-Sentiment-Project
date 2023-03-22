from yahoofinancials import YahooFinancials as yf       # The yahoo finance library
import pandas                                           # Easier calculation with many data points
import datetime as dt                                   # Calculate dates easier 
import numpy as np                                      # Make more difficult calculations like 

# Get the shortname of the company
def get_name(data_all, ticker):
    stock_general_data = data_all.get_stock_quote_type_data()
    return stock_general_data[ticker]['shortName']

# Get all data of the company by ticker
def get_all_data(ticker):
    return yf(ticker)

# Get the total debt of the company
def get_debt(data_financial_stmts_quarterly, ticker):
    data = data_financial_stmts_quarterly['balanceSheetHistoryQuarterly'][ticker][0]

    # Get the last date that is available through YahooFinance library
    data_last_date = list(data.keys())[-1]
    data = data[data_last_date]

    # If no shortLongTermDebt than 0 (because there is none)
    if 'shortLongTermDebt' in data:
        shortTermDebt = data['shortLongTermDebt']
    else:
        shortTermDebt = 0

    # If no longTermDebt than 0 (because there is none)
    if 'longTermDebt' in data:
        longTermDebt = data['longTermDebt']
    else:
        longTermDebt = 0

    # Calculate the total debt
    totDebt = shortTermDebt + longTermDebt
    
    return totDebt

# Get the beta of the company
def get_beta(ticker):
    today = dt.datetime.now().strftime('%Y-%m-%d')
    data_stock = yf(ticker).get_historical_price_data('2000-01-01', today, 'daily')[ticker] # We will begin from 2000 because that means we can check when the first price of the stock was and with that compare it with the market
    start_date = data_stock['firstTradeDate']['formatted_date']
    
    data_market = yf('^GSPC').get_historical_price_data(start_date, today, 'daily')['^GSPC']

    # Get the prices of the stock and the market
    data_prices_stock = data_stock['prices']
    data_prices_market = data_market['prices']

    prices_stock = []
    prices_market = []

    # Get close prices of the stock
    for data in data_prices_stock:
        prices_stock.append(data['close'])

    # Get close prices of the market
    for data in data_prices_market:
        prices_market.append(data['close'])

    # configures the all_data variable for two rows
    all_data = {'stock': [], 'market': []}
    all_data['stock'] = prices_stock
    all_data['market'] = prices_market

    # Turn the above data in a dataframe
    data = pandas.DataFrame(data=all_data)

    # Calculate the change of each data point with the previous
    returns = data.pct_change()
    market_return = returns.get('market')

    # Calculate the variance
    variance_market = market_return.var()

    # Calculate the covariance
    cov = returns.cov()

    # Calculate the beta
    beta = cov.loc['stock', 'market']/variance_market

    return beta

# Get the total equity of the company
def get_equity(data_all):
    print(data_all)
    equity = data_all.get_book_value()
    return equity

# Get the Return On Equity (ROE)
def get_ROE(data_all, ticker):
    balance_sheet = data_all.get_financial_stmts('annual', 'balance')['balanceSheetHistory'][ticker][0]
    cash_sheet = data_all.get_financial_stmts('annual', 'cash')['cashflowStatementHistory'][ticker][0]
    last_balance_sheet_date = list(balance_sheet.keys())[-1]
    last_cash_sheet_date = list(cash_sheet.keys())[-1]

    stockholder_equity = balance_sheet[last_balance_sheet_date]['stockholdersEquity']
    net_income = cash_sheet[last_cash_sheet_date]['netIncome']

    roe = net_income/stockholder_equity

    return roe

# Get the total value of the company without knowing debt and equity
def get_total_value(data_financial_stmts_quarterly, data_all, ticker):
    equity = get_equity(data_all)
    debt = get_debt(data_financial_stmts_quarterly, ticker)

    print()
    print(f'Debt is {debt} and of the total is {debt/(debt+equity)}')
    print(f'Equity is {equity} and of the total is {equity/(debt+equity)}')
    print()

    value = equity + debt
    return value

# Get the total value of the company with knowing debt and equity
def get_total_value(debt, equity):
    value = equity + debt

    print('Debt is {:d} euros and of the total is {:.2%}'.format(debt, (debt/value)))
    print('Equity is {:d} euros and of the total is {:.2%}'.format(equity, (equity/value)))

    return value

###################################################################################################################################################
############# TODO Calculate Cost of Equity by automatically get return of market and the risk free rate ##########################################
###################################################################################################################################################
# Calculate the Cost of Equity (COE)
# def calc_COE(data_all, ticker):
#     if(data_all.get_beta() != None):
#         re = risk_free_rate + (data_all.get_beta()*(return_of_market-risk_free_rate))
#     else:
#         beta = get_beta(ticker)
#         re = risk_free_rate + (beta*(return_of_market-risk_free_rate))

#     print('The Cost of Equity is {:.2%}'.format(re))
#     return re


###################################################################################################################################################
############# TODO Calculate Cost of Debt by automatically get the tax-rate of the companies' country #############################################
###################################################################################################################################################
# Calculate the Cost of Debt (COD)
# def calc_COD(data_all, debt):
#     interest_expense = data_all.get_interest_expense()*-1   # The data you get is below zero because it is an expense thus we multiply it by -1 to get the positive value
#     if(debt != 0):
#         cod = (interest_expense/debt)*(1-tax_rate)
#         print('The interest rate is {:.2%}'.format(interest_expense/debt))
#     else:
#         cod = 0
#         print('The interest rate is 0.0%')

    
#     print('The Cost of Debt is {:.2%}'.format(cod))
#     return cod

# Get the last Dividend per Share (DPS)
def get_last_DPS(data_previous_years):                                    
    data = data_previous_years['eventsData']['dividends']    
    last_dividend_date = list(data.keys())[-1]

    return data[last_dividend_date]['amount']

# Get the Current Market Value (CMV)
def get_CMV(data_all, ticker):                  
    data = data_all.get_stock_price_data(reformat=True)[ticker]
    return data['regularMarketPrice']

# Get data of a company of multiple years
def get_historical_data(data_all, year_ago, ticker):
    now = dt.datetime.now()
    begin = now.year - year_ago
    historical_data = data_all.get_historical_price_data(f'{begin}-01-01', now.strftime('%Y-%m-%d'), 'monthly') 
    return historical_data[ticker]

def get_data(ticker):
    data_all = get_all_data(ticker)
    return data_all

def run(ticker):
    data_all = get_data(ticker)
    print(data_all)
    data_financial_stmts_quarterly = data_all.get_financial_stmts('quarterly', 'balance')
    data = {ticker: {'name': get_name(data_all, ticker)}}
    data[ticker]['equity'] = get_equity(data_all)
    data[ticker]['debt'] = get_debt(data_financial_stmts_quarterly, ticker)
    data[ticker]['return_on_equity'] = get_ROE(data_all, ticker)
    data[ticker]['beta'] = get_beta(ticker)
    data[ticker]['value'] = get_total_value(data[ticker]['debt'], data[ticker]['equity'])
    data[ticker]['div_per_share'] = get_last_DPS(get_historical_data(data_all, 1, ticker))
    data[ticker]['market_value'] = get_CMV(data_all, ticker)

    return data
