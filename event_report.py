from dhooks import Webhook, File, Embed
import requests
import config
from datetime import datetime
from datetime import timedelta
import os
import time
import traceback
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

hook = Webhook(config.webhook_url)

def make_embed(d,c,t):
    embed = Embed(
        description=d,
        color=c,
        timestamp='now'  # sets the timestamp to current time
    )
    return embed

def discord_funky(text:str):
    return "```"+text+"```"

def send_within_char_limit(embed,offending_text):

    text = offending_text.split(" ")
    to_send = ""
    sent_before = False

    for word in text:
        if to_send == "":
            to_send = word
        else:
            to_send = to_send+" "+word

        if len(to_send) > 600:
            
            if sent_before:
                embed.add_field("",discord_funky(to_send),False)
            else:
                embed.add_field("Event Text",discord_funky(to_send),False)

            sent_before = True
            to_send = ""

    if to_send != "":
        embed.add_field("",discord_funky(to_send),False)

    try:
        hook.send(embed=embed)
    except Exception:
        print(traceback.format_exc())


previous_date = ""

def run():

    if os.name == "nt": #stink windows fix
        current_date = (datetime.today()).strftime('%#m/%#d/%Y')
        last_date = (datetime.today() - timedelta(days = 1)).strftime('%#m/%#d/%Y')
    else:
        current_date = (datetime.today()).strftime('%-m/%-d/%Y')
        last_date = (datetime.today() - timedelta(days = 1)).strftime('%-m/%-d/%Y')

    request = requests.get("https://www.nrc.gov/reading-rm/doc-collections/event-status/event/en.html")

    soup = BeautifulSoup(request.content, 'html.parser') 

 
    #search for everything that has <b>
    text = soup.find_all(name = "b")

    all_text = []

    plants = []

    for section in text:
        extracted_text = section.find_next_sibling(string= True)

        #if the text is Event Text, find the next sibling, then find all descendants that are strings
        if "Event Text" in section.string:
            parent = section.find_next_sibling(class_="border")

            parent = parent.find_all(string = True)
            extracted_text = ""
            
            
            for p in parent:
                extracted_text = extracted_text+p 

        if "Person" in section.string:
            other_text = section.find_next_siblings(string=True)

            extracted_text = ""
            for p in other_text:
                extracted_text = extracted_text+p

        #clean it up
        if not "Event Text" in section.string:
            extracted_text = extracted_text.replace("\n","")

        extracted_text = extracted_text.replace("\r","")
        extracted_text = extracted_text.replace("\t","")

        #special formatting for 10 CFR
        if "Emergency Class" in section.string:
            other_text = section.find_next_siblings(string=True)

            extracted_text = ""
            for p in other_text:
                p = p.replace("\n","")
                p = p.replace("\r","")
                p = p.replace("\t","")
                extracted_text = extracted_text+"\n"+p

        #if we start a new report
        if "Facility" in section.string or "Rep Org" in section.string:
            all_text = []
            plants.append(all_text)

        #this is a power reactor, we can grab the table
        if "Unit" in section.string:
            rx_table = section.findParent()
            rx_table = rx_table.findParent()
            rx_table = rx_table.find_next_sibling()
            rx_table = rx_table.find_all(string = True)
            #remove unnecessary stuff
            while "\n" in rx_table:
                rx_table.remove("\n")

            unit = []
            text_list = []
            start = False

            for t in rx_table:
                if t == "1":
                    start = True

                if t in ["2","3"]:
                    if rx_table[rx_table.index(t)+1] in ["Y","N","y","n"]:
                        unit.append(text_list)
                        text_list = []

                if start:
                    text_list.append(t)

            if text_list != []:
                unit.append(text_list)

            all_text.append(unit)
                

            

        #make it look nicer
        if ":" in section.string:
            all_text.append(section.string+extracted_text)
        else:
            all_text.append(section.string+":"+extracted_text)

    for plant in plants:
        is_power_reactor = False
        for text in plant:
            if "Unit:" in text:
                is_power_reactor = True

        #we dont care about non power reactors
        if is_power_reactor == False:
            plants.pop(plants.index(plant))

    #run it twice for shiggles
    for plant in plants:
        is_power_reactor = False
        for text in plant:
            if "Unit:" in text:
                is_power_reactor = True

        #we dont care about non power reactors
        if is_power_reactor == False:
            plants.pop(plants.index(plant))

    #maybe a third times a charm?
    for plant in plants:
        is_power_reactor = False
        for text in plant:
            if "Unit:" in text:
                is_power_reactor = True

        #we dont care about non power reactors
        if is_power_reactor == False:
            plants.pop(plants.index(plant))

    #why did that work

    for plant in plants:

        embed = make_embed("Event Report",0x00000,"now")


        plant_info = ""
        emergency_class = ""
        notification_info = ""
        event_text = ""
        unit_info = ""

        for text in plant:
            #TODO: good formatting
            if "Facility:" in text:
                plant_info = plant_info+text+"\n"

            if "Unit:" in text:
                plant_info = plant_info+text+"\n"

            if "RX Type:" in text:
                plant_info = plant_info+text

            if "Emergency Class:" in text:
                emergency_class = emergency_class+text

            if "Event Date:" in text:
                notification_info = notification_info+text+"\n"

            if "Event Time:" in text:
                notification_info = notification_info+text+"\n"

            if "Last Update Date:" in text:
                notification_info = notification_info+text

            if "Event Text" in text:
                event_text = (text.replace("Event Text:",""))

            if type(text) == type([]):
                unit_info = "Unit|Code|Crit|I PWR|I Mode|C PWR|C Mode\n"
                for u in text:
                    for t in u:
                        unit_info = unit_info + " " + t

                    unit_info = unit_info + "\n"

        embed.add_field(name = "Plant Info", value = discord_funky(plant_info))
        embed.add_field(name = "Notification Info", value = discord_funky(notification_info))
        embed.add_field(name = "Emergency Class", value = discord_funky(emergency_class), inline = False)
        embed.add_field(name = "Unit Info", value = discord_funky(unit_info), inline = False)
        

        send_within_char_limit(embed,event_text)

        time.sleep(10)
