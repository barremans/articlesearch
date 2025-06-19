# test.py
import requests

TOKEN = "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"
url = "https://api.github.com/repos/barremans/articlesearch/contents/releases/latest/version.txt?ref=main"

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3.raw"
}

resp = requests.get(url, headers=headers)
print(resp.status_code)
print(resp.text)
