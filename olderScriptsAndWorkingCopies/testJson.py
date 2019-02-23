# Error checking script when JSON not harvestable
import requests
import json

r = requests.get('https://geodata.iowa.gov/data.json/')
r.encoding = 'utf-8'

try:
    foo = json.loads(r.text, 'utf-8')
    print "Yay, I got a json from geodata!"
except Exception, e:
    print "Why didn't i get a json from geodata? Maybe it wasn't a json..."
    print "What is it then? It seems is a {0} whose length is {1}".format(
        r.text.__class__, len(r.text)
    )