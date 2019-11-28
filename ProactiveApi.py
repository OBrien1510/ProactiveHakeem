import random
import requests
import pymongo as pm
import datetime
from dateutil.parser import parse
import time
import json


class ProactiveApi:
    uri = "mongodb://hakeemdb:ESmBikpcBDGdwAJ3NEpRhmOIlyVhJ1TKzbllvXm8GdDWYyBYrAGsa0Tp19MB0YoWVQAyW3522vGAcN3C72N2Rg==@hakeemdb.documents.azure.com:10255/?ssl=true&replicaSet=globaldb"

    def __init__(self):
        self.client = pm.MongoClient(self.uri)
        self.db = self.client.hakeemdb
        self.user_col = self.db.users
        self.course_col = self.db.hakeem_course_list
        self.host = "https://testsloteurope.azurewebsites.net/api/ProactiveApi"
        #self.host = "http://localhost:3979/api/ProactiveApi"

    def checkUserActivity(self):
        for user in self.user_col.find({"conversationReference.ChannelId": "skype"}):
            interest = user["interests"]
            if "Computers" in interest or "Video Games" in interest:
                interest.append("Technology")
            elif "Sports" in interest:
                interest.append("Fitness")
            elif "Reading" in interest or "Writing" in interest:
                interest.append("Creative Writing")
            elif "Economics" in interest or "Finance" in interest:
                interest.append("Economics and Finance")
            elif "Nature" in interest:
                interest.append("Biology")
            print("user", user["Name"])
            # last = datetime.datetime.fromtimestamp(user["lastActive"])
            last = user["lastActive"]
            print(user["lastNotified"])
            time_since = datetime.datetime.utcnow() - last
            # if user hasn't been active in a year, delete their user profile
            if time_since.days >= 365:
                self.user_col.delete_one({"User_id": user["User_id"]})

            # if user has been notified in a while and hasn't been talking to the bot in the past 10 minutes
            elif user["lastNotified"] >= user["Notification"] and time_since.total_seconds() >= 600:
                self.user_col.find_one_and_update({"User_id": user["User_id"]}, {"$set": {"lastNotified": 0}})
                courses = list(self.getnewCourses())
                if len(courses) == 0:
                    # if no new courses could be found than send fail message to bot and exit
                    payload = {
                        "Text": "fail",
                        "From": {"id": user["User_id"]}
                    }
                    print("Posting", payload)
                    requests.post(self.host, json=payload, headers={"Content-Type": "application/json"})
                    return
                random.shuffle(courses)
                for course in courses:
                    if course["topic"] in interest or course["subTopic"] in interest:
                        payload = {
                            "Text": course["subTopic"] + "$" + course["subTopicArabic"] + "$" + course["topic"] + "$" + course["topicArabic"],
                            "From": {"id": user["User_id"]}
                        }
                        print("Posting", payload)
                        requests.post(self.host, json=payload, headers={"Content-Type": "application/json"})

                        return

                # if none of the courses match the user interests then pass the failure payload to the bot
                payload = {
                    "Text": "fail",
                    "From": {"id": user["User_id"]}
                }
                print("Posting", payload)
                requests.post(self.host, json=payload, headers={"Content-Type": "application/json"})
                return

            elif user["lastNotified"] < user["Notification"]:

                self.user_col.update({"User_id": user["User_id"]}, {"$inc": {"lastNotified": 1}})

    def getnewCourses(self):
        course_len = 0
        timeout = 0
        while course_len == 0 and timeout <= 10:
            past = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            courses = self.course_col.find({"lastUpdated": {"$gt": past.isoformat()}})
            print("courses", courses.count())
            # return courses that have been added in the past 4 weeks
            timeout += 1
            course_len = courses.count()

        print("returning courses")
        return courses
