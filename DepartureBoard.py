from google.transit import gtfs_realtime_pb2
import urllib.request

API_key = ""
stop_ID = "6849"

feed = gtfs_realtime_pb2.FeedMessage()
response = urllib.request.urlopen("https://developer.trimet.org/ws/V1/arrivals?locIDs=" + stop_ID + "&appID=" + API_key)
feed.ParseFromString(response.read())
for entity in feed.entity:
  if entity.HasField('trip_update'):
    print(entity.trip_update)
