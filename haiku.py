#!/usr/bin/python

from random import shuffle

import json
import keys
import re
import requests

# Wordnik API URL
wordnik_api_url = "http://api.wordnik.com:80/v4/word.json/<WORD>/hyphenation?useCanonical=false&limit=50&api_key=" + keys.wordnik_api_key

books = ['pride_and_prejudice.txt', 'emma.txt', 'sense_and_sensibility.txt']

# Compiling regex patterns
p = re.compile(r"(\S.+?[.!?])(?=\s+|$)", re.MULTILINE)
m = re.compile(r"[\(\)\[\]:.,!_?\-;&\'\"]")
s = re.compile(r"[ ]+")

# Build a corpus of text
corpus = ""
for b in books:
   f = open('corpus/' + b)
   corpus = f.read().replace("\n", " ").replace("Mr.", "Mr").replace("Mrs.", "Mrs").replace("'s ", "s ")
   f.close()

# Since Wordnik only allows a certain amount of API hits per hour, it's not feasible to run the entire
# corpus through every time this script runs. Therefore, it will cache words its already looked up
# in a syllables.json file to limit the amount of API calls. This next is just loading that file up
# and pulling the existing data (if any) into a dict
f = open('syllables.json')
j = f.read()
if len(j) > 0:
   syllables = json.loads(j)
else:
   syllables = dict()
f.close()

lookups = 0
corpus_list = []

# Loop through the corpus via regex
for sentence in re.findall(p, corpus):

   # Since a sentence with more than 7 words would be too long for any haiku line, ignore those
   #if len(sentence.split(" ")) < 7:
   c = sentence.strip().lower()
   c = m.sub(" ", c)
   c = s.sub(" ", c)
   corpus_list.append(c)

haiku = []
shuffle(corpus_list)
for sentence in corpus_list:
   # print sentence.strip()
   total = 0

   for w in sentence.split(" "):
      if len(w) > 0:
         if w not in syllables:
            lookups = lookups + 1
            print "Looking up '" + w + "' on wordnik (" + str(lookups) + ") ..."
            request = requests.get(wordnik_api_url.replace("<WORD>", w))
            result = json.loads(request.content)

            if len(result) > 0:
               syllables[w] = len(result)
            else:
               syllables[w] = 1000

            # Write the current syllables dict out to disk for caching purposes (see above)
            f = open('syllables.json', 'w')
            f.write(json.dumps(syllables))
            f.close()

         total = total + syllables[w]
         if total > 7:
            continue

   if len(haiku) == 0 and total == 5:
      haiku.append(sentence)
   if len(haiku) == 1 and total == 7:
      haiku.append(sentence)
   if len(haiku) == 2 and total == 5:
      haiku.append(sentence)
   if len(haiku) == 3:
      break

for line in haiku:
   print line.capitalize().strip()
         
# Write the current syllables dict out to disk for caching purposes (see above)
f = open('syllables.json', 'w')
f.write(json.dumps(syllables))
f.close()
