import urllib.request
#import requests
import xml.etree.ElementTree as ET
import pandas as pd

#Authenticaion and stop ids definitions
API_key = "6C292EB7ABD605BE358A442D2"
stop_IDs = {"417", "418", "2615", "2616"} # Will need to figure out how to handle multiple stops
#417:15WB, 418:15EB, 2616:14WB, 2615:14EB

#import code -- will figure out later on (want to just get the handling down first)
def fetch_GTFS():
    stop_string = ","
    stop_string = stop_string.join(stop_IDs)

    url = "https://developer.trimet.org/ws/V1/arrivals?locIDs=" + stop_string + "&appID=" + API_key
    response = urllib.request.urlopen(url)
    return response.read()

#Code for parsing --
def parse_GTFS(xmlbody,table):
    root = ET.fromstring(xmlbody)
    for child in root:
        if child.tag.split("}")[1] == "arrival":
            table = append_to_dataframe(child.attrib,table)
    return table

def append_to_dataframe(arrival, table):
    row_dict = {}
    for value in table.columns:
        if value in arrival:
            row_dict[value] = arrival[value]
    table = table.append(row_dict, ignore_index=True)
    return table

def consolidate_by_route_dir(table): #takes a dataframe with rows for each block (bus on a route)
    result = pd.DataFrame(columns=["shortSign","blocks"])
    encounters = set()
    for index, row in table.iterrows():
        if row["shortSign"] in encounters:  # checking to see if this route+dir was already encountered. Using shortSign as a unique id
             #append to the blocks within
             #print(result.loc[result.shortSign == row["shortSign"]])
             thing = 1 #this is just here to fill the line for the block (after the if statement)
        else: #Creating a new row in the results dataframe
            result = result.append({"shortSign":row["shortSign"], "blocks":table.loc[table.shortSign == row["shortSign"]]}, ignore_index=True) #this might be the sourse of a lot of the issues?
            #print("appended")
            #print(table.loc[table.shortSign == row["shortSign"]])
            encounters.add(row["shortSign"])
    return result

def shortSignAliases(rawShortSign): #to be used for consolidating known aliases
    #Want to block the 15 directsions for my purposes
    #TODO Create a dictionary of domain and ranges for appropiate aliases
    return rawShortSign

#"main" starts here
#example: 'block': '1521', 'departed': 'false', 'dir': '0', 'status': 'scheduled', 'fullSign': '15  Belmont/NW 23rd to NW Thurman St', 'piece': '1', 'route': '15', 'scheduled': '1568867948000','estimated': '1568866545000', 'shortSign': '15 To Thurman', 'locid': '417', 'detour': 'true'
by_block = pd.DataFrame(columns=["route","dir","fullSign", "shortSign", "scheduled","estimated", "reason"])
by_block = parse_GTFS(fetch_GTFS(),by_block)

#temporary stuff to see what's going on
print(by_block.head())
by_block.to_csv("dump.csv")

by_route_dir = consolidate_by_route_dir(by_block)
print("afterwards")
print(by_route_dir)
