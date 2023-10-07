# set default value as -1
registerd_users = {}
# contest_1 = {}
# contest_2 = {}
contest_1 = {"918446277653": {"action": 1, "points": 0}, "919146524272": {"action": 1, "points": 0}}
contest_2 = {"918446277653": {"action": 1, "points": 0}, "919146524272": {"action": 1, "points": 0}}


action_seq = {
        0: "Profile photo received successfully ",
        1: "Profile photo matched with submission ",
        2: "Profile photo is different from your submission ",
        9999: "We have already received your submission for this contest."
    }


def my_points(user_no, text_msg=None, winner_flag=False):
    if "1" in text_msg or "2" in text_msg:
        contest = check_contest(text_msg)
        print(f"cntest{contest}")
        points = contest[user_no]["points"]
        print(f"points{points}")
        if winner_flag:
           return points 
    else:
        points_1 = contest_1[user_no]["points"] 
        points_2 = contest_2[user_no]["points"]
        points = f" contest_1: {points_1} and contest_2: {points_2}"
        if winner_flag:
            return points_1 + points_2
    return f"Your points earned for the day are {points}"


def check_contest(contest_name):
    if "1" in contest_name:
        return contest_1
    elif "2" in contest_name:
        return contest_2
    else:
        return "No other activities are currently live "

#  This method to be used for images responses only
def check_action_sequence(user_no, contest_name, user_name):
    # Profile set message sent
    if user_no not in registerd_users.keys():
        registerd_users[user_no] = user_name
        return action_seq[0]
    # Contest messages sent
    contest = check_contest(contest_name)
    out = contest[user_no]
    # if out:
    #     return action_seq[9999]
    # else:
    #     contest.append({user_no: {"action": 1, "points": 0}})
    res = out["action"]
    if "matched" in action_seq[res]:
        out["points"] += 10
    out["action"] += 1 if (out["action"]+1<3) else 9999
    react = action_seq[res] + f" for contest {contest_name}"
    return react


def get_winner(contest_name, winner_flag = True):
    contest = check_contest(contest_name)
    base_points = 0
    total_points = 0
    for user_no in registerd_users.keys():
        print(f"Inside{user_no}")
        total_points = my_points(user_no, contest_name, winner_flag)
        print(f"Inside{total_points}")
        if base_points <= total_points:
            print(f"Inner inside{total_points}")
            base_points = total_points
            winner = registerd_users[user_no]
    if base_points == 0:
        return "No winner for the day."
    return f"Winner for today's challenge is {winner}"

def get_user_dict(in_dict):
    new_d = {}
    for key, sub in in_dict.items():
        for temp_key, value in sub.items():
            if key in registerd_users.keys() and temp_key == "points":
                new_d[registerd_users[key]] = value 
    return new_d

def merge_dict(in_1, in_2):
    new_d = {}
    dict_1 = get_user_dict(in_1)
    dict_2 = get_user_dict(in_2)
    for user_no, user_name in registerd_users.items():
        print(f"+++++++++++++++++++{dict_1.keys()}++++++++++++++++++++")
        if user_name in dict_1.keys() and user_name in dict_2.keys():
            new_d[user_name] = dict_1[user_name] + dict_2[user_name]
        elif user_name in dict_1.keys():
            new_d[user_name] = dict_1[user_name]
        elif user_name in dict_2.keys():
            new_d[user_name] = dict_2[user_name]
    return new_d


def leader_board(contest_name):
    contest = check_contest(contest_name)
    print("=================== output calculate ====================================")
    if "1" in contest_name or "2" in contest_name:
        points_dict = get_user_dict(contest)
    else:
        points_dict = merge_dict(contest_1, contest_2)
    temp = sorted(points_dict.items(), key=lambda x:x[1], reverse=True)
    out = dict(temp)
    return send_leader_board(out)


def send_leader_board(out):
    output = "No: User Name: Points \n"
    j = 1
    for key, value in out.items():
        output = output + f"{j}: {key}: {value}" + "\n"
        j += 1
    print(output)
    return f"*Leader Board* \n\n {output}"
