import imaplib
from datetime import datetime, date,timedelta
from collections import defaultdict
import email
import time
import logging
import os
import random

from bs4 import BeautifulSoup as bs
import pandas as pd
from playsound import playsound
import regex as re

from fmp_api import *
from info_logger import Info_Logger as il
from ghost_signal_bv02 import *
import ghost_global

#Containers and Global-Variables
balance = [30000]
alarm_list = []
spread_list = []
stop_loss_list = []
close_today = []

#Funtions
def read_first_signal():
    '''This function reads first_signal.csv and loads
    the tickers into alarm_list'''

    try:
        if os.stat('first_signal.csv').st_size == 0:
            il.ghost_log("first_signal.csv did not found",20)
        else:
            df = pd.read_csv('first_signal.csv',header=None) 
            il.ghost_log("Passing first signal for evaluation...",20)
            tickers = df[df.columns[0]].values.tolist()
            sizes = df[df.columns[1]].values.tolist()
            for ticker,size in zip(tickers,sizes):
                if (ticker == None) or (ticker == 'NONE') or (ticker == 'N/A') or (type(ticker) != str):
                    pass
                else:
                    alarm_list.append(ticker)
            il.ghost_log(f'processed signal to alarm list: {alarm_list}',20)
    except FileNotFoundError:
        il.ghost_log("first_signal.csv did not found",20)

    #delete all data inside file
    #f = open("manual_include.csv", "w")
    #f.close()

def produce_signal():
    '''Produce signal from SEC using ghost_signal module.
    retrieves a tuple = (ticker, insider buying amnount), appends to alarm_list
    for evaluation.'''

    global alarm_list

    today = date.today()
    strt_date = today - timedelta(days=1)
    strt_date = strt_date.strftime("%Y-%m-%d")    
    new_signal = signal_second(strt_date)
    alarm_list = alarm_list + new_signal

    return alarm_list

def mail_alarm():
    '''Get and parse insider inforamtion providor and make the signal for the system to evaluate. retrives ticker and insider
    buying amount.'''

    imap_server = "imap.gmail.com"
    email_address = 'zerogravityalgo@gmail.com'
    password = "hrlbpbmraohyrtms"

    helper_list = []
    try:
        imap = imaplib.IMAP4_SSL(imap_server)
        imap.login(email_address,password)

        imap.select("Inbox")
        _, msgnums = imap.search(None, "UNSEEN")
        for msgnum in msgnums[0].split():
            _, data = imap.fetch(msgnum,"(RFC822)")
            try:
                message = email.message_from_bytes(data[0][1])
                il.ghost_log(f"Subject: {message.get('Subject')}",20)
                ticker_mess = message.get('Subject')
                ticker = re.findall('\((.*?)\)',ticker_mess)

                for part in message.walk():
                        if part.get_content_type() == "text/plain":
                            time.sleep(1)
                        elif part.get_content_type() == "text/html":
                            html_body = part.get_payload(decode=True)
                            soup = bs(html_body, 'html.parser')
                            all = soup.get_text()
                            first_split = all.split("$")
                            try:
                                second_split = first_split[1].split(":")
                            except IndexError:
                                total_amount = 0
                                break

                            total_amount = second_split[0]
                            total_amount = total_amount.replace(',',"")
                            total_amount = int(total_amount)

                    
                            time.sleep(1)
            
                if len(ticker[0]) <= 6:            
                    data_pack = ticker[0], total_amount
                    il.ghost_log(f"ALARM:: {ticker[0]} insider buying of {total_amount} USD",20)
                    helper_list.append(data_pack)
                else:
                    pass
            except Exception or imaplib.IMAP4.abort:
                il.ghost_log("ERROR:: Failed to retrive signal from provider",30)
                pass
    except Exception or imaplib.IMAP4.abort:
        il.ghost_log("ERROR:: Failed to retrive signal from provider",30)
        pass

    #Double-Signal value check feature
    d = defaultdict(int)
    for t in helper_list:
        d[t[0]] += t[1]

    #Create list of tuples from the defaultdict values
    wrapper_list = [(k, d[k]) for k in d]
    for i in wrapper_list:
        alarm_list.append(i)

def evaluate_balance(stock_price):
    '''Helper function to evaluate current account balance and place a trade only with sufficient funds'''

    position_value = float(stock_price)*1000
    if position_value < balance[-1]:
        new_balance = balance[-1] - position_value
        balance.append(new_balance)
    else:
        return False

def api_get(tuple_list: list):
    '''This helper function recives a list of tuples of the form [(ticker:string, trade_size:int),..]
    or a list of tickers and return a list of tuples in the form:
    (ticker, market_price, market_cap, volume, average_volume)
    Or an Empty list.
    '''
    if tuple_list == []:
        parsed_list = []
        return parsed_list
    elif isinstance(tuple_list[0], tuple):
        symbols = []
        for each_tuple in tuple_list:
            symbol, _ = each_tuple
            symbols.append(symbol)
        parsed_list = Fmp_Api.multiple_quotes(symbols)
        return parsed_list
    else:
        parsed_list = Fmp_Api.multiple_quotes(tuple_list)
        return parsed_list

def evaluation_block(phase):
    '''This function gets the data list from above and checks if any trades could be taken
    based on specified criteria. After evaluation, the function gets the most recent price for
    the chosen equities and appends (ticker,price) to the close_today list.'''

    global alarm_list,spread_list
    eval_list = list(set(alarm_list + spread_list))
    eval_list = api_get(eval_list)

    if eval_list == []:
        il.ghost_log("No new trades have been taken",20)
        pass
    else:
        for data_pack in eval_list:
            ticker, price ,market_cap, volume, average_volume = data_pack
            buy_price = None
            price = float(price)
            volume = int(volume)
            average_volume = int(average_volume)
            market_cap = int(market_cap)
            if price <= 1.99 or price >= 15:####
                il.ghost_log(ticker + " did not meet price criteria",20)
            elif volume <= 250000: ###              
                il.ghost_log(ticker + " did not meet volume criteria",20)
            elif average_volume <= 250000: ####               
                il.ghost_log(ticker + " did not meet average volume criteria",20)
            else:
                if phase == 0:
                    bid = Fmp_Api.pre_post_market(ticker,'bid')
                    ask = Fmp_Api.pre_post_market(ticker,'ask')
                    spread = round(ask - bid,2)
                    if spread > 0.1:
                        il.ghost_log(ticker + f" did not meet spread criteria ({spread})",20)
                        if ticker not in spread_list:
                            spread_list.append(ticker)
                    else:
                        il.ghost_log(ticker + " meet all criteria, proceeding order",20)
                        current_price = (bid+ask)/2
                        if ticker in spread_list:
                            spread_list.remove(ticker)
                        slipage = random.uniform(0.01,0.03)
                        buy_price = current_price + slipage
                else:
                    il.ghost_log(ticker + " meet all criteria, proceeding order",20)
                    current_price = Fmp_Api.quote(ticker,'price')
                    slipage = random.uniform(0.01,0.03)
                    buy_price = current_price + slipage
                    
                if buy_price == None:
                    pass
                elif evaluate_balance(buy_price) == False:
                    il.ghost_log(f"Not enough funds - Was not able to take a trade on {ticker}",20)
                    pass
                else:
                    buy_data = ticker, buy_price
                    close_today.append(buy_data)
                    print_price = round(buy_price,3)
                    playsound(r'C:\Users\danil\PythonFiles\Ghost\sound_folder\trade_set.mp3')
                    il.ghost_log(f"{ticker} trade has been set @ BUY price {print_price}",20)
                    il.ghost_log(f"Current Account Balance: {round(balance[-1],2)}$",20)                              

def stop_loss(stop_loss_value,phase):
    '''Stop Loss function. when current price dips below the rules of the stop, this function will write the trade
    to stop_loss_list.'''

    global close_today
    try:

        if close_today == []:
            pass
        else:
            for stock in close_today:
                stock_name, buy_price = stock
                if phase == 0:
                    bid = Fmp_Api.pre_post_market(stock_name,'bid')
                    ask = Fmp_Api.pre_post_market(stock_name,'ask')
                    current_price = (bid+ask)/2
                    spread = round(ask - bid,2)
                    il.ghost_log(f'{stock_name} pre-market spread is: {spread}',20)
                else:
                    current_price = Fmp_Api.quote(stock_name, 'price')
                index = close_today.index(stock)
                current_price = float(current_price)
                if float(buy_price)-stop_loss_value >= current_price:
                    today = date.today()
                    today = today.strftime("%d/%m/%Y")
                    slippage = random.uniform(0.01,0.03)
                    sell_price = current_price - slippage
                    change = sell_price - buy_price
                    change_precent = (sell_price - buy_price)/ buy_price
                    stop_tuple = (today, stock_name, buy_price, sell_price, change, change_precent)
                    stop_loss_list.append(stop_tuple)
                    balance.append(balance[-1] + float(buy_price)*1000 + float(change)*1000)
                    il.ghost_log(f"{stock_name} hit Stop-Loss at {round(sell_price,3)} with realized loss of: {round(change,3)}",20)
                    il.ghost_log(f"Current Account Balance: {round(balance[-1],2)}$",20)  
                    playsound(r'C:\Users\danil\PythonFiles\Ghost\sound_folder\stop_loss.mp3')
                    del close_today[index]
                else:
                    unrealized_pnl = current_price-buy_price
                    unrealized_pnl = round(unrealized_pnl,2)
                    change_in_position = ((current_price-buy_price)/buy_price)*100
                    change_in_position = round(change_in_position,2)
                    il.ghost_log(f"Possition:: {stock_name} Unrealized P&L: {unrealized_pnl} ({change_in_position}%)",20)

    except Exception: 
        il.ghost_log('ERROR:: Failed to establish a new connection when retriving stop-loss data',30)
        pass

def close_position():
    '''Writes down all the trades from close_today and stop_loss_list to Results.csv'''

    todays_date = []
    tickers = []
    buy = []
    sell = []
    revenue = []
    change_precentage = []

    for stock in close_today:

        today = date.today()
        today = today.strftime("%d/%m/%Y")        
        name, buy_price = stock
        buy_price = float(buy_price)
        current_price = Fmp_Api.quote(name, 'price')
        slippage = random.uniform(0.01,0.03)
        sell_price = current_price - slippage
        change = sell_price - buy_price
        change_precent = (sell_price - buy_price)/ buy_price
        todays_date.append(today)
        tickers.append(name)
        buy.append(buy_price)
        sell.append(sell_price)
        revenue.append(change)
        change_precentage.append(change_precent)
        il.ghost_log(f"{name} closed the position at {round(sell_price,3)} with realized p&l of: {round(change,3)}",20)

    for stop_tuple in stop_loss_list:
        
        stop_today, stop_name, stop_buy, stop_sell, stop_change, stop_change_precent = stop_tuple
        todays_date.append(stop_today)
        tickers.append(stop_name)
        buy.append(stop_buy)
        sell.append(stop_sell)
        revenue.append(stop_change)
        change_precentage.append(stop_change_precent)
    
    il.ghost_log("Succesfully wrote stop-possitions to results.csv",20)
    
    df = pd.DataFrame()
    df['date'] = todays_date
    df['tickers'] = tickers
    df['buy'] = buy
    df['sell'] = sell
    df['revenue'] = revenue
    df['change_precentage'] = change_precentage

    df.to_csv("Results.csv", header=False, index=False)

def ghost_main():

    playsound(r'C:\Users\danil\PythonFiles\Ghost\sound_folder\initializing.mp3')
    read_first_signal()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    if current_time < "15:30:00":  #15:30
        il.ghost_log('Awaiting Pre-Market Open.',20)
        while current_time < "15:30:00": #15:30
            time.sleep(50)
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
    else:
        pass
    while current_time < "16:30:00": #16:30:00
        if ghost_global.kill_mode == 0:
            phase = 0
            produce_signal()
            evaluation_block(phase)
            alarm_list.clear()
            stop_loss(0.22,phase)
            time.sleep(50)
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
        else:
            close_position()
            il.ghost_log('All positions closed, results.csv and info.log have been created.',20)
            il.ghost_log('Goodbye.',20)
            playsound(r'C:\Users\danil\PythonFiles\Ghost\sound_folder\goodbye.mp3')
            quit()
    il.ghost_log('End of phase 0. Entering phase 1.',20)
    playsound(r'C:\Users\danil\PythonFiles\Ghost\sound_folder\phase_shift.mp3')
    while current_time < "18:00:00": #18:00:00
        if ghost_global.kill_mode == 0:
            phase = 1
            global spread_list
            spread_list = []
            produce_signal() 
            evaluation_block(phase)
            alarm_list.clear()
            stop_loss(0.22,phase)
            time.sleep(50)
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
        else:
            close_position()
            il.ghost_log('All positions closed, results.csv and info.log have been created.',20)
            il.ghost_log('Goodbye.',20)
            playsound(r'C:\Users\danil\PythonFiles\Ghost\sound_folder\goodbye.mp3')
            quit()            
    il.ghost_log('End of phase 1. Entering phase 2.',20) 
    playsound(r'C:\Users\danil\PythonFiles\Ghost\sound_folder\closing_positions.mp3')
    close_position()
    il.ghost_log('All positions closed, results.csv and info.log have been created.',20)   
    il.ghost_log('End of phase 2. Goodbye.',20)
    playsound(r'C:\Users\danil\PythonFiles\Ghost\sound_folder\end_phase_2.mp3')
    quit()

if __name__ == "__main__":
    ghost_main()


