import urllib.request
#import requests
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import time
import math

#need to address how I'm getting NaN for some of the later departures

#Authentication and stop ids definitions
keys_txt = open("keys.txt","r")

API_key = keys_txt.readline()
keys_txt.close()

stop_IDs = {"417", "418", "2615", "2616"}
#417:15WB, 418:15EB, 2616:14WB, 2615:14EB

#determines how far out relative timings will be used
relative_time_horizon = 15000

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
    #Want to block the 15 directions for my purposes
    #TODO Create a dictionary of domain and ranges for appropiate aliases
    return rawShortSign


def relativeTimingInfo(eventTime):
    currentTime = time.time()*1000
    eventTime = int(eventTime)
    if (eventTime-currentTime>relative_time_horizon):
        return str(math.floor(((eventTime-currentTime)/1000)/60))
    else:
        return str("XX:XX") #str(time.localtime(eventTime/1000))

def humanReadable(table): #pass the entire table, converts into something more human readable ready for display formatting
    output = pd.DataFrame(columns=["line","bound_to", "departures"])
    routes = table["route"].unique()

    for i in routes:
        dirs = table.loc[table["route"] == i]["dir"].unique()
        for j in dirs:
            relevantLines = (table.loc[(table["route"] == i) & (table["dir"] == j)]) #selects the rows that have the exact right line and direction
            departureTimes = ""
            for index, row in relevantLines.iterrows():
                print("this is a new line") # will be adding code here to make the first addition different (no leading spaces)
                departureTimes += " " + relativeTimingInfo(row["estimated"])
                print(departureTimes)
            output = output.append({"line":i,"bound_to":j,"departures":departureTimes},ignore_index=True)
            print(output)

    print(output)
    return output #returns a single line with all selected buses


#"main" starts here
#example: 'block': '1521', 'departed': 'false', 'dir': '0', 'status': 'scheduled', 'fullSign': '15  Belmont/NW 23rd to NW Thurman St', 'piece': '1', 'route': '15', 'scheduled': '1568867948000','estimated': '1568866545000', 'shortSign': '15 To Thurman', 'locid': '417', 'detour': 'true'
by_block = pd.DataFrame(columns=["route","dir","fullSign", "shortSign", "scheduled","estimated", "reason"])
by_block = parse_GTFS(fetch_GTFS(),by_block)

humanReadable(by_block)

#setting up the multiIndex to enable easy filtering by route and/or direction
by_block = by_block.set_index(["route","dir"])
#print(by_block.xs(["14","0"])) #select the line and the direction, will return all posted upcoming times



#useful as a guide for how to gen rows (think of it as the equivalent to STATA gen command)
#by_block["dirID"] = by_block.apply(lambda row: row["route"]+"-"+row["dir"], axis = 1)
