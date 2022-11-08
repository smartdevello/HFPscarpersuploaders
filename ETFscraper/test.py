import requests

url = "https://newscatcher.p.rapidapi.com/v1/aggregation"

querystring = {"q":"Apple","agg_by":"day","media":"True"}

headers = {
    'x-rapidapi-key': "1e94609cbamsh1bbf8beef0a4826p107bcejsnb6a2a1bbb6ce",
    'x-rapidapi-host': "newscatcher.p.rapidapi.com"
    }

response = requests.request("GET", url, headers=headers, params=querystring)

print(response.text)