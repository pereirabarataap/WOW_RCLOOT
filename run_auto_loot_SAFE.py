import os
import json
import time
import github
import joblib
import requests
import numpy as np
import pandas as pd
import seaborn as sb
import networkx as nx
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from tqdm.notebook import tqdm
from copy import deepcopy as copy
from matplotlib import pyplot as plt

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

plt.style.use("dark_background")

init_day=16
init_month=10
init_year=2023

benching_dict = {
    "Almightyryu":     ["2023-11-22"],
    "Blixtfisk":       ["2023-11-08", "2023-11-13"],
    "Checo":           ["2023-10-16", "2023-10-18"],
    "Egret":           ["2023-11-06", "2023-11-08", "2023-11-13", "2023-11-15", "2023-11-22"],
    "Galima":          ["2023-11-06", "2023-11-08"],
    "Gizbo Beebo":     ["2023-11-08", "2023-11-15", "2023-11-20"],
    "Glamros":         ["2023-10-30"],
    "Hexblade":        ["2023-11-08"],
    "Kazøn":           ["2023-11-06", "2023-11-22", "2023-11-29"],
    "Minox":           ["2023-10-30"],
    "Mõss":            ["2023-11-29"],
    "Paladinhó":       ["2023-11-08"],
    "Sesos":           ["2023-10-18", "2023-10-23", "2023-11-06"],
    "Uilskuiken":      ["2023-11-13", "2023-11-22"],
    "Xaverian":        ["2023-11-15", "2023-11-20", "2023-11-22", "2023-11-29", "2023-12-11"],
    "Vafanior Vafina": ["2023-11-15"],
    "Zaylz":           ["2023-11-06"],
    "Zwack":           ["2023-10-30", "2023-11-06"],
}

class_colors =  {
    "Mage": "#3FC7EB",
    "Druid": "#FF7C0A",
    "Rogue": "#FFF468",
    "Hunter": "#AAD372",
    "Priest": "#F3F3F3",
    "Shaman": "#0070DD",
    "Warlock": "#8788EE",
    "Warrior": "#C69B6D",
    "Paladin": "#F48CBA",
    "Deathknight": "#C41E3A",
}

class_icons = {
    "Mage": "https://static.wikia.nocookie.net/wowpedia/images/a/ae/Inv_staff_13.png",
    "Priest": "https://static.wikia.nocookie.net/wowpedia/images/3/3c/Inv_staff_30.png",
    "Warrior": "https://static.wikia.nocookie.net/wowpedia/images/8/83/Inv_sword_27.png",
    "Hunter": "https://static.wikia.nocookie.net/wowpedia/images/e/e7/Inv_weapon_bow_07.png",
    "Rogue": "https://static.wikia.nocookie.net/wowpedia/images/8/8e/Inv_throwingknife_04.png",
    "Paladin": "https://static.wikia.nocookie.net/wowpedia/images/6/6c/Ability_thunderbolt.png",
    "Warlock": "https://static.wikia.nocookie.net/wowpedia/images/d/d2/Spell_nature_drowsy.png",
    "Druid": "https://static.wikia.nocookie.net/wowpedia/images/c/c8/Inv_misc_monsterclaw_04.png",
    "Shaman": "https://static.wikia.nocookie.net/wowpedia/images/d/d9/Inv_jewelry_talisman_04.png",
    "Deathknight": "https://static.wikia.nocookie.net/wowpedia/images/f/fd/Spell_deathknight_classicon.png",
}

mrt_path = "C:/Program Files (x86)/World of Warcraft/_classic_" + \
           "/WTF/Account/APBARATA/SavedVariables/MRT.lua"

rc_path = "C:/Program Files (x86)/World of Warcraft/_classic_" + \
          "/WTF/Account/APBARATA/SavedVariables/RCLootCouncil_Classic.lua"

logs_folder = "C:/Program Files (x86)/World of Warcraft/_classic_/Logs"

token = "YOUR_GIT_TOKEN_HERE"

def hex_to_rgba(s):
    h = s[1:]
    return np.array(
        (list((int(h[i:i+2], 16)/255) for i in (0, 2, 4)) + [1])
    )

def get_rc_loot_df(path_to_lua="rc_path", save=True):

    with open(path_to_lua, "r", encoding="utf-8-sig") as op:
        lines = op.readlines()

    response_id_old = {
        "1": "BiS",
        "2": "Major", 
        "3": "Minor",
        "4": "OS",
    }

    response_id_new = {
        "1": "BiS",
        "2": "R-BiS",
        "3": "Major", 
        "4": "Minor",
        "5": "OS",
    }

    kois = [
        '"time"', 
        '"date"',
        '"class"', 
        '"lootWon"', 
        '"instance"',
        '"response"',
        '"responseID"',
    ]
    rc_db_flag = 0
    row_counter = 0
    proto_loot_dict = {}
    for line in lines:
        if "RCLootCouncilLootDB = {" in line:
            rc_db_flag = 1

        if rc_db_flag:
            if ("-Earthshaker" in line) and ('["owner"]' not in line):
                player = line.split("-Earthshaker")[0].split('["')[1]

            for koi in kois:

                if koi in line:
                    if koi!='"responseID"':
                        voi = line.split("=")[1].strip().rstrip()[1:-2]
                        voi = voi.lower().capitalize() if "class" in koi else voi

                    else:
                        voi = line.split("=")[1].strip().rstrip()[0]
                        # if voi in response_id.keys():
                        #     voi = response_id[voi]

                    if row_counter not in list(proto_loot_dict.keys()):
                        proto_loot_dict[row_counter] = {}

                    if "Hitem:" in voi:
                        sub_voi_1 = voi.split(":")[1].split(":")[0]
                        sub_voi_2 = voi.split("[")[1].split("]")[0]
                        proto_loot_dict[row_counter]["item_id"] = sub_voi_1
                        proto_loot_dict[row_counter]["item_name"] = sub_voi_2

                    else:
                        proto_loot_dict[row_counter][koi[1:-1]] = voi

            if "}, -- [" in line:
                proto_loot_dict[row_counter]["player"] = player
                row_counter += 1
                vois = []


    rc_loot_df = pd.DataFrame.from_dict(proto_loot_dict).T.copy()
    rc_loot_df = rc_loot_df.loc[~(rc_loot_df["response"].isin(['Pass', 'Banking', 'Disenchant']))].copy()
    rc_loot_df["date"] = rc_loot_df["date"].apply(lambda x: pd.Timestamp(
        day=int(x[:2]), month=int(x[3:5]), year=int("20"+x[-2:])
    ))
    old_new_response_trans_time = rc_loot_df.loc[rc_loot_df.responseID=="5"].date.min()

    # fix
    rc_loot_df.loc[
        (rc_loot_df.player=="Minox") &
        (rc_loot_df.item_name=="Overload Legwraps"),
        "responseID"
    ] = "3" # minor in the old response dict
    rc_loot_df.loc[
        (rc_loot_df.player=="Kaylz") &
        (rc_loot_df.item_name=="Crown of Luminescence"),
        "responseID"
    ] = "1"
    
    # keeping only awards of items by response_id 1 ~ 4
    rc_loot_df = rc_loot_df.loc[rc_loot_df.responseID.isin(["1", "2", "3", "4"])].reset_index(drop=True)
    # rc_loot_df["response"] = rc_loot_df.apply(
    #     lambda row: 
    #         response_id_old[row["responseID"]] if (
    #             row["date"]<old_new_response_trans_time
    #         ) else (
    #             response_id_new[row["responseID"]]
    #         ),
    #     axis=1
    # )
    
    rc_loot_df["response"] = rc_loot_df.apply(
        lambda row: 
            response_id_old[row["responseID"]],
        axis=1
    )
    
    rc_loot_df = rc_loot_df.drop(columns=["responseID"]).copy()
    rc_loot_df["class_icon"] = rc_loot_df["class"].apply(lambda claxx: class_icons[claxx])
    rc_loot_df["class_color_hex"] = rc_loot_df["class"].apply(lambda claxx: class_colors[claxx])
    rc_loot_df["class_color_rgba"] = rc_loot_df["class"].apply(lambda claxx: hex_to_rgba(class_colors[claxx]))
    rc_loot_df["class_order"] = rc_loot_df["class"].apply(lambda claxx: sorted(rc_loot_df["class"].unique()).index(claxx))
    # rc_loot_df["date"] = pd.to_datetime(rc_loot_df["date"] + " " +  rc_loot_df["time"], dayfirst=True); rc_loot_df.drop(columns=["time"], inplace=True)
    
    #--------------#
    # MANUAL FIXES #
    #--------------#
    
    misc_ids = [
        "50274", # Shadowfrost Shard
        "43346", # Large Satchel of Spoils
        "43345", # Dragon Hide Bag
        "43954", # Reins of the Twilight Drake
        "46348", # Formula: Enchant Weapon - Blood Draining
        "46110", # Alchemist's Cache
    ]
    rc_loot_df.loc[rc_loot_df["item_id"].isin(misc_ids), "response"] = "Misc"
    
    # Heroic Key to Tenebros 
    fix_row = copy(rc_loot_df.loc[rc_loot_df["player"]=="Tenebros"].iloc[0])
    fix_row["date"] = pd.to_datetime("12-10-2022 23:00:00", dayfirst=True)
    fix_row["item_name"] = "Heroic Key to the Focusing Iris"
    fix_row["instance"] = "Naxxramas-25 Player"
    fix_row["item_id"] = "44577"
    fix_row["response"] = "BiS"
    rc_loot_df = pd.concat(
        (rc_loot_df, pd.DataFrame(fix_row).T),
        axis=0
    )
    
    # Heroic Key to Fideous 
    fix_row = copy(rc_loot_df.loc[rc_loot_df["player"]=="Fideous"].iloc[0])
    fix_row["date"] = pd.to_datetime("05-10-2022 23:00:00", dayfirst=True)
    fix_row["item_name"] = "Heroic Key to the Focusing Iris"
    fix_row["instance"] = "Naxxramas-25 Player"
    fix_row["item_id"] = "44577"
    fix_row["response"] = "BiS"
    rc_loot_df = pd.concat(
        (rc_loot_df, pd.DataFrame(fix_row).T),
        axis=0
    )
    
    rc_loot_df.sort_values(by="date", inplace=True)
    if save:
        joblib.dump(rc_loot_df, os.getcwd() + "/rc_loot_df.pkl")
    
    init_date = pd.Timestamp(year=init_year, month=init_month, day=init_day)
    rc_loot_df = rc_loot_df.loc[
        (rc_loot_df.date >= init_date).values.astype(bool)
    ].reset_index(drop=True)
    
    # merging Vaf's main and alt
    main_alt_loc = rc_loot_df.player.isin(["Vafanior", "Vafina"])
    rc_loot_df.loc[main_alt_loc, "player"] = "Vafanior Vafina"
    rc_loot_df.loc[
        main_alt_loc & (rc_loot_df["class"]=="Druid"),
        "response"
    ] = "OS"
    class_color_hex = rc_loot_df.loc[
        main_alt_loc & (rc_loot_df["class"]=="Warrior"),
        "class_color_hex"
    ].values[0]
    class_color_rgba = rc_loot_df.loc[
        main_alt_loc & (rc_loot_df["class"]=="Warrior"),
        "class_color_rgba"
    ].values[0]
    class_order = rc_loot_df.loc[
        main_alt_loc & (rc_loot_df["class"]=="Warrior"),
        "class_order"
    ].values[0]
    rc_loot_df.loc[main_alt_loc, "class"] = "Warrior"
    rc_loot_df.loc[main_alt_loc, "class_order"] = class_order
    rc_loot_df.loc[main_alt_loc, "class_color_hex"] = class_color_hex
    rc_loot_df.loc[main_alt_loc, "class_color_rgba"] = rc_loot_df.loc[main_alt_loc, "class_color_hex"].apply(
        lambda hexa:
            hex_to_rgba(hexa)
    )
    
    # merging Gizbo's main and alt
    main_alt_loc = rc_loot_df.player.isin(["Gizbo", "Beebo"])
    rc_loot_df.loc[main_alt_loc, "player"] = "Gizbo Beebo"
    rc_loot_df.loc[
        main_alt_loc & (rc_loot_df["class"]=="Warlock"),
        "response"
    ] = "OS"
    class_color_hex = rc_loot_df.loc[
        main_alt_loc & (rc_loot_df["class"]=="Mage"),
        "class_color_hex"
    ].values[0]
    class_color_rgba = rc_loot_df.loc[
        main_alt_loc & (rc_loot_df["class"]=="Mage"),
        "class_color_rgba"
    ].values[0]
    class_order = rc_loot_df.loc[
        main_alt_loc & (rc_loot_df["class"]=="Mage"),
        "class_order"
    ].values[0]
    rc_loot_df.loc[main_alt_loc, "class"] = "Mage"
    rc_loot_df.loc[main_alt_loc, "class_order"] = class_order
    rc_loot_df.loc[main_alt_loc, "class_color_hex"] = class_color_hex
    rc_loot_df.loc[main_alt_loc, "class_color_rgba"] = rc_loot_df.loc[main_alt_loc, "class_color_hex"].apply(
        lambda hexa:
            hex_to_rgba(hexa)
    )
    
    # removing loot from Ulduar that is not BiS
    drop_loc = (
        rc_loot_df.instance.str.contains("Ulduar") &
        ~(rc_loot_df.response.str.contains("BiS"))
    )
    rc_loot_df = rc_loot_df.loc[~drop_loc].reset_index(drop=True)
    # removing plans/patterns from list
    rc_loot_df = rc_loot_df.loc[
        ~(rc_loot_df.item_name.str.contains(":"))
    ].reset_index(drop=True)
    
    # adding manual rows
    
    
    manual_rows = [
        [
            "Shaman", #
            "21:15:00", #
            "Icecrown Citadel-25 Player",
            "Major", #
            "52026", #
            "Protector's Mark of Sanctification", #
            pd.to_datetime("2023-10-23"), #
            "Tenebruv",
            rc_loot_df.loc[rc_loot_df["class"]=="Shaman", "class_icon"].values[0],
            rc_loot_df.loc[rc_loot_df["class"]=="Shaman", "class_color_hex"].values[0],
            rc_loot_df.loc[rc_loot_df["class"]=="Shaman", "class_color_rgba"].values[0],
            rc_loot_df.loc[rc_loot_df["class"]=="Shaman", "class_order"].values[0]
        ],
        
    ]
    for new_row in manual_rows:
        rc_loot_df = pd.concat([rc_loot_df, pd.DataFrame([new_row], columns=rc_loot_df.columns)], axis=0, ignore_index=True)
        
    return rc_loot_df

def get_html_loot_df(
    rc_loot_df="get_rc_loot_df()", 
    save=True, 
    instances=["Icecrown"], 
    init_day=init_day, init_month=init_month, init_year=init_year):
   
    rc_loot_df = copy(get_rc_loot_df(rc_path, save=True))
    rc_loot_df = rc_loot_df.loc[
        rc_loot_df["instance"].str.contains("|".join(instances))
    ].reset_index(drop=True)

    # removing duplicate entries
#     sub_dfs = []
#     for player, sub_df in rc_loot_df.groupby(by=["player", "item_id", "date"]):
#         sub_df_idx = sub_df.index.copy()
#         rows_to_keep = np.repeat(True, len(sub_df_idx))
#         if len(sub_df)>1:
#             times = pd.to_datetime(sub_df.time).values
#             same_loot_indxs = []
#             for i in range(len(times)-1):
#                 time_i = times[i]
#                 for j in range(i+1, len(times)):
#                     time_j = times[j]
#                     time_delta_hours = abs(float(time_j - time_i) / 1e9 / 3600)
#                     if (time_delta_hours == 1) or (time_delta_hours == 0):
#                         same_loot_indxs.append((i,j))

#             # if we have duplicate items
#             if len(same_loot_indxs) > 0:
#                 G = nx.Graph()
#                 G.add_edges_from(same_loot_indxs)
#                 for duplicate_rows in nx.components.connected_components(G):
#                     duplicate_idxs = sub_df_idx[list(duplicate_rows)]
#                     swap_to_false_loc = sub_df_idx.isin(duplicate_idxs[1:])
#                     rows_to_keep[swap_to_false_loc] = False

#         sub_df = sub_df.loc[rows_to_keep]
#         sub_dfs.append(sub_df)
    
#     rc_loot_df = pd.concat(sub_dfs, ignore_index=True).reset_index(drop=True)

    columns = [
        "Class_text", "Class", "Player",
        "#BiS", "#Major", "#Minor", "#OS", "#Misc",
        "BiS", "Major", "Minor", "OS", "Misc"
    ]
    n_counts = 5
    html_loot_df = pd.DataFrame(columns=columns)
    players_groups = rc_loot_df.groupby(by="player")
    loc_counter = 0
    for player, sub_df in players_groups:

        item_counts = [0] * n_counts
        item_links = [""] * n_counts
        player_class = sub_df["class"].unique()[0]
        class_icon = sub_df["class_icon"].unique()[0]
        class_order = sub_df["class_order"].unique()[0]
        ordered_responses = columns[-n_counts:]

        row_data = [
            player_class if "Death" not in player_class else player_class + " dk DK",
            "<p style='position:relative;color:transparent;'>"+ str(class_order) + \
            "<img style='position:absolute;top:0;left:0;' src=" + class_icon + \
            " alt='"+ player_class + "' width='32' height='32'></img></p>",
            player
        ]
        if len(instances)==1:
            for i in range(len(item_counts)):
                response_i = ordered_responses[i]
                item_counts[i] = sub_df["response"].value_counts()[response_i] \
                                 if response_i in sub_df["response"].value_counts().keys() else 0

                if item_counts[i] == 1:        
                    item_id, item_name = sub_df.loc[sub_df["response"]==response_i, ["item_id", "item_name"]].values.ravel()
                    item_links[i] = "<a href='https://www.wowhead.com/wotlk/item="+item_id+"'>"+item_name+"_</a>"

                elif item_counts[i] > 1:
                    item_links[i] = "</br>".join(
                        [
                            "<a href='https://www.wowhead.com/wotlk/item="+item_id+"'>"+item_name+"_</a>" \
                            for item_id, item_name in sub_df.loc[sub_df["response"]==response_i, ["item_id", "item_name"]].values
                        ]
                    )
                
                
        else:
            for i in range(len(item_counts)):
                response_i = ordered_responses[i]

                if response_i=="Ulduar-BiS":
                    uldu_sub_df = sub_df.loc[sub_df.instance.str.contains("Ulduar")].copy()
                    item_counts[i] = uldu_sub_df["response"].value_counts()["BiS"] \
                                     if "BiS" in uldu_sub_df["response"].value_counts().keys() else 0

                    if item_counts[i] == 1:        
                        item_id, item_name = uldu_sub_df.loc[uldu_sub_df["response"]=="BiS", ["item_id", "item_name"]].values.ravel()
                        item_links[i] = "<a href='https://www.wowhead.com/wotlk/item="+item_id+"'>"+item_name+"_</a>"

                    elif item_counts[i] > 1:
                        item_links[i] = "</br>".join(
                            [
                                "<a href='https://www.wowhead.com/wotlk/item="+item_id+"'>"+item_name+"_</a>" \
                                for item_id, item_name in uldu_sub_df.loc[uldu_sub_df["response"]=="BiS", ["item_id", "item_name"]].values
                            ]
                        )

                else:
                    instance_sub_df = sub_df.loc[~(sub_df.instance.str.contains("Ulduar"))].copy()
                    item_counts[i] = instance_sub_df["response"].value_counts()[response_i] \
                                     if response_i in instance_sub_df["response"].value_counts().keys() else 0

                    if item_counts[i] == 1:        
                        item_id, item_name = instance_sub_df.loc[instance_sub_df["response"]==response_i, ["item_id", "item_name"]].values.ravel()
                        item_links[i] = "<a href='https://www.wowhead.com/wotlk/item="+item_id+"'>"+item_name+"_</a>"

                    elif item_counts[i] > 1:
                        item_links[i] = "</br>".join(
                            [
                                "<a href='https://www.wowhead.com/wotlk/item="+item_id+"'>"+item_name+"_</a>" \
                                for item_id, item_name in instance_sub_df.loc[instance_sub_df["response"]==response_i, ["item_id", "item_name"]].values
                            ]
                        )

        row_data = row_data + item_counts + item_links
        html_loot_df.loc[loc_counter, columns] = row_data
        loc_counter += 1

    html_loot_df.sort_values(by=["#BiS", "#Major", "#Minor", "#OS", "#Misc"], ascending=False, inplace=True)
    html_loot_df.reset_index(drop=True, inplace=True)
    
    if save:
        joblib.dump(html_loot_df, os.getcwd() +"/html_loot_df.pkl")
        
    return html_loot_df

def get_attendance_df(
    path_to_lua="rc_path", 
    logs_folder="logs_folder", 
    init_day=init_day, 
    init_month=init_month, 
    init_year=init_year,
    benching_dict=benching_dict):

    init_date = datetime(year=init_year, month=init_month, day=init_day)
    all_saved_players = get_rc_loot_df(path_to_lua)["player"].unique()
    main_alt_names = [name for name in all_saved_players if " " in name]
    all_saved_players = all_saved_players.tolist()
    [all_saved_players.remove(main_alt_name) for main_alt_name in main_alt_names];
    [all_saved_players.append(name) for main_alt_name in main_alt_names for name in main_alt_name.split(" ")];

    logs = [item for item in os.listdir(logs_folder) if "WoWCombatLog" in item]
    combat_logs = [log for log in logs if (
        datetime.strptime(
            log[13:15] + "-" + log[15:17] + "-20" + log[17:19], "%m-%d-%Y"
        ).strftime("%A") in ["Monday", "Wednesday"]
    )]
    phase_logs = []
    for combat_log in combat_logs:
        date = combat_log.split("-")[1].split("_")[0]
        day = int(date[2:4])
        month = int(date[:2])
        year = int("20"+ date[-2:])

        raid_date = datetime(year=year, month=month, day=day)

        # first ulduar raid 23.01.2023
        if  raid_date >= init_date:
            # Monday / Wednesday 25man raid days
            if raid_date.weekday() in [0,2]:
                phase_logs.append(combat_log)

    dates = None
    raid_players = None
    for phase_log in phase_logs:
        date = phase_log.split("-")[1].split("_")[0]
        day = int(date[2:4])
        month = int(date[:2])
        year = int("20"+ date[-2:])
        players = []
        with open(logs_folder + "/" + phase_log, "r", encoding="utf-8-sig") as op:
            in_instance = 0
            for line in op.readlines():
                if "ZONE_CHANGE" in line:
                    if ',631,"Icecrown Citadel"' in line:
                        in_instance = 1
                    else:
                        in_instance = 0

                elif in_instance:
                    if line.find("-Earthshaker") >= 1:
                        players.append(line.split("-Earthshaker")[0].split('"')[-1])

        unique_players = np.intersect1d(
            np.unique(players),
            all_saved_players
        ).reshape(-1, 1)

        if raid_players is None:
            raid_players = unique_players

        else:
            raid_players = np.concatenate(
                (raid_players, unique_players),
                axis=0
            )

        if dates is None:
            dates = np.repeat(
                pd.to_datetime(datetime(year=year,month=month,day=day)), len(unique_players)
            ).reshape(-1,1)
        else:
            dates = np.concatenate(
                (dates, np.repeat(
                    pd.to_datetime(datetime(year=year,month=month,day=day)), len(unique_players)
                ).reshape(-1,1)),
                axis=0
            )

    attendance_df = pd.DataFrame(np.concatenate((dates, raid_players), axis=1))

    for main_alt_name in main_alt_names:
        loc = attendance_df[1].isin(main_alt_name.split(" "))
        attendance_df.loc[loc, 1] = main_alt_name

    attendance_df = attendance_df.drop_duplicates().reset_index(drop=True)

    attend_data = []
    for player in attendance_df[1].unique():
        player_row = []
        for date in attendance_df[0].unique():
            if sum((attendance_df[0]==date) & (attendance_df[1]==player)):
                player_row.append(1)
            else:
                player_row.append(0)

        attend_data.append(player_row)

    attendance_df = pd.DataFrame(
        index=attendance_df[1].unique(),
        columns=pd.Series(attendance_df[0].unique()).astype(str).str[:10],
        data=attend_data
    )

    attendance_df["#Bench"] = 0

    # awarding attendance
    for player in benching_dict:
        if player in attendance_df.index:
            for date in benching_dict[player]:
                attendance_df.loc[player, date] = 1
                attendance_df.loc[player, "#Bench"] = attendance_df.loc[player, "#Bench"] + 1

    attendance_df["#Raids"] = attendance_df.T.iloc[:-1].sum()
    attendance_df["%Raids"] = (100*attendance_df["#Raids"] / (attendance_df.shape[1] - 2)).round(2)

    for index, row in attendance_df.iterrows():
        attend_row = []
        first_raid = 0
        for value in row.values[:-3]:
            if value==1:
                first_raid = 1

            if first_raid:
                attend_row.append(value)

        n_raids_sf = sum(attend_row)
        p_raids_sf = round(100 * n_raids_sf / len(attend_row), 2)
        attendance_df.loc[index, "#Raids-SinceFirst"] = int(n_raids_sf)
        attendance_df.loc[index, "%Raids-SinceFirst"] = p_raids_sf
    attendance_df = attendance_df.drop(columns=["#Raids-SinceFirst"])
    attendance_df.index.name = "Player"
    
    return attendance_df

def get_merged_df(attendance_df="attendance_df", html_loot_df="html_loot_df", path_to_lua="rc_path"):
    merged_df = html_loot_df.join(attendance_df, on="Player")
    groups = get_rc_loot_df(path_to_lua)[["date", "player", "response"]].groupby(by="player")
    for key, group_df in groups:
        if sum(merged_df["Player"].isin([key])):
            group_df = group_df.loc[group_df["response"].isin(["BiS", "R-BiS", "Major"])]
            if len(group_df)>=1:
                last_loot_date = group_df["date"].max()
                days_since_last_loot = (datetime.now().date() - last_loot_date.date()).days
            else:
                # if no BiS or Major loot has been given, mark -1
                days_since_last_loot = -1
            merged_df.loc[merged_df["Player"]==key, "#Days-LastLoot"] = days_since_last_loot

    merged_df["#Days-LastLoot"] = merged_df["#Days-LastLoot"].astype(int)
    merged_df["#BiS-perRaid"] = (merged_df["#BiS"] / merged_df["#Raids"]).astype(float).round(2)
    merged_df["#Major-perRaid"] = (merged_df["#Major"] / merged_df["#Raids"]).astype(float).round(2)
    columns = merged_df.columns.tolist()
    player_cols = columns[:3]
    loot_cols = columns[3:12]
    stats_cols = columns[-7:]
    merged_df = merged_df[player_cols+stats_cols+loot_cols]
    merged_df = merged_df.drop(columns="#Misc")
    return merged_df

def make_html_loot_history(html_loot_df="get_html_loot_df()", save=True, upload=True, token="token"):
    # def make_html_loot_history(html_loot_df=get_html_loot_df()):
    # grabbing loot as html
    loot_text = html_loot_df.to_html(index=True).replace("&lt;", "<").replace("&gt;", ">")[37:]

    # pandas automatically aligns right
    loot_text = loot_text.replace('<tr style="text-align: right;">', "<tr>")

    # class colors
    color_marker = 0
    p_classes = class_colors.keys()
    loot_lines = loot_text.split("\n")
    for i in range(len(loot_lines)):
        line = loot_lines[i]

        if color_marker==0:
            for p_class in p_classes:
                if (p_class in line) and ("32"  in line):
                    color_marker = 1
                    class_color = class_colors[p_class]

        elif color_marker < 14: # 7:
            new_line = line.replace("<td>", "<td style='font-weight:bold;color:"+class_color+"'>")
            loot_lines[i] = new_line
            color_marker += 1

        else:
            color_marker = 0

    loot_text = "\n".join(loot_lines[:-1])

    output_text = """<!DOCTYPE html>
    <html>
    <head>

    <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/5.1.3/css/bootstrap.min.css">
    <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.12.1/css/dataTables.bootstrap5.min.css">	

    <style>
        body, table, tbody, thead, td, tr {
            color: #B3B3B3;
            max-width: 99.999%;
            vertical-align: middle;
            background-color: #121212;
            text-align:left;
            font-size: 13px;
            font-family: 'Helvetica', 'Arial', sans-serif;
        }

        th {
            font-size:13px;
            font-weight:bold;
        }
    </style>

    <script src="https://wow.zamimg.com/js/tooltips.js"></script>
    <script type="text/javascript" language="javascript" src="https://code.jquery.com/jquery-3.5.1.js"></script>
    <script type="text/javascript" language="javascript" src="https://cdn.datatables.net/1.12.1/js/jquery.dataTables.min.js"></script>
    <script type="text/javascript" language="javascript" src="https://cdn.datatables.net/fixedheader/3.2.4/js/dataTables.fixedHeader.min.js"></script>
    <script>
        const whTooltips = {colorLinks: true, iconizeLinks: true, renameLinks: true};

        $(document).ready(function () {
            $('#example').DataTable(
                {
                    paging: false,
                    fixedHeader: true,
                    scrollY: '85vh',
                    search:{
                        smart:true,
                        regex:true,
                        caseInsensitive:true,
                    },
                    columnDefs: [
                        {
                            target: 0,
                            visible: false,
                            searchable: false,
                        },
                        {
                            target: 1,
                            visible: false,
                            searchable: true,
                        }
                    ]
                }
            );
        });
    </script>
    </head>
    <body>
    <table id="example" class="table compact" width="100%">
    """ + \
    loot_text + \
    """
    </table>
    </body>
    </html>
    """
    
    if save:
        with open(os.getcwd() + "/loot_history.html", "w", encoding="utf-8-sig") as op:
            op.write(output_text)
    
    if upload:
        g = github.Github(token)
        repo = g.get_user().get_repo("pereirabarataap.github.io")
        contents = repo.get_contents("loot_history.html")
        repo.update_file(
            "loot_history.html",
            str(datetime.now()),
            output_text,
            contents.sha,
            branch="main"
        )         

def run_main():

    rc_mod_date = copy(
        pd.to_datetime(
            datetime.utcfromtimestamp(
                os.path.getmtime(rc_path)
            )
        )
    )

    while True:
        rc_mod_date_check = copy(
            pd.to_datetime(
                datetime.utcfromtimestamp(
                    os.path.getmtime(rc_path)
                )
            )
        )

        if rc_mod_date != rc_mod_date_check:            
            rc_mod_date = copy(rc_mod_date_check)
            
            rc_loot_df = copy(get_rc_loot_df(rc_path, save=False))
            html_loot_df = copy(get_html_loot_df(rc_loot_df, save=False))
            attendance_df = copy(get_attendance_df(rc_path, logs_folder))
            merged_df = copy(get_merged_df(attendance_df, html_loot_df, rc_path))
            make_html_loot_history(merged_df, save=True, upload=True, token=token)
            
            time.sleep(5)
            
            print(
                datetime.now(), "Loot updated", end="\r", flush=True
            )
            
        else:
            time.sleep(5)
            
if __name__ == "__main__":
    run_main()