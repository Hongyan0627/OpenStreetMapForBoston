import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint
import string
import codecs
import json

""""
3 regular expressions to check for certain patterns in the tags
"""
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')


street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)


"""
Expected street types. I add some uncommon ones for boston area such as 'Terrace','Park','Wharf'
"""
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons","Broadway","Highway","Terrace","Park","Wharf"]

mapping = { "St": "Street",
            "St.": "Street",
            'Ave':"Avenue",
            'Rd.':"Road",
            'Ave.':"Avenue",
            "Ct":"Court",
            "Rd":"Road",
            "st":"Street"
            }

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
            


def count_tags(filename):
    """
    Find different tag names. Count for each tag. 
    Input: file name
    Output: a dictionary with tag names as keys and count as values
    """
    result = {}
    for event,elem in ET.iterparse(filename):
        result[elem.tag] = result.get(elem.tag,0) + 1
    return result
    

def key_type(element, keys):
    """
    check the "k" value for each "<tag>" and see if they can be valid keys in MongoDB
    """
    if (element.tag == "tag"):
        if lower.search(element.attrib['k']):
            keys["lower"] = keys["lower"] + 1
        elif lower_colon.search(element.attrib['k']):
            keys["lower_colon"] += 1
        elif problemchars.search(element.attrib['k']):
            keys["problemchars"] += 1
        else:
            keys["other"] += 1
        
    return keys

def get_user(element):
    """
    find out how many unique users
    have contributed to the map in this particular area
    """
    return element.attrib["uid"]



def is_street_name(elem):
    """
    See if an elem 'k' value is street
    Input: element
    Output: True/False
    """
    return (elem.attrib['k'] == "addr:street")


def audit_street_type(street_types, street_name):
    """
    If street_name is not in our expected street types, add it to street_types.
    Input: street_types is a dictionary, street_name is a string
    Output: No output. Update the street_types dictionary
    """
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)
            
def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):
        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v']) 
    return street_types

def update_name(name, mapping):
    """
    Update the old street name to a better name based on dictionary mapping
    """
    for key in mapping:
        if key in name:
            name = string.replace(name,key,mapping[key])
            break
    return name


def shape_element(element):
    """
    Shape the element to our expected data structure.
    """
    node = {}
    
    if element.tag == "node" or element.tag == "way" :
        node["tag_type"] = element.tag
        attributes = element.attrib.keys()
        temp_created = {}
        temp_pos = [None,None]
        temp_address = {}
        temp_node_refs = []
        
        # loop over all attributes of the input element
        
        for item in attributes:
            
            if item in CREATED:
                temp_created[item] = element.attrib[item]
            elif (item == 'lat'):
                temp_pos[0] = float(element.attrib[item])
            elif (item == 'lon'):
                temp_pos[1] = float(element.attrib[item])
            else:
                node[item] = element.attrib[item]
        
                
        # loop over all second level elments in the input element
        for second_element in element.iter():         
            
            attributes = second_element.attrib.keys()
            
            for item in attributes:
                
                if item == 'v':
                    continue
                elif item in CREATED:
                    temp_created[item] = second_element.attrib[item]
                elif (item == 'lat'):
                    temp_pos[0] = float(second_element.attrib[item])
                elif (item == 'lon'):
                    temp_pos[1] = float(second_element.attrib[item])
                elif item == 'k':
                    temp_str = second_element.attrib['k']
                    if (problemchars.search(temp_str)):
                        continue
                    elif (temp_str == "address"):
                        address_list = second_element.attrib['v'].split(' ')
                        for i in range(len(address_list)):
                            if (len(address_list[i]) > 0 and address_list[i][-1] == ','):
                                address_list[i] = address_list[i][0:len(address_list[i])-1]
                        if (len(address_list) == 6):
                            try:
                                temp_address['housenumber'] = str(int(address_list[0]))
                                temp_address['street'] = " ".join(address_list[1:3])
                                temp_address['city'] = address_list[3]
                                temp_address['state'] = 'MA'
                                if (address_list[-1].startswith("02") and len(address_list[-1]) >= 5):
                                    temp_address['postcode'] = address_list[-1][0:5]
                            except:
                                pass
                        elif (len(address_list) > 6):
                            try:
                                if (address_list[-1].startswith("02") and len(address_list[-1]) >= 5):
                                    temp_address['postcode'] = address_list[-1][0:5]
                                temp_address['state'] = 'MA'
                                temp_address['housenumber'] = str(int(address_list[0]))
                                temp_address['city'] = address_list[len(address_list)-3]
                                temp_aadress['street'] = " ".join(address_list[1:len(address_list)-3])
                            except:
                                pass
                        else:
                            pass
                    elif temp_str.startswith('addr:'):
                        
                        if (temp_str.find(':',5) == -1):
                            temp_address[temp_str[5:]] = second_element.attrib['v']
                        else:
                            continue
                    else:
                        node[second_element.attrib['k']] = second_element.attrib['v']
                elif (item == 'ref'):
                    temp_node_refs.append(second_element.attrib[item])
                else:
                    node[item] = second_element.attrib[item]
        
        if (len(temp_node_refs) > 0):
            node['node_refs'] = temp_node_refs
            
        if (len(temp_created.keys())>0):
            node["created"] = temp_created
            
        if (temp_pos[0] and temp_pos[1]):
            node['pos'] = temp_pos
            
        if (len(temp_address.keys()) > 0):
            node['address'] = temp_address
            if ("street" in node["address"]):
                node["address"]["street"] = update_name(node["address"]["street"], mapping)
        return node
    else:
        return None
        




    

def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data

def test():
    data = process_map('boston_massachusetts.osm', True)

test()