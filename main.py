# -*- coding: utf-8 -*-
"""
Created on Fri Aug  4 18:02:18 2017

@author: Dylan
"""
import requests
import csv
import yaml
from pprint import pprint
from time import localtime
from math import floor
from ast import literal_eval

with open("config.yml", 'r') as ymlfile:
    cfg = yaml.load(ymlfile)
    token = cfg['token']
    baseUrl = cfg['apiUrl']
    groupId = '29613589'
    myId = cfg['myId']

class Group():
    """ Handle a group's messages, people, requests, and associated files """
    def __init__(self, groupId, update=False):
        self.groupUrl = baseUrl + "/groups/" + groupId
        self.basePayload = {'token': token}
        self.update = update
        self.getGroupData()

    def makeRequest(self, url, payload):
        r = requests.get(url, params=payload)
        if self.ensureRequest(r.status_code):
            return r
        else:
            return None

    def ensureRequest(self, code):
        if code != 200:
            print("Request failed you jabroni. Code: ", code)
            return False
        return True

    def getGroupData(self):
        r = self.makeRequest(self.groupUrl, self.basePayload)
        if r:
            self.groupData = r.json()['response']
            self.fn = self.groupData['name'] + '.csv'
            self.buildPeople()
            if self.update:
                self.updateAndWriteMessages()
            self.readMessages()
        else:
            raise Exception("Can't get group data")
#    peopleDict = buildPeopleDict(groupData['members'])
#    messagesList = buildMessagesList(groupRequestUrl, payload, groupFilename, update)
    def buildPeople(self):
        self.people = [Person(member) for member in self.groupData['members']]

    def updateAndWriteMessages(self):
        """ Request all the groups messages and write data to csv """
        with open(self.fn, "w", encoding='utf-8', newline='') as f:
            url = self.groupUrl + '/messages'
            payload = self.basePayload
            payload['limit'] = 100

            oldestTime = localtime()
            allMessages = []
            r = self.makeRequest(url,payload)
            if r:
                messages = r.json()['response']['messages']
                messagesDict = messages[0]
                messagesDict['event'] = 'need this field for now'
                writer = csv.DictWriter(f, messagesDict.keys())
                writer.writeheader()

                while(payload['limit'] > 1):
                    r = self.makeRequest(url, payload)
                    if r:
                        messages = r.json()['response']['messages']
                        userMessages = list(filter(lambda d: d['sender_type'] == 'user', messages))
                        allMessages += userMessages

                        # update before_id
                        nMessages = len(messages)
                        print("Got {} messages".format(nMessages))
                        lastMessage = messages[nMessages-1]
                        payload['before_id'] = lastMessage['id']
                        oldestTime = localtime(lastMessage['created_at'])
                    else:
                        lim = payload['limit']
                        payload['limit'] = floor(lim/2)

                print("Writing {} messages to {}".format(len(allMessages), f))
                writer.writerows(allMessages)
            else:
                print("Couldn't get first set of messaeges")
                return False
        return True

    def readMessages(self):
        """ Serialize messages into memory from csv """
        with open(self.fn, "r", encoding='utf-8', newline='') as f:
            messageReader = csv.DictReader(f)
            self.messages = [Message(message) for message in messageReader]


    def stats(self):
        for message in self.messages:
            if message.userId == myId:
                print ("Message with {} likes:\n {} \n".format(message.favorites, message.text))



class Person():
    def __init__(self, member):
        self.userId = member['user_id']
        self.nicknames = [member['nickname']]
        self.otherId = member['id']
        self.messages = []
        self.likes = []

    def addMessage(self, message):
        self.messages.append(message)

    def addMessages(self, messages):
        self.messages += messages

class Message():
    def __init__(self, mDict):
        self.mDict = mDict
        self.userId = mDict['user_id']
        self.favorites = literal_eval(mDict['favorited_by'])
        self.nFavorites = len(self.favorites)
        self.text = mDict['text']
        self.time = localtime(int(mDict['created_at']))
        self.attachments = mDict['attachments']

def main():
    group = Group(groupId, False)
    group.stats()



main()

