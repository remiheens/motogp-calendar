# -*- coding: utf-8 -*-

"""
get list of gp for current season
parse https://www.motogp.com/fr/calendar
"""

import requests
from bs4 import BeautifulSoup
import json
from dotenv import load_dotenv
import locale
import os
from ecal import EcalClient
from datetime import datetime, timedelta
from unidecode import unidecode


load_dotenv()


domain = "https://www.motogp.com"

ECAL_KEY = os.getenv("ECAL_API_KEY")
ECAL_SECRET = os.getenv("ECAL_API_SECRET")
CALENDAR_ID = os.getenv('ECAL_ID')
ecal = EcalClient()
ecal.setApiKey(ECAL_KEY)
ecal.setApiSecret(ECAL_SECRET)
ecal.setParams({"showDraft": "true"})
cal = ecal.get("/apiv2/calendar/")
print(f"{cal}")

# check if exist
ecal.setParams({"calendarId": CALENDAR_ID, "showPastEvents": "1"})
events_already_in_cal = ecal.get("/apiv2/event")


response = requests.get(domain+"/fr/calendar")
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    events = soup.find_all('a', class_='calendar-listing__event')

    for event in events:
        type = event.find('div', class_="calendar-listing__status-type").text.strip()
        if type.startswith("GP"):
            event_name = event.find('div', class_='calendar-listing__title')
            event_date_start_day = event.find('div', class_='calendar-listing__date-start-day').text.strip()
            event_date_start_month = event.find('div', class_='calendar-listing__date-start-month').text.strip()
            event_date_end_day = event.find('div', class_='calendar-listing__date-end-day').text.strip()
            event_date_end_month = event.find('div', class_='calendar-listing__date-end-month').text.strip()

            for child in event_name.contents:
                if not isinstance(child, str):
                    child.extract()
                    
            event_name = unidecode(event_name.get_text(strip=True))
            
            print(f"############")
            print(f"Nom du GP : {event_name}")
            print(f"Date de l'événement : du {event_date_start_day} {event_date_start_month} au {event_date_end_day} {event_date_end_month}")
            print(f"URL : {domain}{event['href']}")
            print(f"ID : {event['href'].split('/')[-1]}")
            print(f"############")

            responseDetailled = requests.get("https://api.motogp.pulselive.com/motogp/v1/events/"+event['href'].split('/')[-1])
            data_json = json.loads(responseDetailled.text)
            
            for broadcast in data_json['broadcasts']:
                if (broadcast['category']['acronym'] == "MGP" 
                    and broadcast['kind'] in ("RACE", "QUALIFYING", "PRACTICE")):

                    start = datetime.strptime(broadcast['date_start'], "%Y-%m-%dT%H:%M:%S%z")
                    end = datetime.strptime(broadcast['date_end'], "%Y-%m-%dT%H:%M:%S%z")

                    if end == start:
                        end = start + timedelta(minutes=30)

                    if "data" in events_already_in_cal:
                        for ev in events_already_in_cal["data"]:
                            if ev["reference"].startswith(broadcast['id']):
                                ecal.delete("/apiv2/event/" + ev['id'])

                    print(f"ID : {broadcast['id']}")
                    print(f"Name : {broadcast['name']}")
                    print(f"Type : {broadcast['kind']}")
                    print(f"Start : {broadcast['date_start']}")
                    print(f"StartDate : {start.date()}")
                    print(f"StartTime : {start.strftime("%H:%M:%S")}")
                    print(f"End : {broadcast['date_end']}")
                    print(f"EndDate : {end.date()}")
                    print(f"EndTime : {end.strftime("%H:%M:%S")}")
                    print("-------------------------")

                    ecal.setJson({
                        "name": event_name + " - " + broadcast['name'],
                        "location": event_name,
                        "startDate": start.strftime("%Y-%m-%d"),
                        "startTime": start.strftime("%H:%M"),
                        "endDate": end.strftime("%Y-%m-%d"),
                        "endTime": end.strftime("%H:%M"),
                        "timezone": "Europe/Paris",
                        "calendarId": CALENDAR_ID,
                        "reference": broadcast['id']
                    })
                    e = ecal.post("/apiv2/event")
                    
                    print(f"{e}")
