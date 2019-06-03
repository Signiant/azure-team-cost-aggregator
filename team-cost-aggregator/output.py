import json
import mail
import datetime
import os


def get_team_totals(config_map, folder, debug):
    team_costs = dict()
    team_prev_costs = dict()
    team_period = dict()
    total_cost = 0
    total_prev_cost = 0

    # Get all the results files in the folder
    all_team_results_files = os.listdir(folder)

    for team_result_file in all_team_results_files:
        team_cost = 0

        # get the team name from the filename
        filename_bits = team_result_file.split('.json')
        if len(filename_bits) == 2:
            team_name = filename_bits[0]
        else:
            team_name = "unknown"

        # Get the full path of the file and open it
        team_result_fullpath = os.path.join(folder, team_result_file)

        # Skip if we have a sub-dir
        if os.path.isdir(team_result_fullpath):
            continue

        # is this a previous run file?  skip it and read the values later
        if str(team_result_fullpath).endswith(".prev"):
            continue

        print("Reading data from: " + str(team_result_fullpath))

        with open(team_result_fullpath) as data_file:
            team_data = json.load(data_file)
            if debug:
                print(team_data)
            data_file.close()

        # Now get the total for this team
        # and save it off so we can sort these later
        team_costs[team_name] = float("{0:.2f}".format(team_data['cost']))
        team_period[team_name] = team_data['start'] + " - " + team_data['end']

        # See if we have some previous results so we can show a percent change
        team_result_prev_fullpath = team_result_fullpath + ".prev"
        if os.path.exists(team_result_prev_fullpath):
            print("previous results exist for " + team_name + ".  Reading " + team_result_prev_fullpath)

            # read these in the same as the main results and save off the previous report value
            with open(team_result_prev_fullpath) as prev_file:
                team_prev_data = json.load(prev_file)
                if debug:
                    print(team_prev_data)
                prev_file.close()

            # Now get the total for this team
            team_prev_cost = float("{0:.2f}".format(team_prev_data['cost']))
            if debug:
                print("Team previous cost is " + str(team_prev_cost))

            # and save it off so we can sort these later
            team_prev_costs[team_name] = team_prev_cost

    # ok, let's output stuff (email only likes inline styles....)
    table = "<table>"
    table = table + "<tr><th style='padding: 15px;'>Team</th><th style='padding: 15px;'>Period</th><th style='padding: 15px;'>Cost</th><th style='padding: 15px;'>Previous</th><th style='padding: 15px;'>% Change</th></tr>"

    # We now have a dict of team costs...let's process it (sorted)
    # for key, value in sorted(team_costs.items(), key=lambda (k, v): (v, k), reverse=True):
    for key, value in team_costs.items():
        prev_cost = ""
        percent_change = ""
        print("Processing costs for " + str(key) + " with current cost " + str(value))

        if key in team_prev_costs:
            print("Previous costs found for " + str(key) + " of " + str(team_prev_costs[key]))
            prev_cost = team_prev_costs[key]
            percent_change = (value - prev_cost) / prev_cost * 100
            percent_change = "{0:.0f}".format(percent_change)
            print("Percentage change for " + str(key) + " is " + str(percent_change))
        else:
            print("No previous costs found for team " + str(key))
            percent_change = 0

        table = table + "<tr><td style='padding: 10px;'>" + str(key) + "</td><td style='padding: 10px;'>" + team_period[key] + "</td><td style='padding: 10px;'>$" + str(value) + "</td><td style='padding: 10px;'>$" + str(prev_cost) + "</td><td style='padding: 10px;'>" + str(percent_change) + "%</td></tr>"
        if debug:
            print("%s: %s" % (key, value))

    # what is the total cost for all teams?
    for team in team_costs:
        total_cost = total_cost + team_costs[team]
        if team in team_prev_costs:
            total_prev_cost = total_prev_cost + team_prev_costs[team]

    table = table + "<tr><td style='padding: 10px;'>" + "" + "</td><td style='padding: 10px;'>" + "" + "</td><td style='padding: 10px;border-bottom:1pt solid black;border-top:1pt solid black;'><strong>$" + str(total_cost) + "<td style='padding: 10px;border-bottom:1pt solid black;border-top:1pt solid black;'><strong>$" + str(total_prev_cost) +  "</strong></td></tr>"
    table = table + "</table>"

    return table


# produce an html file and return the filename
def output_results(folder, config_map, debug):
    # Get the SMTP config
    smtp_server = config_map['global']['smtp']['server']
    smtp_tls = config_map['global']['smtp']['tls']
    smtp_port = config_map['global']['smtp']['port']
    smtp_user = config_map['global']['smtp']['user']
    smtp_pass = config_map['global']['smtp']['password']
    smtp_to = config_map['global']['smtp']['to_addr']
    smtp_from = config_map['global']['smtp']['from_addr']
    smtp_cc = config_map['global']['smtp']['cc_addrs']
    email_template_file = config_map['global']['smtp']['template']
    email_subject = "Azure Team Cost Summary for all teams"
    values = {}
    values['reportGenerationDate'] = datetime.datetime.now().strftime("%Y-%m-%d")
    values['teamCosts'] = str(get_team_totals(config_map, folder, debug))
    template = mail.EmailTemplate(template_name=email_template_file, values=values)
    server = mail.MailServer(server_name=smtp_server, username=smtp_user, password=smtp_pass, port=smtp_port, require_starttls=smtp_tls)
    msg = mail.MailMessage(from_email=smtp_from, to_emails=[smtp_to], cc_emails=smtp_cc,subject=email_subject,template=template)
    print("Sending email to %s" % smtp_to)
    mail.send(mail_msg=msg, mail_server=server)
