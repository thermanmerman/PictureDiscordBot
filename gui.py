# gui.py>

import nltk
from nltk.stem import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()
import pickle
import numpy as np

from keras.models import load_model
model = load_model('/home/pi/Downloads/piChatbot/chatbot_model.h5')
import json
import random

import discord
import os

import string

#import urllib.request as req
#import bs4
#import urllib.parse as parse

  
from selenium import webdriver
import time
import requests
import shutil
import urllib.request

intents = json.loads(open('/home/pi/Downloads/piChatbot/intents.json').read())
words = pickle.load(open('/home/pi/Downloads/piChatbot/words.pkl','rb'))
classes = pickle.load(open('/home/pi/Downloads/piChatbot/classes.pkl','rb'))

bruh = False

client = discord.Client()

def null_count(l):
    #given a list l, find the number of null
    null_count = 0
    
    for element in l:
        if element == None:
            null_count += 1
            
    return null_count


def get_google_img(query):
	#Selenium code to scroll to bottom of the page

	# search_query = "jindo+dog"
	query.replace(' ','+')
	search_query = query

	link = "https://www.google.com/search?q={}&tbm=isch".format(search_query)
	DRIVER_PATH = "/home/pi/Downloads/chromedriver.exe"

	driver = webdriver.Chrome(executable_path=DRIVER_PATH)
	driver.get(link)

	SCROLL_PAUSE_TIME=2
	i=0
	while True:
		i+=1
		# Scroll down to bottom

		# Wait to load page
		time.sleep(SCROLL_PAUSE_TIME)

		#break #insert press load more
		try:
			element = driver.find_elements_by_class_name('mye4qd') #returns list
			element[0].click()
		except:
			break
		

	image_links = driver.find_elements_by_class_name('rg_i.Q4LuWd')
	total = 5

	data_src_links = [image_links[i].get_attribute('data-src') for i in range(total)]
	src_links = [image_links[i].get_attribute('src') for i in range(total)]
	data_src_null_count = null_count(data_src_links)
	src_null_count = null_count(src_links)
	for i,element in enumerate(data_src_links):
		if element == None:
			data_src_links[i] = src_links[i]
	"Nulls: {}, Length: {}".format(null_count(data_src_links), len(data_src_links))
	for i,link in enumerate(data_src_links):
    
		#change comment based on jindo or shiba
		#name = 'jindo{}.png'.format(i) 
		name = 'shiba{}.png'.format(i)
		
		urllib.request.urlretrieve(link, name)
		time.sleep(1)
	driver.quit()

	num = random.randint(0, 4)
	chosen = '/home/pi/Downloads/piChatbot/shiba'+str(num)+'.png'
	return chosen

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
	if len(message.channel_mentions) > 0:
		channel = message.channel_mentions[0]
	else:
		channel = message.channel

	if message.author == client.user:
		return


	print(message.author.name)
	if message.content.startswith('$'):
		strMessage = message.content
		msg = strMessage.replace('$','')
		
		file = open("/home/pi/Downloads/piChatbot/questions.txt", "r+")

		read = file.read()

		async for massage in channel.history(limit = 10):
			if massage.author == client.user:
				if os.stat("/home/pi/Downloads/piChatbot/questions.txt").st_size != 0:
					print(massage.content)
					ints = predict_class(msg, model)
					json_stuff(ints, intents, msg)
					break
		else:
			resp = chatbot_response(msg)
			await message.channel.send(resp)

	if message.content.startswith('!'):
		await message.channel.send("please wait a few seconds")
		strMessage = message.content
		msg = strMessage.replace('!','')
		googResult = get_google_img(msg)
		print(googResult)
		await message.channel.send(file = discord.File(googResult))
		os.remove('/home/pi/Downloads/piChatbot/shiba0.png')
		os.remove('/home/pi/Downloads/piChatbot/shiba1.png')
		os.remove('/home/pi/Downloads/piChatbot/shiba2.png')
		os.remove('/home/pi/Downloads/piChatbot/shiba3.png')
		os.remove('/home/pi/Downloads/piChatbot/shiba4.png')

def clean_up_sentence(sentence):
    sentence_words = nltk.word_tokenize(sentence)
    sentence_words = [lemmatizer.lemmatize(word.lower()) for word in sentence_words]
    return sentence_words

# return bag of words array: 0 or 1 for each word in the bag that exists in the sentence

def bow(sentence, words, show_details=True):
    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)
    # bag of words - matrix of N words, vocabulary matrix
    bag = [0]*len(words)
    for s in sentence_words:
        for i,w in enumerate(words):
            if w == s:
                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print ("found in bag: %s" % w)
    return(np.array(bag))

def predict_class(sentence, model):
    # filter out predictions below a threshold
    p = bow(sentence, words,show_details=False)
    res = model.predict(np.array([p]))[0]
    ERROR_THRESHOLD = 0.25
    results = [[i,r] for i,r in enumerate(res) if r>ERROR_THRESHOLD]
    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []
    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list


def json_stuff(ints, intents_json, msg):
    tag = ints[0]['intent']
    list_of_intents = intents_json
    letters = string.ascii_lowercase
    newTag = ''.join(random.choice(letters) for i in range(10))

    for i in list_of_intents:
        file = open("/home/pi/Downloads/piChatbot/questions.txt", "r+")
        newQuestion = file.read()

        with open('/home/pi/Downloads/piChatbot/intents.json', 'r') as outfile:
            z=json.load(outfile)
            temp = z['intents']
            temp.insert(0, {
                'tag': newTag,
                'patterns': [newQuestion],
                'responses': [msg],
                "context": [ "" ]})


        with open('/home/pi/Downloads/piChatbot/intents.json', 'w') as outfile:
            json.dump(z, outfile, indent = 4)

        file.truncate(0)
        file.close()

        break

def getResponse(ints, intents_json, msg):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:

        if(i['tag'] == 'noanswer'):
                    file = open("/home/pi/Downloads/piChatbot/questions.txt", 'w')
                    newQuestion = file.write(msg)
                    file.close()
                    result = "I don't know that one. Please input what you would like me to say next time someone asks me that."
                    break     
                    
        elif(i['tag']== tag):
                result = random.choice(i['responses'])
                break

    return result

    

def chatbot_response(msg):
    ints = predict_class(msg, model)
    res = getResponse(ints, intents, msg)
    return res

client.run('ODM0NTgxNDA0ODI2MDc1MTY3.YIC-gA.OtnIQD5GU2myZmNytoDtQyM_SpA')