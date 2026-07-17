import os 
from dotenv import load_dotenv 
import httpx 
# sound stuff 
import subprocess # for playing separate files 


load_dotenv() 
key= os.environ["XC_API_KEY"]



bird_name = input("Bird name: ").strip() # user input 

def search(bird_name, queries, key): 
    # searches in XC, should return a list of recordings

    print(f"trying {queries}")
    params = {
        "query":f'en:"{bird_name}" {queries}'.strip(),
        "key": key
    }

    response  = httpx.get(
        "https://xeno-canto.org/api/3/recordings", 
        params=params, 
        timeout=10
    )
    response.raise_for_status()

    data = response.json() 

    return data["recordings"]

def play_sound(recording): 
    # download and play the sound 
    audio_url = best_recording["file"]

    os.makedirs(".cache",exist_ok=True) # make invis cache folder
    xc_name = best_recording["file-name"]
    file_suffix = os.path.splitext(xc_name)[1] # creates a tuple containing file name and suffix, suffix is the element of position 1 
    audio_path = os.path.join(".cache",f"XC{best_recording['id']}{file_suffix}")

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
        
    print(f"playing {recording['en']} recording...")
    subprocess.run(["afplay","-t","20",audio_path]) # play for 20 sec at most


# attempts search multiple times, from the most restrictive (highest quality) to least restrictive (lowest quality)
attempts=[
    "q:A len:5-40", # highest quality audio, short length
    "q:A", # high quality audio of any length
    "q_gt:C len:5-40", # A or B, short
    "" # anything
]

try: 

    recordings = []
    for request in attempts: 
        recordings = search(bird_name,request,key)
        if len(recordings)>0: # if recordings are found, search is done
            break

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
    play_sound(best_recording)

    places = {}
    for r in recordings: 
        country = r["cnt"]
        places[country]=places.get(country,0) +1 
    # print (places) # it works :)

    # sort by largest to smallest and grab top 5 
    copy = places.copy()
    top_places=[]
    for i in range(5): 
        
        if len(copy)==0: # if less than 5 entries
            break

        best_place=""
        best_count=0
        for place,count in copy.items():
            if count>best_count: 
                best_place=place
                best_count=count
        top_places.append((best_place,best_count))
        del copy[best_place] 
    # print(top_places) # it works 
    print(f"\nMost recorded in (based on {len(recordings)} samples): ")
    for i, (place,count) in enumerate(top_places,start=1): 
        print(f"{i}     {place},   {count} recordings")
    
    choice = (input("\n Do you want to hear it from a different country? (enter a number, or click enter to skip)")).strip()
    if choice: 
        new_place = top_places[int(choice)-1][0] # string!
        recordings_from_new_place = []
        for r in recordings: 
            if r["cnt"]==new_place: 
                recordings_from_new_place.append(r)
        best_recording = sorted(recordings_from_new_place, key=lambda rec:rec["q"])[0]
        print(f"\nSwitching to a recording from {new_place}")
        print(f"Recorded in: {best_recording['loc']}, {best_recording['cnt']}")
        print(f"xeno-canto XC{best_recording['id']}")

        play_sound(best_recording)


except httpx.ReadTimeout: 
    print("it took too long to respond")

except httpx.HTTPError as e: 
    print(f"request failed bc of {e}")


