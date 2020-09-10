import xml.etree.cElementTree as ElementTree
import json, pytz, zipfile, unicodedata, re
from datetime import datetime
from os import listdir
from os.path import isfile, join
import glob


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters.
    Slightly modified from https://github.com/django/django/blob/master/django/utils/text.py
    """ 
    value = str(value)
    try:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii') 
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()
        value = re.sub(r'[-\s]+', '-', value)
    except:
        print('Could not slugify filename, will use default one instead')
        value = 'output'
    return value

creator = "GapX"
version = "1.1"

zip_files = glob.glob("*.zip")

for zip_file in zip_files:
    print("Unzipping " + zip_file)
    zip_ref = zipfile.ZipFile(zip_file, 'r')
    for info in zip_ref.infolist():
        print(info.filename)
        if info.filename.endswith("metadata.json") or info.filename.endswith("rungap.json") or info.filename.endswith("nike.json"):
            zip_ref.extract(info)
    zip_ref.close()

metadata_files = glob.glob("*metadata.json")
data_files = glob.glob("*rungap.json")
data_files += glob.glob("*nike.json")
print("Found metadata files")
print(metadata_files)
print("Found data files")
print(data_files)

if len(metadata_files) != len(data_files):
    print("Error, number of metadata files does not match number of datafiles!")
    exit(1)


for idx, metadata_file in enumerate(metadata_files):
    print("=========")
    print("Parsing " + metadata_file + " and " + data_files[idx])
    metadata_data = json.load(open(metadata_file))
    data = json.load(open(data_files[idx]))

    root = ElementTree.Element("gpx")
    root.set("xmlns","http://www.topografix.com/GPX/1/1")
    root.set("creator", creator)
    root.set("version", version)
    metadata = ElementTree.SubElement(root, "metadata")

    name = metadata_data["title"]
    desc =  metadata_data["description"]
    print("Route name: " + name)
    print("Route description: " + desc)
    ElementTree.SubElement(metadata, "name").text = name
    ElementTree.SubElement(metadata, "desc").text = desc
    ElementTree.SubElement(metadata, "time").text = metadata_data["startTime"]["time"]
    timezone = pytz.timezone(metadata_data["startTime"].get("timeZone", "UTC"))
    source = metadata_data["source"] + " exported by Rungap for iOS, version " + metadata_data["appversion"]
    
    track = ElementTree.SubElement(root, "trk")
    ElementTree.SubElement(track, "name").text = name
    ElementTree.SubElement(track, "desc").text = desc
    ElementTree.SubElement(track, "src").text = source
    segment = ElementTree.SubElement(track, "trkseg")
    if "laps" in data:
        print("Found " + str(len(data["laps"][0]["points"])) + " track points")
        for point in data["laps"][0]["points"]:
            if ("lat" in point and "lon" in point and "ele" in point and "time" in point):
                trkpt = ElementTree.SubElement(segment, "trkpt", lat=str(point["lat"]), lon=str(point["lon"]))
                ElementTree.SubElement(trkpt, "ele").text = str(point["ele"])
                ElementTree.SubElement(trkpt, "time").text = datetime.fromtimestamp(point["time"], timezone).isoformat()
    elif "laps" in metadata_data:
        print("Found " + str(len(metadata_data["laps"])) + " track points")
        for point in metadata_data["laps"]:
            p = point.get("startLocation", {})
            if ("lat" in p and "lon" in p and "startTime" in point):
                #dt = datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%SZ")
                trkpt = ElementTree.SubElement(segment, "trkpt", lat=str(p["lat"]), lon=str(p["lon"]))
                ElementTree.SubElement(trkpt, "time").text = point["startTime"]
        
    gpx_filename =  slugify(name + " - " + datetime.now().isoformat()) + ".gpx"
    print("Writing " + gpx_filename)
    tree = ElementTree.ElementTree(root)
    tree.write(gpx_filename, "UTF-8", True)