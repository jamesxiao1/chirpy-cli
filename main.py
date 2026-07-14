import os 
from dotenv import load_dotenv 
import requests 

load_dotenv() 
key= os.environ["XC_API_KEY"]

resp = requests.get(
    "https://xeno-canto.org/api/3/recordings",
    params={"query": 'en:"Common Blackbird"', "key": key},
)
data = resp.json()
print(data["numRecordings"], "recordings found")
print(data["recordings"][0]["loc"])