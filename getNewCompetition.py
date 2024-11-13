import requests
import json

url = "https://raw.githubusercontent.com/ProbiusOfficial/Hello-CTFtime/main/CN.json"

def getNewCompetition():
    response = requests.get(url,proxies={'http': None, 'https': None})
    data = json.loads(response.text)
    return data
if __name__ == "__main__":
    print(getNewCompetition())