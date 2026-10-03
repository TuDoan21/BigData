import urllib.request
import re

req = urllib.request.Request("http://127.0.0.1:8501", headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8")
        print("Length:", len(html))
        print("Title in HTML:", re.findall(r"<title>.*?</title>", html))
except Exception as e:
    print("Error:", e)
