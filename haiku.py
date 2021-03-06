#!/usr/bin/python

import json
import keys
import random
import re
import requests
import twitter

pwd = "/home/amarriner/python/haiku/"

# Wordnik API URL
wordnik_api_url = "http://api.wordnik.com:80/v4/word.json/<WORD>/hyphenation?useCanonical=false&limit=50&api_key=" + keys.wordnik_api_key

# List of books to add to the corpus
books = ['pride_and_prejudice.txt', 'emma.txt', 'sense_and_sensibility.txt']

# Compiling regex patterns
p = re.compile(r"(\S.+?[.!?])(?=\s+|$)", re.MULTILINE)
m = re.compile(r"[\(\)\[\]:.,!_?\-;&\'\"]")
s = re.compile(r"[ ]+")

# Build a corpus of text
corpus = ""
for b in books:
   f = open(pwd + 'corpus/' + b)
   corpus = corpus + f.read().replace("\n", " ").replace("Mr.", "Mr").replace("Mrs.", "Mrs").replace("'s ", "s ") + ". "
   f.close()

# Since Wordnik only allows a certain amount of API hits per hour, it's not feasible to run the entire
# corpus through every time this script runs. Therefore, it will cache words its already looked up
# in a syllables.json file to limit the amount of API calls. This next is just loading that file up
# and pulling the existing data (if any) into a dict
f = open(pwd + 'syllables.json')
j = f.read()
if len(j) > 0:
   syllables = json.loads(j)
else:
   syllables = dict()
f.close()

# Get a list of words that require some kind of capitalization or punctuation
f = open(pwd + 'pretty.json')
pretty = json.loads(f.read())
f.close

lookups = 0
corpus_list = []

# Loop through the corpus via regex
for sentence in re.findall(p, corpus):
   c = sentence.strip().lower()
   c = m.sub(" ", c)
   c = s.sub(" ", c)
   corpus_list.append(c)

haiku = []
while len(haiku) < 3:
   sentence = random.choice(corpus_list)
   total = 0

   for w in sentence.split(" "):
      if len(w) > 0:

         # If we don't know the number of syllables in this word, look it up on Wordnik
         if w not in syllables.keys():
            lookups = lookups + 1
            request = requests.get(wordnik_api_url.replace("<WORD>", w))
            result = json.loads(request.content)

            # Store the resulting number of syllables for later reference. Default to 1000 if unsure
            if len(result) > 0:
               syllables[w] = len(result)
            else:
               syllables[w] = 1000

            # Write the current syllables dict out to disk for caching purposes (see above)
            # Inefficient to do at every word, but in case the script dies for some reason
            # I want to limit API calls to Wordnik. Probably only an issue in testing, though 
            f = open(pwd + 'syllables.json', 'w')
            f.write(json.dumps(syllables))
            f.close()

         # Keep track of the total number of syllables in this line so far and continue if it's over the limit
         total = total + syllables[w]
         if total > 7:
            continue

   # Append line to the haiku list if it's the appropriate number of syllables
   if (len(haiku) == 0 and total == 5) or (len(haiku) == 1 and total == 7) or (len(haiku) == 2 and total == 5):
      haiku.append(sentence)

# Assemble the haiku list into a string with capitalization
tweet = ""
for line in haiku:
   l = ""

   for w in line.split(" "):
      if w in pretty.keys():
         l = l + pretty[w] + " "
      else:
         l = l + w + " "

   tweet = tweet + l.strip().capitalize() + "\n"

# Connect to Twitter
api = twitter.Api(keys.consumer_key, keys.consumer_secret, keys.access_token, keys.access_token_secret)

# Tweet haiku
status = api.PostUpdate(tweet + "\n\n#Haiku")
         
# Write the current syllables dict out to disk for caching purposes (see above)
f = open(pwd + 'syllables.json', 'w')
f.write(json.dumps(syllables))
f.close()
