import time

sTime = time.time()

import urllib.request
#import requests
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import math
import sys

from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont

# Config variables
keys_txt = open("keys.txt","r") #Authentication and TODO {stop ids definitions} file location
API_key = keys_txt.readline()
keys_txt.close()

stop_IDs = {"417", "418", "2615", "2616"} #417:15WB, 418:15EB, 2616:14WB, 2615:14EB

relative_time_horizon = 30 * 1000 * 60 #determines how far out relative timings will be used

#image matrix config stuff
options = RGBMatrixOptions()
options.rows = 32
options.chain_length = 4
options.parallel = 1
options.hardware_mapping = 'adafruit-hat'  # If you have an Adafruit HAT: 'adafruit-hat'


# All the functions
def fetch_GTFS(): #submits the request to Trimet, returning an XML string
    stop_string = ","
    stop_string = stop_string.join(stop_IDs)

    url = "https://developer.trimet.org/ws/V1/arrivals?locIDs=" + stop_string + "&appID=" + API_key
    response = urllib.request.urlopen(url)
    return response.read()

def parse_GTFS(xmlbody, table): #parses through the XML, populating a table that is passed in
    root = ET.fromstring(xmlbody)
    for child in root:
        if child.tag.split("}")[1] == "arrival":
            table = append_to_dataframe(child.attrib,table)
    return table

def append_to_dataframe(arrival, table): #adds individual rows to the DF
    row_dict = {}
    for value in table.columns:
        if value in arrival:
            row_dict[value] = arrival[value]
    table = table.append(row_dict, ignore_index=True)
    return table

def shortSignAliases(rawShortSign): #to be used for consolidating known aliases
    #could also have a different (or the same) function build up a dict or smth, and instead have this function just be passed the line and dir, and get back the relevant ShortSign
    #Want to block the 15 directions for my purposes
    #TODO Create a dictionary of domain and ranges for appropiate aliases
    associations = {
        "15 Gateway TC": "15 Eastbound",
        "15 To 60th Ave": "15 Eastbound",
        "15 To 92nd Ave": "15 Eastbound",
        "15 Montgomery Pk": "15 Portland",
        "15 To Thurman":"15 Portland",
        "15 To NW Yeon": "15 Portland",
        "15 To  SW 5th & Washington": "15 Portland",
        "14 To 94-Foster": "14 94-Foster",
        "14 To Portland": "14 City Center"
    }
    return associations[rawShortSign]

def relativeTimingInfo(eventTime):
    currentTime = time.time()*1000
    eventTime = int(eventTime)
    if (eventTime-currentTime < relative_time_horizon): #For minutes till style
        return str(math.floor(((eventTime-currentTime)/1000)/60))
    else:
        if time.strftime("%I", time.localtime(eventTime/1000))[0] == "0": #For single digit hours
            return time.strftime("%I:%M", time.localtime(eventTime/1000))[1:]
        else:
            return time.strftime("%I:%M", time.localtime(eventTime/1000)) #For two digit hours

def humanReadable(table): #pass the entire table, converts into something more human readable ready for display formatting
    output = pd.DataFrame(columns=["line","dir","bound_to", "departures"])
    routes = table["route"].unique()

    for i in routes:
        dirs = table.loc[table["route"] == i]["dir"].unique()
        for j in dirs:
            relevantLines = (table.loc[(table["route"] == i) & (table["dir"] == j)]) #selects the rows that have the exact right line and direction

            # Generating the appropiate time info and creates a string, 'departureTimes'
            departureTimes = ""
            for index, row in relevantLines.iterrows(): # TODO: add more spacing between times, or commas?
                if isinstance(row["estimated"], str): # This works for now, but I don't know if I like how it works
                    departureTimes += " " + relativeTimingInfo(row["estimated"])
                else:
                    departureTimes += " " + relativeTimingInfo(row["scheduled"])

            #temp code to figure out how to best write shortsigns to the dataframe
            relevantLines["shortSign"].iloc[0]
            shortSign = shortSignAliases(relevantLines["shortSign"].iloc[0])

            output = output.append({"line":i,"dir":j,"bound_to":shortSign,"departures":departureTimes},ignore_index=True)
    return output #returns a single line with all selected buses

def format(table): #not sure where and how I want to handle formatting
    output = ""


# And, here's where "Main" starts
# selecting from these which columns to use: 'block': '1521', 'departed': 'false', 'dir': '0', 'status': 'scheduled', 'fullSign': '15  Belmont/NW 23rd to NW Thurman St', 'piece': '1', 'route': '15', 'scheduled': '1568867948000','estimated': '1568866545000', 'shortSign': '15 To Thurman', 'locid': '417', 'detour': 'true'
print("initialization completed in " + str(sTime-time.time()) + " seconds")

fnt = ImageFont.truetype(font="pixelmix/pixelmix.ttf",size=8, layout_engine=ImageFont.LAYOUT_BASIC)

while True:
    sTime = time.time()
    by_block = pd.DataFrame(columns=["route","dir","fullSign", "shortSign", "scheduled","estimated", "reason"])
    by_block = parse_GTFS(fetch_GTFS(),by_block)

    for i in range(3):
        humanReady = humanReadable(by_block).set_index(["line","dir"])

        frame = Image.new("RGB",(128,32))
        d = ImageDraw.Draw(frame)
        d.fontmode = "1"

        d.text((0,-1), humanReady.xs(["14","1"]).loc["bound_to"], font=fnt, fill=(255,187,45))
        departures_r1 = humanReady.xs(["14","1"]).loc["departures"]
        coords_r1 = 128-d.textsize(departures_r1,font=fnt)[0]
        d.text((coords_r1,-1),departures_r1,font=fnt, fill=(255,187,45))

        d.text((0,7), humanReady.xs(["15","0"]).loc["bound_to"],font=fnt, fill=(255,187,45))
        departures_r2 = humanReady.xs(["15","0"]).loc["departures"]
        coords_r2 = 128-d.textsize(departures_r2,font=fnt)[0]
        d.text((coords_r2,7),departures_r2,font=fnt, fill=(255,187,45))

        d.text((0,15), humanReady.xs(["14","0"]).loc["bound_to"],font=fnt, fill=(255,187,45))
        departures_r3 = humanReady.xs(["14","0"]).loc["departures"]
        coords_r3 = 128-d.textsize(departures_r3,font=fnt)[0]
        d.text((coords_r3,15),departures_r3,font=fnt, fill=(255,187,45))

        d.text((0,23), humanReady.xs(["15","1"]).loc["bound_to"],font=fnt, fill=(255,187,45))
        departures_r4 = humanReady.xs(["15","1"]).loc["departures"]
        coords_r4 = 128-d.textsize(departures_r4,font=fnt)[0]
        d.text((coords_r4,23),departures_r4,font=fnt, fill=(255,187,45))


        matrix = RGBMatrix(options = options)
        matrix.SetImage(frame.convert('RGB'))

        time.sleep(20)




# Code scraps, for later on

# Multindex stuff I tried to use
#by_block = by_block.set_index(["route","dir"])
#print(by_block.xs(["14","0"])) #select the line and the direction, will return all posted upcoming times

# useful as a guide for how to gen rows (think of it as the equivalent to STATA gen command)
#by_block["dirID"] = by_block.apply(lambda row: row["route"]+"-"+row["dir"], axis = 1)
