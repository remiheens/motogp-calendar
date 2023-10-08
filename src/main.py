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

events_already_in_cal = []
# check if exist
ecal.setParams({"calendarId": CALENDAR_ID, "showPastEvents": "1"})
per_page = 100
page = 1
while True:
    ecal.setParams({"calendarId": CALENDAR_ID, "showPastEvents": "1", "page": page, "limit": per_page})
    e = ecal.get("/apiv2/event")

    if len(e) > 0 and "data" in e:
        events_already_in_cal.extend(e['data'])  # Ajoutez les résultats à la liste
        page += 1  # Incrémente le numéro de page pour la prochaine itération
    else:
        break

print(f"{events_already_in_cal}")

def get_emoji_by_type(type):
    if type == "RACE":
        return '🏁'
    elif type == "QUALIFYING":
        return '⏱️'
    elif type == "PRACTICE":
        return '🏍️'
    return ''

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
                    
            event_name = unidecode(event_name.get_text(strip=True)).replace('MotoGP(tm)','')
            
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

                    previous_event_id = ""

                    for ev in events_already_in_cal:
                        if ev["reference"].startswith(broadcast['id']):
                            previous_event_id = ev['id']

                    print(f"ID : {broadcast['id']}")
                    print(f"Name : {get_emoji_by_type(broadcast['kind'])} {broadcast['name']}")
                    print(f"Type : {broadcast['kind']}")
                    print(f"Start : {broadcast['date_start']}")
                    print(f"StartDate : {start.date()}")
                    print(f"StartTime : {start.strftime("%H:%M:%S")}")
                    print(f"End : {broadcast['date_end']}")
                    print(f"EndDate : {end.date()}")
                    print(f"EndTime : {end.strftime("%H:%M:%S")}")
                    print("-------------------------")

                    ecal.setJson({
                        "name": get_emoji_by_type(broadcast['kind']) + "  " + event_name + " - " + broadcast['name'],
                        "location": event_name,
                        "startDate": start.strftime("%Y-%m-%d"),
                        "startTime": start.strftime("%H:%M"),
                        "endDate": end.strftime("%Y-%m-%d"),
                        "endTime": end.strftime("%H:%M"),
                        "timezone": "Europe/Paris",
                        "calendarId": CALENDAR_ID,
                        "reference": broadcast['id']
                    })
                    if len(previous_event_id) > 0:
                        e = ecal.put("/apiv2/event/"+previous_event_id)
                    else:
                        e = ecal.post("/apiv2/event")
                    
                    print(f"{e}")
