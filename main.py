from dhooks import Webhook, File, Embed
import requests
import config
from datetime import datetime
from datetime import timedelta
import os
import time
import event_report

hook = Webhook(config.webhook_url)



def make_embed(d,c,t):
    embed = Embed(
        description=d,
        color=c,
        timestamp='now'  # sets the timestamp to current time
    )
    return embed

previous_date = ""

while True:

    if os.name == "nt": #stink windows fix
        current_date = (datetime.today()).strftime('%#m/%#d/%Y')
        last_date = (datetime.today() - timedelta(days = 1)).strftime('%#m/%#d/%Y')
    else:
        current_date = (datetime.today()).strftime('%-m/%-d/%Y')
        last_date = (datetime.today() - timedelta(days = 1)).strftime('%-m/%-d/%Y')
    try:
        request = requests.get("https://www.nrc.gov/reading-rm/doc-collections/event-status/reactor-status/powerreactorstatusforlast365days.txt")

        lines = request.text.split("\r\n")
        lines.pop(0)

        if previous_date != current_date and current_date in lines[0]:

            previous_date = current_date

            formatted_lines = []

            last_powers = []

            for line in lines:
                if line == " ": 
                    continue

                line_content = line.split("|")
                date = line_content[0]
                plant_name = line_content[1]
                power = line_content[2]

                date = date.split(" ")[0]

                if not plant_name in config.accepted_plants and config.accepted_plants != []:
                    continue

                if date == current_date:
                    formatted_lines.append("%s : %s" % (plant_name,power)) 
                elif date == last_date:
                    last_powers.append(power)
                else:
                    break




            big_string = ""

            for line in formatted_lines:

                line_index = formatted_lines.index(line)
                last_power = last_powers[line_index]
                current_power = line.split(" : ")[1]

                if last_power != current_power:
                    line = "**__"+line+"__**"

                if big_string == "":
                    big_string = line
                else:
                    big_string = big_string+"\r\n"+line




            embed = make_embed(big_string,0x00000,current_date)
            hook.send(embed=embed)

        if config.event_report_checks:
            event_report.run()

        time.sleep(3600)
    except:
        time.sleep(600) #Maybe their servers are cooked?