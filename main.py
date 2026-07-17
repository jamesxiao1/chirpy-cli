import os 
from dotenv import load_dotenv 
import httpx 
# sound stuff 
import subprocess # for playing separate files 
from pathlib import Path

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

    # print(best_recording)

    # download and play the sound 
    audio_url = best_recording["file"]

    os.makedirs("cache",exist_ok=True) # make invis cache folder
    xc_name = best_recording["file-name"]
    file_suffix = os.path.splitext(xc_name)[1] # creates a tuple containing file name and suffix, suffix is the element of position 1 
    audio_path = os.path.join("cache",f"XC{best_recording['id']}{file_suffix}")

    if not os.path.exists(audio_path): # if file alr exists 
        print("downloading..")
        audio_response=httpx.get(
            audio_url, 
            timeout=10,
            follow_redirects=True
        )
        audio_response.raise_for_status()

        f = open(audio_path, "wb") # open the file, wb = write binary
        f.write(audio_response.content) # creates WC{audio_path}.mp3 with audio_response containing mp3 files
        f.close()
        
    print(f"playing {bird_name} recording...")
    subprocess.run(["afplay","-t","20",audio_path]) # play for 20 sec at most

except httpx.ReadTimeout: 
    print("it took too long to respond")

except httpx.HTTPError as e: 
    print(f"request failed bc of {e}")


