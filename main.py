import os 
from dotenv import load_dotenv 
import httpx 

load_dotenv() 
key= os.environ["XC_API_KEY"]

bird_name = input("Bird name: ") # user input 

params = {
    "query":f'en:"{bird_name}" q:A len:5-40',
    "key": key

}

try: 
    response  = httpx.get(
    "https://xeno-canto.org/api/3/recordings", 
    params=params, 
    timeout=10
    )

    response.raise_for_status()

    data = response.json() 
    recordings = data["recordings"]
    # print(data)

    if len(recordings)==0: # if nothing found 
        print(f"No recordings found for '{bird_name}'")
        exit()
    best_recording = sorted(recordings, key=lambda rec:rec["q"])[0]

    # print useful stuff 
     
    print(f"{best_recording['en']} ({best_recording['gen']} {best_recording['sp']})")
    print(f"Recorded in: {best_recording['loc']}, {best_recording['cnt']}")
    print(f"Coordinates: {best_recording['lat']}, {best_recording['lon']}")
    print(f"Recordist: {best_recording['rec']}, Quality: {best_recording['q']}, Length: {best_recording['length']}")
    print(f"xeno-canto XC{best_recording['id']}")




except httpx.ReadTimeout: 
    print("it took too long to respond")

except httpx.HTTPError as e: 
    print(f"request failed bc of {e}")


