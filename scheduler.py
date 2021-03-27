import schedule
import requests
import time
import warnings

def report():
    url = 'https://localhost:5000/statergies/dc'
    
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        response = requests.get(url=url,verify=False)
    print(response.text)
    return response


    
schedule.every().minute.at(":02").do(report)


while True:
    schedule.run_pending()
    time.sleep(1)