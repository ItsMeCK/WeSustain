import requests
import request_id
from flask import Flask, jsonify, request, render_template, make_response
from request_id import RequestIdMiddleware
import json

registerd_users = {}
contest_commute = {}
contest_office = {}
contest_food = {}
new_contest_2 = {}
contest_names = ["Commute Sustainably", "Green office , Green world", "Food choices matter"]
contest_compare = ["commute", "office", "food"]

contest_1 = {"918446277653": {"action": 1, "points": 0}, "919146524272": {"action": 1, "points": 0}}
contest_2 = {"918446277653": {"action": 1, "points": 0}, "919146524272": {"action": 1, "points": 0}}


action_seq = {
        0: "Profile photo received successfully ",
        1: "Profile photo matched with submission ",
        2: "Profile photo is different from your submission ",
        9999: "We have already received your submission for this contest."
    }


def my_points(user_no, text_msg=None, winner_flag=False):
    if text_msg in contest_names:
        contest, contest_name = check_contest_new(text_msg)
        points = contest[user_no]["points"]
        if winner_flag:
           return points 
    else:
        points = 0
        out = ""
        for con in contest_names:
            contest, contest_name = check_contest_new(con)
            if user_no in contest.keys():
                points = points + contest[user_no]["points"] 
            out = out + f"{contest_name}: {points}"
        if winner_flag:
            return points
    return f"Your points earned for the day are {out}"


def get_winner(contest_name, winner_flag = True):
    contest, contest_name = check_contest_new(contest_name)
    if contest is None:
        contest_keys = list(contest_commute.keys()) + list(contest_food.keys()) + list(contest_office.keys())
        registerd_users = list(set(contest_keys))
    else:
        registerd_users = contest.keys()
    base_points = 0
    total_points = 0
    for user_no in registerd_users:
        print(f"Inside{user_no}")
        total_points = my_points(user_no, contest_name, winner_flag)
        print(f"Inside{total_points}")
        if base_points <= total_points:
            print(f"Inner inside{total_points}")
            base_points = total_points
            winner_no = user_no
    if base_points == 0:
        return "No winner for the day."
    if winner_no in contest_commute.keys():
        winner = contest_commute[winner_no]['name']
    elif winner_no in contest_food.keys():
        winner = contest_food[winner_no]['name']
    elif winner_no in contest_office.keys():
        winner = contest_office[winner_no]['name']
    else:
        return f"No valid winner for the contest"
    return f"Winner for today's challenge is {winner}"


def get_user_dict_new(in_dict):
    new_d = {}
    for key, sub in in_dict.items():
        for temp_key, value in sub.items():
            new_d[in_dict[key]["name"]] = in_dict[key]["points"] 
    return new_d

# Not working now
def merge_dict():
    new_d = {}
    registerd_users = []
    dict_1 = get_user_dict_new(contest_commute)
    dict_2 = get_user_dict_new(contest_food)
    dict_3 = get_user_dict_new(contest_office)
    registerd_users = list(dict_1.keys()) + list(dict_2.keys()) + list(dict_3.keys())
    registerd_users = list(set(registerd_users))
    for user_name in registerd_users:
        if user_name in dict_1.keys() and user_name in dict_2.keys() and user_name in dict_3.keys():
            new_d[user_name] = dict_1[user_name] + dict_2[user_name] + dict_3[user_name]
        elif user_name in dict_1.keys() and user_name in dict_2.keys():
            new_d[user_name] = dict_1[user_name] + dict_2[user_name]
        elif user_name in dict_1.keys() and user_name in dict_3.keys():
            new_d[user_name] = dict_1[user_name] + dict_3[user_name]
        elif user_name in dict_2.keys() and user_name in dict_3.keys():
            new_d[user_name] = dict_2[user_name] + dict_3[user_name]
        elif user_name in dict_1.keys():
            new_d[user_name] = dict_1[user_name]
        elif user_name in dict_2.keys():
            new_d[user_name] = dict_2[user_name]
        elif user_name in dict_3.keys():
            new_d[user_name] = dict_3[user_name]
    return new_d


def leader_board(text_msg):
    contest, contest_name = check_contest_new(text_msg)
    if contest is None:
        points_dict = merge_dict()
        contest_name = " for all contests"
    elif contest_name in contest_names:
        points_dict = get_user_dict_new(contest)
    else:
        return f"Please mention correct entry. You have provided: {text_msg}"
    temp = sorted(points_dict.items(), key=lambda x:x[1], reverse=True)
    out = dict(temp)
    return send_leader_board(out, contest_name)


def send_leader_board(out, contest_name):
    output = "No: User Name: Points \n"
    j = 1
    for key, value in out.items():
        output = output + f"{j}: {key}: {value}" + "\n"
        j += 1
    print(output)
    return f"*Leader Board for {contest_name}* \n\n {output}"


def check_contest_new(text_msg):
    if "commute" in text_msg.lower():
        contest_dict = contest_commute
        contest_name = contest_names[0]
    elif "office" in text_msg.lower():
        contest_dict = contest_office
        contest_name = contest_names[1]
    elif "food" in text_msg.lower():
        contest_dict = contest_food
        contest_name = contest_names[2]
    else:
        return None, text_msg
    return contest_dict, contest_name

def check_action_sequence_new(user_no, text_msg, user_name):
    # Contest messages sent
    contest, contest_name = check_contest_new(text_msg)
    out = contest[user_no]
    res = out["action"]
    if "matched" in action_seq[res]:
        out["points"] += 100
    out["action"] += 1 if (out["action"]+1<3) else 9999
    react = action_seq[res] + f" for contest {contest_name}"
    return react

def update_contest_registrations(from_num, text_msg, name):
    contest, contest_name = check_contest_new(text_msg)
    print(contest_name)
    contest[from_num] = {"action": 1, "points": 0, "name": name}
    return f"Entry received for contest {contest_name}"

def broadcast_message(message, broadcast_ids):
    
    for number in broadcast_ids:
        token = 'EAAtTz8pRH9cBO5BWGnNHQLWFOOjZBotYSgCO57UcId03HyOBA30Qjn9bVlZAPLpRJTuwdZBhUoeoDkFToqOirZBILwlZA78NTAiNsZAvRbxqjJCYdcVEJGuQbPwklWil88Lsg2tiZBdFS2qbqRWdLPgkN0QBgL70Hp9OLchP7OVJ2JxIyK5dkgZCkvMTKZCLzmoimgKcQHJkEByPzVO77NHiGBpeFjIIZD'
        req_obj = requests.post(f'https://graph.facebook.com/v12.0/{133722459827672}/messages?access_token={token}', data ={
            "access_token": token,
            "messaging_product": "whatsapp",
            "to": f"{number}",
            "text": json.dumps({"body": f"{message}"})
        })

def broadcast_cotext_details():
    message = f"""🌿 Good morning, WeSustain Warriors! 🌍
Today's challenge is all about turning your office routine into a sustainability powerhouse! Are you ready to make a positive impact while at work? Say 'YES' to join the challenge!
🌟 Challenge Details:
Contest 1 - 
🏢 Office Hours - 7 AM to 11 AM: Business Commute
🚗 Commute Sustainably: Choose eco-friendly transport like carpooling, biking, or public transit. Reduce emissions and lead the way to a greener commute! Share a pic of your eco-commute! 🚴‍♂️🚆

Contest 2 - 
🍽️ Office Hours - 9 PM to 11 PM: Sustainable Food Habits
🍏 Food Choices Matter: Show us your sustainable food habits. Are you eating local, reducing packaging, or minimizing waste? Snap a pic of your sustainable meal and share your tips! 🍴♻️

Contest 3 - 
🏢 Office Hours - 4 PM to 10 PM: Eco-Conscious Work Practices
💼 Green Office, Green World: Demonstrate how you save energy, reduce paper usage, or adopt other eco-conscious habits at the office. A pic of your eco-efforts will do wonders! 📸🌿

🌍 Grading System:
Your actions today could save between 100-500 CO2 emissions! The more sustainable your choices, the higher your score. Your daily decisions add up to a greener world! ♻️🌍
🏆 Winner Announcement:
At 11:59 PM, we'll crown our sustainability champion! Will it be you? Stay tuned to find out! 🏆
Ready to transform your office day into a sustainability masterpiece? Reply 'YES,' take action, and inspire others to join the cause! Let's make today count for a more sustainable world! 💚🌎
#SustainabilityChallenge #GreenOffice #WeSustain🌿
 
Click a photo while travelling and upload with caption - <Contest Name>"""
    broadcast_message(message, list(set(list(contest_commute.keys()) + list(contest_office.keys()) + list(contest_food.keys()))))
    return "Contest details sent"
