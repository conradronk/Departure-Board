import urllib.request
#import requests
import xml.etree.ElementTree as ET
import pandas as pd

#Authentication and stop ids definitions
keys_txt = open("keys.txt","r")

API_key = keys_txt.readline()
keys_txt.close()

stop_IDs = {"417", "418", "2615", "2616"} # Will need to figure out how to handle multiple stops
#417:15WB, 418:15EB, 2616:14WB, 2615:14EB

def fetch_GTFS():
    stop_string = ","
    stop_string = stop_string.join(stop_IDs)

    url = "https://developer.trimet.org/ws/V1/arrivals?locIDs=" + stop_string + "&appID=" + API_key
    response = urllib.request.urlopen(url)
    return response.read()


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


def shortSignAliases(rawShortSign): #to be used for consolidating known aliases
    #Want to block the 15 directsions for my purposes
    #TODO Create a dictionary of domain and ranges for appropiate aliases
    return rawShortSign


#"main" starts here
#example: 'block': '1521', 'departed': 'false', 'dir': '0', 'status': 'scheduled', 'fullSign': '15  Belmont/NW 23rd to NW Thurman St', 'piece': '1', 'route': '15', 'scheduled': '1568867948000','estimated': '1568866545000', 'shortSign': '15 To Thurman', 'locid': '417', 'detour': 'true'
by_block = pd.DataFrame(columns=["route","dir","fullSign", "shortSign", "scheduled","estimated", "reason"])
by_block = parse_GTFS(fetch_GTFS(),by_block)

#setting up the multiIndex to enable easy filtering by route and/or direction
by_block = by_block.set_index(["route","dir"])
print(by_block.xs(["14","0"]))


#useful as a guide for how to gen rows (think of it as the equivalent to STATA gen command)
#by_block["dirID"] = by_block.apply(lambda row: row["route"]+"-"+row["dir"], axis = 1)
