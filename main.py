import os 
from dotenv import load_dotenv 
import httpx 
# sound stuff 
import subprocess # for playing separate files 
# for geolocation stuff 
import math 
from geopy.geocoders import Nominatim 
# for current time 
from datetime import datetime
import time 


load_dotenv() 
key= os.environ["XC_API_KEY"]





def search(query,key): 
    # returns a list of recordings from XC

    print(f"trying {query}")
    params = {
        "query": query, 
        "key":key
    }

    response  = httpx.get(
        "https://xeno-canto.org/api/3/recordings", 
        params=params, 
        timeout=10
    )

    response.raise_for_status()
    data = response.json() 

    return data["recordings"]

def get_audio(recording): 
    # downloads the sound if we don't have it, returns the path to the file
    audio_url = recording["file"]

    os.makedirs(".cache",exist_ok=True) # make invis cache folder
    xc_name = recording["file-name"]
    file_suffix = os.path.splitext(xc_name)[1] # creates a tuple containing file name and suffix, suffix is the element of position 1 
    audio_path = os.path.join(".cache",f"XC{recording['id']}{file_suffix}")

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

    return audio_path

def play_sound(recording,seconds=20): 
    # plays a sound and WAITS for it to finish
    audio_path = get_audio(recording)
    print(f"playing {recording['en']} recording...")
    subprocess.run(["afplay","-t",str(seconds),audio_path]) # play for 20 sec at most

def play_sound_ATTHESAMETIME(recording,seconds=20,volume=1.0): 
    # plays the sounds at the same time lol
    audio_path = get_audio(recording)
    return subprocess.Popen(["afplay","-v",str(volume),"-t",str(seconds),audio_path]) # popen plays it at the same time

def get_coords(place): 
    # accepts "40.44,-79.99" OR "Pittsburgh, PA" -> returns (lat, lon)
    if "," in place: 
        parts = place.split(",") # is a list
        try: # if its coordinates, numbers 
            return (float(parts[0]), float(parts[1]))
        except ValueError: 
            pass # not numbers, treat it as a place name
    geolocator = Nominatim(user_agent="chirpy-cli")
    location = geolocator.geocode(place)
    if location is None: # if its something random
        return None 
    return (location.latitude, location.longitude)

def make_box(lat,lon,radius_km): 
    # turns a center point + radius into a box 
    dlat=radius_km/111.0 # convert km to lat
    dlon = radius_km/(111.0*math.cos(math.radians(lat))) # km to lon

    return f"{lat-dlat},{lon-dlon},{lat+dlat},{lon+dlon}" 

def top_n(counts,n): 
    # should take in a dict, return the top n as (key,count) pairs
    counts_copy=counts.copy()
    results=[]
    for i in range(n): 
        if len(counts_copy)==0: # if its empty
            break
        best_key=""
        best_count=0
        for k,count in counts_copy.items(): 
            if count>best_count: 
                best_key=k
                best_count=count
        results.append((best_key,best_count))
        del counts_copy[best_key]
    return results

def pick_best(recordings): 
    # finds the best recording
    return sorted(recordings, key=lambda rec:rec["q"])[0]

def count_places(recordings, val): 
    # counts how many recordings have a specific val
    places = {}
    for r in recordings: 
        country = r[val]
        places[country]=places.get(country,0) +1 
    return places

def filter_by(recordings, field, val): 
    new = []
    for r in recordings: 
        if r[field]==val: 
            new.append(r)
    return new 

# attempts search multiple times, from the most restrictive (highest quality) to least restrictive (lowest quality)
attempts=[
    "q:A len:5-40", # highest quality audio, short length
    "q:A", # high quality audio of any length
    "q_gt:C len:5-40", # A or B, short
    "" # anything
]

def search_by_name(key): 
    bird_name = input("Bird name: ").strip() # user input 
    recordings = []
    for request in attempts: 
        recordings = search(f'en:"{bird_name}" {request}'.strip(),key)
        if len(recordings)>0: # if recordings are found, search is done
            break

    if len(recordings)==0: # if nothing found 
        print(f"No recordings found for '{bird_name}'")
        return
    
    # print useful stuff 
    best_recording = pick_best(recordings) # placeholder, replace
    print(f"{best_recording['en']} ({best_recording['gen']} {best_recording['sp']})")
    print(f"Recorded in: {best_recording['loc']}, {best_recording['cnt']}")
    print(f"Coordinates: {best_recording['lat']}, {best_recording['lon']}")
    print(f"Recordist: {best_recording['rec']}, Quality: {best_recording['q']}, Length: {best_recording['length']}")
    print(f"xeno-canto XC{best_recording['id']}")

    # print(best_recording)
    play_sound(best_recording)

    places = count_places(recordings,"cnt")
    top_places = top_n(places,5)

    print(f"\nMost recorded in (based on {len(recordings)} samples): ")
    for i, (place,count) in enumerate(top_places,start=1): 
        print(f"{i}     {place},   {count} recordings")
    print("Note: shows where recordings were made, not where the bird lives")

    choice = (input("\n Do you want to hear it from a different country? (enter a number, or click enter to skip)")).strip()
    if choice: 
        new_place = top_places[int(choice)-1][0] # string!
        filtered_new_cnt=filter_by(recordings, "cnt", new_place)
        best_recording =pick_best(filtered_new_cnt)

        print(f"\nSwitching to a recording from {new_place}")
        print(f"Recorded in: {best_recording['loc']}, {best_recording['cnt']}")
        print(f"xeno-canto XC{best_recording['id']}")

        play_sound(best_recording)

def birds_near_me(key): 
    place=input("location (city or lat,lon): ").strip()
    coords = get_coords(place)
    if coords is None: 
        print(f"couldn't find '{place}'")
        return 
    lat,lon=coords 
    print(f"{place}->{lat},{lon}") # shows the coords 

    # start the box around it 
    box = make_box(lat,lon,25) # its 25km radius
    nearby = search(f"box:{box}",key)

    if len(nearby)==0: # if the list is empty in the box of the location
        print("No recordings are near here")
        return 
    
    species = count_places(nearby,"en")
    top_species =top_n(species,10)

    print(f"\nBirds were recorded near {place}, ({len(nearby)} recordings), {len(species)} species live here")
    for i,(name,count) in enumerate(top_species,start=1): 
        print(f"{i}     {name},   {count} recordings")
    print("Note: shows where recordings were made, not where the bird lives")

    choice =input("\ndo you want to hear one? (enter a number or enter to skip)").strip()
    if choice: 
        chosen=top_species[int(choice)-1][0]
        filtered_cnt=filter_by(nearby,"en",chosen)
        best=pick_best(filtered_cnt)
        print(f"\ntheres a {best['en']} in {best['loc']}!")
        play_sound(best)

def morning_sounds(key): 
    place = input("Where are you? Location (city or lat,lon): ").strip() 
    coords = get_coords(place)
    if coords is None: 
        print(f"couldn't find '{place}'")
        return 
    lat,lon=coords 

    box= make_box(lat,lon,50)
    month=datetime.now().month
    month_name = datetime.now().strftime("%B")

    nearby = search(f"box:{box} month:{month}",key)
    seasonal=True 

    if len(nearby)<10: # month will constrain the dataset
        print(f"(not many {month_name} recordings here, using all year)")
        nearby=search(f"box:{box}",key)
        seasonal=False
    if len(nearby)==0: # if its empty
        print("no recordings in this time")
        return 
    
    species =count_places(nearby,"en")
    cast=top_n(species,6) # the vocal cast

    if seasonal: 
        print(f"\nThere is a chorus in {place} during {month_name}")
    else: 
        print(f"\nThere is a churus near {place}, and its year-round")

    print("The birds singing are: ")
    for i,(name,count) in enumerate(cast,start=1): 
        print(f"    {i}.   {name}")
    print()
    

    # gotta download all the files first 
    print("downloading the bird noises")
    singers=[]
    for (name,count) in cast: 
        species_cnt=filter_by(nearby,"en",name)
        best=pick_best(species_cnt)
        get_audio(best) # download then cache it 
        singers.append(best)
    
    input("press enter to begin..")

    processes = []
    for i,rec in enumerate(singers,start=1): 
        print(f"\n[{i}/{len(singers)}] {rec['en']}")
        print(f"    {rec['loc']}")
        print(f"    recorded by {rec['rec']}")

        p = play_sound_ATTHESAMETIME(rec, 25, 0.7) # no wait happens
        processes.append(p)
        time.sleep(2.5) # stagger so they layer 

    try: 
        for p in processes: 
            p.wait() # wait for every bird to finish singing
    except KeyboardInterrupt: 
        for p in processes: 

            p.terminate() # ctrl+c kills the birds too
    except:
        # do smth here
    

    print("\nThis is the end of the chorus")

try: 

    print("(1) search a bird by name or,\n(2) finds birds by location, birds near me!, or\n(3) listen to a morning chorus of birds in a specific location")
    la_version=input("choose: ").strip()

    if la_version=="1": 
        search_by_name(key)
    elif la_version=="2": 
        birds_near_me(key)
    elif la_version=="3": 
        morning_sounds(key)
    else: 
        print("pick 1 or 2 or 3 bro")
    


except httpx.ReadTimeout: 
    print("it took too long to respond")

except httpx.HTTPError as e: 
    print(f"request failed bc of {e}")


