import requests

# Define the API endpoint
url = "http://127.0.0.1:8000/getTrack"

# Define the track data
track_data = {
    # "url": "https://www.traxsource.com/track/12172154/sabali"
    "url": "https://www.beatport.com/track/blue-mile/18367412"
}


# Make the PUT request to the API
response = requests.get(url, params=track_data)

# Check the response
if response.status_code == 200:
    print("Track added successfully:", response.json())
else:
    print("Failed to add track:", response.status_code, response.text)
