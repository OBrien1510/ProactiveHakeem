import requests
import pymongo as pm
import datetime
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

        for user in self.user_col.find({"cookie.Address.ChannelId": "skype"}):

            interest = user["interests"]
            print("user", user["Name"])
            # last = datetime.datetime.fromtimestamp(user["lastActive"])
            last = user["lastActive"]
            time_since = datetime.datetime.now() - last

            # if user has been notified in a while and hasn't been talking to the bot in the past 10 minutes
            print("time since", time_since.total_seconds())
            if user["lastNotified"] >= user["Notification"] and time_since.total_seconds() >= 3000:
                self.user_col.find_one_and_update({"User_id": user["User_id"]}, {"$set": {"lastNotified": 0}})
                courses = self.getnewCourses()
                if courses.count() == 0:
                    # if no new courses could be found than send fail message to bot and exit
                    payload = {
                        "Text": "fail",
                        "From": {"id": user["User_id"]}
                    }
                    print("Posting", payload)
                    requests.post(self.host, json=payload, headers={"Content-Type": "application/json"})
                    return

                for course in self.getnewCourses():

                    if course["topic"] in interest:

                        # if there is a newish course that matches a user's interest, then send a notification and break
                        y = ""
                        if course["courseNameArabic"] is None or course["courseNameArabic"] == "":
                            y = "x"
                        else:
                            y = course["courseNameArabic"]
                        payload = {
                            "Text": course["subTopic"] + "$" + y,
                            "From": {"id": user["User_id"]}
                        }
                        print("Posting", payload)
                        requests.post(self.host, json=payload, headers={"Content-Type": "application/json"})

                        return



    def getnewCourses(self):


        course_len = 0
        timeout = 0
        while course_len == 0 or timeout <= 10:
            past = int(time.time()) - datetime.timedelta(seconds=60*60*timeout*5).total_seconds()
            #past = datetime.datetime.utcnow() - datetime.timedelta(days=28)

            courses = self.course_col.find({"Added": {"$gt": past}})
            print("courses", courses.count())
            # return courses that have been added in the past 4 weeks
            timeout += 1
            course_len = courses.count()

        print("returning courses")
        return courses



