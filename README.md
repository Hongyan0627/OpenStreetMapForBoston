# OpenStreetMap Project
### Map Area: Boston, MA, United States

<https://www.openstreetmap.org/relation/1507233>
<http://metro.teczno.com/#charlotte>

## 1. Problems Encountered in the Map

After generating a sample osm file for Boston area and running it against my auditdata.py, I noticed several main problems with the data:

* Over-abbreviated street names and uncommon street names
* In some elements, there are some attributes 'k' whose values are "type" or "address"

### Over-abbreviated street names and uncommon street names

Some street names are like "St","St.","Ave","Ct" and so on. I update all these street names and change them to expected street names like "Street","Avenue", "Court" and so on. Also, I find there are some uncommon street names such as "Wharf","Park", "Terrace". I add these uncommon street names to my expected steet names. 

###  In some elements, there are some attributes 'k' whose values are "type" or "address"

At first, I plan to use "type" to represent "node" or "way". Then I noticed that in some elements, The value of 'k' attribute is "type", and the value of 'v' may be like "County". I decided to use another name "tag_type" to represent "node" or "way" since the name doesn't influence our statistics.

Some values of 'k' are "address" and the corresponding 'v' values are like "200 Nashua Street, Boston, MA 02114","300 South St, Brookline, MA". They contain information for address. I want to transfer these strings to our data structure "{"address":{"housenumber":...,"city":...}}". This is very difficult because some strings contain zipcode but others don't. Besides, these strings for address may miss different part of the whole information. The postcodes for Boston area all start with "02" and the states should all be "MA". Besides, I noticed the strings for "address" are well splited by space. After spliting the string by space, I get a list. When the length of this list is 6, it means the pattern is [housenumber,street_name,street_type,city,state,postcode]. When the postcode doesn't start with "02", I just ignore that data. Wehn the length of postcode is longer than 5, I just take the first 5 digits as it's postcode. I use the following code to do this transformation.

```
elif (temp_str == "address"): # if 'k' = 'address'
	address_list = second_element.attrib['v'].split(' ') # split 'v' value by space
    for i in range(len(address_list)):     # delete any ','
    	if (address_list[i][-1] == ','):
        	address_list[i] = address_list[i][0:len(address_list[i])-1]
    # when address length is 6, it's like [housenumber,street_name,street_type,city,state,postcode]
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

```

## 2. Data Overview

This section contains basic statistics about the dataset and the MongoDB queries used to gather them.

File sizes

boston_massachusetts.osm....................359 MB
boston_massachusetts.osm.json...............529 MB

### Number of documents

```
db.boston.find().count()
```
1851781

### Number of nodes
```
db.boston.find({"tag_type":"node"}).count()
```
1605526

### Number of ways
```
db.boston.find({"tag_type":"way"}).count()
```
246255

### Number of unique users
```
len(db.boston.distinct("created.user"))
```
910

### Top 1 contributing user
```
pipeline = [{"$group":{"_id":"$created.user","count":{"$sum":1}}},{"$sort":{"count":-1}},{"$limit":1}]
db.boston.aggregate(pipeline)

```
{u'count': 1058618, u'_id': u'crschmidt'}

### Number of users appearing only once(having 1 post)
```
pipeline = [{"$group":{"_id":"$created.user","count":{"$sum":1}}},{"$group":{"_id":"$count","num_users":{"$sum":1}}},{"$match":{"_id":1}}]
db.boston.aggregate(pipeline)

```
{u'num_users': 216, u'_id': 1}

## 3 Additional Ideas

### Contributor statistics

* Top user contribution percentage('crschmidt')- 57.16%
* Top 2 users contribution percentage('crschmidt' and 'jremillard-massgis')-77.88%
* Top 5 users contribution percentage - 88.92%
* Top 10 users contribution percentage - 94.73%
* Top 15 users contribution percentage - 96.00%
* Top 20 users contribution percentage - 96.84%

We can see that most contribution are from 'crschmidt' and 'jremillard-massgis'. And top 10 users contribute about 94.73%, other 900 users contribute only 5.27%.

Only very few users contribute the data for Boston area and most users contribute very little. If we can set some "reward policy", maybe more users would be interested in doing more contribution. 

### Other data exploration using MongoDB queries

#### Popular street names 
```
pipeline = [{"$group":{"_id":"$address.street","count":{"$sum":1}}},{"$sort":SON([("count",-1)])}]
db.boston.aggregate(pipeline)

```

Most documents don't have an "address" or "street", but for those documents which have one, we can see:

No. 1 : {u'count': 150, u'_id': u'Massachusetts Avenuenue'} - 'Massachusetts Avenue'

"Massachusetts Avenue" is a long avenue in Boston. There is no surprise that many addresses are on this avenue. 

No.2 - No.5: {u'count': 57, u'_id': u'Josephine Avenue'},u'count': 55, u'_id': u'Cambridge Street'},{u'count': 50, u'_id': u'Waverly Street'},{u'count': 48, u'_id': u'Beacon Street'}

#### Popular cities
```
pipeline = [{"$group":{"_id":"$address.city","count":{"$sum":1}}},{"$sort":SON([("count",-1)])}]
db.boston.aggregate(pipeline)

```
We can expect that No.1 would be Boston. But normally "Boston area" includes some other around cities or towns. We can see the popularity rank for them. 

No.1 "Boston" - {u'count': 760, u'_id': u'Boston'}

No surprise.

No.2 "Cambridge" - {u'count': 350, u'_id': u'Cambridge'}

Harvard University and MIT are located at Cambridge. There are many students in Cambridge. Maybe that's one reason why Cambridge is popular. 

No.3 "Somerville"-{u'count': 158, u'_id': u'Somerville'}

No.4 "Quincy"-{u'count': 74, u'_id': u'Quincy'}

No.5 "Brookline"-{u'count': 63, u'_id': u'Brookline'}

#### Other ideas about the datasets

* One way to improve the quality of this dataset is that we can design a pattern such taht when user contributes, they all follow this pattern. In this case, when user contributes data, they will be reminded that they need to input what information. Maybe this way can help user contribute more complete documents. But the disadvantage is that this may discourage users from contributing. Because some users may feel it's too complicated to contribute. As we can see from the statistics of users, most data are from few users. 
* Another way is that we can set some "reward policy". For example, for the top 1 user, we can give him/her some grades or other gifts. Then other users will have more motivation to contribute. But I'm worried that the top 1 user is all fixed for a long time, since we can see that now the top 1 user contributes more than 50 %. 
* Another way is Gamification. When the contribution process becomes a game, we can expect that more users will get involved. The difficulty is that those top users may be not interested in such games. 


## Conclusion
After analyzing the dataset by MongoDB, I find that even though the dataset is well cleaned, it's imcomplete for most documents. For example, when I analyze the popular cities and popular streets, in fact, most documents don't have a "city" or "address". If they all have such attributes, the analysis results would be more convincing. All documents have "user", and by the analysis, we can find that these data are most from several users. I see a lot of fun in analyzing the dataset by MongoDB and I also realize that it's very important to have high quality data for analysis. 


