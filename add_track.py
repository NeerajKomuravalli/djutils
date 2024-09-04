import requests

# Define the API endpoint
url = "http://127.0.0.1:8000/addTrack"

# Define the track data
track_data = {
    "title": "Example Track 2",
    "artists": [1],  # Provide at least one artist ID as required
    "label": "Example Label",
    "released": "2024-01-01",  # Provide a valid date
    "genre": "Rock",
    "key": "C",
    "bpm": 120.0,
    "comments": "Some comments",
    "tags": ["tag1", "tag2"]
}


# Make the PUT request to the API
response = requests.put(url, json=track_data)

# Check the response
if response.status_code == 200:
    print("Track added successfully:", response.json())
else:
    print("Failed to add track:", response.status_code, response.text)
