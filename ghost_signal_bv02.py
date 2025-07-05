from datetime import date,datetime,timedelta
import pandas as pd
from requests_html import HTMLSession
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup as bs
import os
import time

from info_logger import Info_Logger as il
import ghost_global

container_list = []

def get_forms(link,strt_date):
    '''This helper function gets all the SEC form 4 & 4/A's
    txt links and returns them in a list.
    input: HTML link of the SEC fillings public database.
    output: list of SEC DB directories for the txt format of the fillings'''

    my_list = []

    try:
        session = HTMLSession()
        r = session.get(link,
                        headers={'User-agent' :
                                "Daniel Liser, privet user: daniliser95@gmail.com"})
        parsed_page = bs(r.content, "html.parser")
        event_containers = parsed_page.find_all('tr', nowrap = 'nowrap')

        for container in event_containers:
            meta_data = container.text
            container_list.append(meta_data)
            form_n = container.find_all('td')[0].text
            form_datetime = container.find_all('td')[3].text
            form_time = form_datetime[-8:]
            form_date = form_datetime[:-8]
            if form_date <= strt_date and form_time < "16:00:00":
                return 0, my_list
            else:
                pass
            if form_n == '4' or form_n == '4/A':
                for l in container.find_all('a', href=True):
                    if (l['href'][-4:]) == '.txt':
                        my_list.append(l['href'])
            else:
                pass
        
    except Exception:
        il.ghost_log('An Error occured when retriving data from SEC.', 30)
        pass

    return 1, my_list

def get_forms_modified(link,strt_date):
    '''This helper function gets all the SEC form 4 & 4/A's
    txt links and returns them in a list.
    input: HTML link of the SEC fillings public database.
    output: list of SEC DB directories for the txt format of the fillings'''

    my_list = []

    try:
        session = HTMLSession()
        r = session.get(link,
                        headers={'User-agent' :
                                "Daniel Liser, privet user: daniliser95@gmail.com"})
        parsed_page = bs(r.content, "html.parser")
        event_containers = parsed_page.find_all('tr', nowrap = 'nowrap')

        for container in event_containers:
            meta_data = container.text
            if signal_checker(meta_data) == False:
                return 0, my_list
            form_n = container.find_all('td')[0].text
            form_datetime = container.find_all('td')[3].text
            form_time = form_datetime[-8:]
            form_date = form_datetime[:-8]
            if form_date <= strt_date and form_time < "16:00:00":
                return 0, my_list
            else:
                pass
            if form_n == '4' or form_n == '4/A':
                for l in container.find_all('a', href=True):
                    if (l['href'][-4:]) == '.txt':
                        my_list.append(l['href'])
            else:
                pass
        
    except Exception:
        il.ghost_log('An Error occured when retriving data from SEC.', 30)

    return 1, my_list

def clean_xml(form,forms):
    '''Get a clean xml format for every form 4,4/A of the html page,
    Save xml in directory.
    input: SEC HTML txt form 4 txt directory
    output: .xml format of the filling'''

    try:
        link = "https://www.sec.gov/" + form
        session = HTMLSession()
        r = session.get(link,
                        headers={'User-agent' :
                                "Daniel Liser, privet user: daniliser95@gmail.com"})
        parsed_page = bs(r.content, 'html.parser')
        xml_file = str(parsed_page.find_all('xml')[0])
        xml_file = xml_file[6:]
        xml_file = xml_file[:-7]
        
        index = forms.index(form) + 1
        file_location = f'C:/Users/danil/PythonFiles/Ghost/signal/GFG{index}.xml'
        with open(file_location, 'w') as f:
            f.write(xml_file)
            f.close()  

    except Exception:
        il.ghost_log(f'Failed to retrieve form {form}',30)
        pass
    except UnboundLocalError:
        il.ghost_log(f'Failed to retrieve form {form}',30)
        pass        

def parse_xml(xml_file):
    '''pasre the xml and get the required information:
    ticket, date, transaction size.
    input: .xml
    output: (ticker:srt, transaction_size:float)'''

    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        issuer = root.find('issuer')
        ticker = issuer.find('issuertradingsymbol').text
        nonDerivativeTable = root.find('nonderivativetable')
        transactions = nonDerivativeTable.findall('nonderivativetransaction')
        total_amount = []
        for transaction in transactions:
            transactioncoding = transaction.find('transactioncoding')
            transactioncode = transactioncoding.find('transactioncode')
            if transactioncode.text == 'P':
                transactionAmounts = transaction.find('transactionamounts')
                transactionShares = transactionAmounts.find('transactionshares')
                transactionValue = transactionShares.find('value')
                amount = float(transactionValue.text)
                transactionPriceperShare = transactionAmounts.find('transactionpricepershare')
                transactionPrice = transactionPriceperShare.find('value')
                price = float(transactionPrice.text)
                transaction_cost = round(amount * price)
                total_amount.append(transaction_cost)
            else:
                pass

        return_tuple = ticker, sum(total_amount)
        return return_tuple
    except AttributeError:
        return None,0
    except Exception:
        il.ghost_log(f'Exception occured when parsing {xml_file}', 30)
        return None,0

def create_signal(html_index,strt_date,function):
    '''Main logic block.
    get a list of HTML txt pages from SEC website, parse each one to get and save
    an xml version in the directory, parse the file to get the signal,
    clean and evaluate it. '''

    status, forms = function(f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&datea=&dateb=&company=&type=4&SIC=&State=&Country=&CIK=&owner=include&accno=&start={html_index}&count=100',strt_date)
    for form in forms:
        clean_xml(form,forms)
        index = forms.index(form)
        il.ghost_log(f'generating signal ({round(html_index/100) + 1}|{round(index/len(forms)*100)})',20)
        time.sleep(2)

    signal_list = []
    for filename in os.listdir(r'C:\Users\danil\PythonFiles\Ghost\signal'):
        if filename.endswith('.xml'):
            file_name = os.path.join(r'C:\Users\danil\PythonFiles\Ghost\signal', filename)
            transaction_data = parse_xml(file_name)
            signal_list.append(transaction_data)
        else:
            pass
    
    #Another small block for filterring duplicates and evaluating the signal.
    signal_list = list(set(signal_list))
    sorted_signal = []
    for signal in signal_list:
        ticker, amount = signal
        if ticker != None and amount >= 200000:
            sorted_signal.append(signal)
        else:
            pass
    
    clean_directory()
    return status,sorted_signal

def clean_directory():
    '''Helper function to clean all the .xml files in directory'''

    for path, directories, files in os.walk(r'C:\Users\danil\PythonFiles\Ghost\signal'):
      for file in files: 
           fname = os.path.join(path, file) 
           if fname.endswith('.xml'):
               os.remove(os.path.abspath(fname))

def signal_tocsv(signal):
    '''Write down the signal to csv file'''

    tickers = []
    sums = []
    for item in signal:
        ticker, amount = item
        tickers.append(ticker)
        sums.append(amount)
    
    df = pd.DataFrame()
    df['ticker'] = tickers
    df['amount'] = sums

    df.to_csv('first_signal.csv', header=False, index=False) 
    il.ghost_log('first_signal.csv file has been created', 20)  

def signal_main(strt_date):
    '''Main block for producing the first signal of the trading day.
    excepts strt_date in str(datetime) format; returns list with
    signal tuples and creates first_signal.csv file.  '''

    all_signal = []

    il.ghost_log('Run Signal',20)
    html_index_list = list(range(0,2100,100))
    for html_index in html_index_list:
        status, signal = create_signal(html_index,strt_date,get_forms)
        for item in signal:
            all_signal.append(item)
        if status == 0:
            all_signal = list(set(all_signal))
            print(all_signal)
            signal_tocsv(all_signal)
            return all_signal
        else:
            pass
        time.sleep(2)
    print(all_signal)
    all_signal = list(set(all_signal))
    signal_tocsv(all_signal)
    ghost_global.signal_mode = 1
    return all_signal

def signal_second(strt_date):
    '''Main logic block for intra-day signal retrive'''

    all_signal = []
    html_index_list = list(range(0,200,100))
    for html_index in html_index_list:
        status, signal = create_signal(html_index,strt_date, get_forms_modified)
        for ticker,amount in signal:
            all_signal.append(ticker)
        if status == 0:
            all_signal = list(set(all_signal))
            return all_signal
        else:
            pass
    all_signal = list(set(all_signal))
        
    return all_signal

def signal_checker(meta_data): 
    '''Helper function to evaluate container.text items
    and decide wheter the get_forms_modified function should
    check and parse the given SEC data container or break
    cuz of duplicate data. '''

    global container_list

    if meta_data not in container_list:
        container_list = [meta_data] + container_list
        return True
    else:
        return False
        
def estimate_runtime(strt_date):
    ''' This function estimated the time it will take 
    to produce the signal.'''

    try:
        html_index_list = list(range(0,2100,100))
        page_count = 1
        for html_index in html_index_list:
            link = f'https://www.sec.gov/cgi-bin/browse-edgar?action=getcurrent&datea=&dateb=&company=&type=4&SIC=&State=&Country=&CIK=&owner=include&accno=&start={html_index}&count=100'
            session = HTMLSession()
            r = session.get(link,
                            headers={'User-agent' :
                                    "Daniel Liser, privet user: daniliser95@gmail.com"})
            parsed_page = bs(r.content, "html.parser")
            event_containers = parsed_page.find_all('tr', nowrap = 'nowrap')
            for container in event_containers:
                form_datetime = container.find_all('td')[3].text
                form_time = form_datetime[-8:]
                form_date = form_datetime[:-8]
                if form_date <= strt_date and form_time < "16:00:00":
                    return (True, page_count/100)               
                page_count += 1
    except Exception:
        return (False, 'Failed to estimate signal run-time')

def main_logic_test():
    '''this the function you run for a script like behavior'''
    #Setting date & time params
    t_delta = input("Choose time delta (1,2,3,9=max): ")
    t_delta = int(t_delta)
    strt_date = datetime.today() - timedelta(days=t_delta)
    strt_date = strt_date.strftime("%Y-%m-%d")
    il.ghost_log('Run signal', 20)
    start = time.time()
    signal_main(strt_date)
    end = time.time()
    run_time = end-start
    il.ghost_log(f'Signal code run time: {run_time} seconds',10)

if __name__ == '__main__':
    main_logic_test()