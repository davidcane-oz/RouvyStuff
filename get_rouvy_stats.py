import json
import os
import sys

from numpy import False_

def extract_level( str_level, str_id):

    if str_level.startswith(str_id): 

        str_level = str_level.lstrip(str_id)

        try:
            return int ( str_level )
        except ValueError:
            return -1
    else:
        return-1


def get_distance_level( el_id ):
    return extract_level( el_id, "total-distance-level-")
 
def get_climber_level( el_id ):
   return extract_level( el_id, "climber-level-")

def get_kcal_level( el_id ):
    return extract_level( el_id, "burn-kcal-level-")

def get_time_level( el_id ):
    return extract_level( el_id, "active-time-level-")

def get_outdoor_level( el_id ):
    return extract_level( el_id, "outdoor")
 
def show_progress( type, last_data, progress_data ):

    if "goalsToAchieve" in progress_data and "goalsProgress" in progress_data:
        try:
            start = int (last_data["goalsToAchieve"][0]["value"])
            goal = int (progress_data["goalsToAchieve"][0]["value"])
            progress = int (progress_data["goalsProgress"][0]["value"])
            unLocked_time = last_data['unlockedAt'].replace('T', ' @ ')[:-7]

            if (progress_data["goalsProgress"][0]["goalId"] == "distanceInMeters"):
                current = format(f"{(progress/1000):.0f}km")
            elif (progress_data["goalsProgress"][0]["goalId"] == "outdoorDistanceInMeters"):
                current = format(f"{(progress/1000):.0f}km")
                last_data['title'] = "(Outdoors) " + last_data['title'] 
            elif (progress_data["goalsProgress"][0]["goalId"] == "elevationInMeters"):
                current = format(f"{(progress):,.0f}m")
            elif (progress_data["goalsProgress"][0]["goalId"] == "kilocaloriesBurned"):
                current = format(f"{(progress):,.0f}kcal")
            elif (progress_data["goalsProgress"][0]["goalId"] == "movingTimeInSeconds"):
                current = format(f"{(progress/3600):.0f}:{((progress%3600)/60):02.0f}:{((progress%3600)%60):02.0f}")             
            else:
                current=""

            print(f"Achieved {last_data['title'].lower()} on {unLocked_time} ; current total is ({current})", end= " ")

            if goal == start:
                print(": Maximum level achieved")
            else:
               print(f"which is {(progress-start)*100/(goal-start):.0f}% towards next level")
                 
        except ValueError:
            print("\tNot found")

def is_unlocked( time ):
   return time != "0001-01-01T00:00:00.000"

def is_achievement( element ):
    achievement_levels = ["total-distance-level-","climber-level-","burn-kcal-level-","active-time-level-" ]

    for achievement in achievement_levels:
        if element['id'].startswith( achievement ):
            return True

    return False

#write 2 x 2 tables for distance, climber, kcal and active time

def get_achievement_html( data ) :
    achievement_levels = ["total-distance-level-","climber-level-","burn-kcal-level-","active-time-level-" ]
    columns = ["Achievement", "Unlocked at", "Points"]
    n = 1
    str_html = ''
    table_head = f"<tr><th>{'</th><th>'.join(columns)}</th></tr>\n"
    
    for achievement_level in achievement_levels:
        First = True
        if n==1 or n==3:
            if n==3:
                str_html += '<div style="clear:both;height:48px;"></div>'

            str_html += '<div class="container">\n<table>\n<td>\n<table class="table1">\n'
        else:
            str_html += '<td>\n<table class="table2">\n'

        last_element=None
        for element in data:
            if element['id'].startswith( achievement_level ):
                element_data=None
                if is_unlocked( element['unlockedAt'] ):
                    element_data = [element['title'], element['unlockedAt'][:10], str(element['points'])]
                    last_element = element
                else:
                    if 'successorOf' in element and 'id' in last_element and element["successorOf"] == last_element["id"]:
                        start = int (last_element["goalsToAchieve"][0]["value"])
                        goal = int (element["goalsToAchieve"][0]["value"])
                        progress = int (element["goalsProgress"][0]["value"])
                        element_data = [element['title'], f"{(progress-start)*100/(goal-start):.0f}% done", str(element['points'])]

                if element_data:
                    if First:
                        str_html += table_head
                        First = False
                    str_html += f"<tr><td>{'</td><td>'.join(element_data)}</td></tr>\n"

        str_html += '</table>\n</td>\n'

        if n==2 or n==4:
            str_html += '</table>\n</div>\n'
            if n==4:
                str_html += '<div style="clear:both;height:48px;"></div>\n'
        
        n+=1

    return str_html


#write 2 badges per row

def get_badge_html( data ) :
    columns = ["Badge", "Date", "Points", ""]

    table_head = f"<thead>\n<tr><th>{'</th><th>'.join(columns)}</th><th>{'</th><th>'.join(columns)}</th></tr>\n</thead>"
    table_body = "\n<tbody>\n"
    
    n = 1
    
    for element in data:
        if is_unlocked( element['unlockedAt'] ):
            if not is_achievement(element):
                date = element['unlockedAt'][5:10] + '-'+element['unlockedAt'][2:4]
                element_data = [element['title'], date, str(element['points']),  '<img src="' + element['badgeToReward']['url'] + '" width="64" height="64">']
                if (n%2 == 1):
                    table_body+="<tr>"
                table_body += f"<td>{'</td><td>'.join(element_data)}</td>\n"
                if (n%2 == 0):
                    table_body+="</tr>\n"
                n+=1

    #fill in second half of table if empty

    if (n%2 == 0):
        table_body+="<td></td><td></td><td></td><td></td></tr>\n"

    table_body += "</tbody>\n"

    return(f'<div class="container">\n<table class="table3">\n{table_head}{table_body}</table>\n</div>\n')

def write_html( filein, header, fileout ):
    s = '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<title>Rouvy achievements and badges</title>\n'
    s+= '<link rel="stylesheet" href="style.css">\n</head>\n<body>'
    header = header.strip().replace('\n', '</p><p>')
    s += '<h1><p>'+header+'</p></h1>\n'
    try:
        with open(filein, "r") as infile:
            for line in infile:
                data = json.loads( line ) 
                break   

        s+= get_achievement_html( data )
        s+= get_badge_html( data )

        with open(fileout, 'w') as f:
            f.write(s)

    except:
        pass




def analyze_achievements( user, file ):

    #print(f"\nAchievements for user id {user}\n")       

    try:
        with open(file, "r") as infile:
            for line in infile:
                data = json.loads( line ) 
                break   

        max_level = 23
        badges = list()
        last_outdoor_level = 0
        
        for element in data:
            el_id = element["id"]
            unlocked = element['unlockedAt'] != "0001-01-01T00:00:00.000"
           
            if (unlocked):
                if get_distance_level( el_id ) >= 0:
                    last_distance = element
                    if get_distance_level( el_id ) == max_level:
                        show_progress( "Distance",  element, element)    
                elif get_climber_level( el_id ) >= 0:
                    last_climber = element
                    if get_climber_level( el_id ) == max_level:
                        show_progress( "Climber",  element, element)
                elif get_kcal_level( el_id ) >= 0:
                    last_kcal = element
                    if get_kcal_level( el_id ) == max_level:
                        show_progress( "kCal",  element, element)
                elif get_outdoor_level( el_id ) >= 0:
                    last_outdoor = element
                    last_outdoor_level = get_outdoor_level( el_id )
                    if last_outdoor_level == 13:
                        show_progress( "Outdoor",  element, element)
                elif get_time_level( el_id ) >= 0:
                    last_time = element
                    if get_time_level( el_id ) == max_level:
                        show_progress( "Time",  element, element)
                else:  # its a one-off achievement
                    badges.append( element['title'] )
            else:
                if 'successorOf' in element:
                    if get_distance_level( el_id ) >= 0 and element["successorOf"] == last_distance["id"]:
                        show_progress( "Distance", last_distance , element)
                    elif get_climber_level( el_id ) >= 0 and element["successorOf"] == last_climber["id"]:
                        show_progress( "Climb",  last_climber, element)
                    elif get_kcal_level( el_id ) >= 0 and element["successorOf"] == last_kcal["id"]:
                        show_progress( "kCal",  last_kcal, element)
                    elif get_time_level( el_id ) >= 0 and element["successorOf"] == last_time["id"]:
                        show_progress( "Time",  last_time, element)
                elif get_outdoor_level( el_id ) == (last_outdoor_level+1) :
                    show_progress( "Outdoor",  last_outdoor, element)                        
    except:
        sys.exit("Some json() error" )
        
    #format badges in a grouping
    badges_str = "Badges: "
    badge_line = ""
    for badge in badges:
        badge_line = badge_line + badge + ", "
        if len(badge_line) > 72:
            badges_str = badges_str + badge_line + '\n'
            badge_line = "\t"
    if badge_line:
        badges_str = badges_str + badge_line + '\n'

    badges_str = badges_str.strip(", \n\t")
    print(badges_str + "\n")

def get_career_stats( user, file ):

    print(f"Career information for user id {user}\n")       

    try:
        with open(file, "r") as infile:
            for line in infile:
                data = json.loads( line ) 
                break   

        coins = data["points"]
        cFtp = data["ftp"]
        history = data["history"]
        level  = 1

        while True:
            str_level = "level-"+f"{level}"

            if str_level in history:
                level_time = history[str_level][:10] #.replace('T', ' @ ')[:-7]
                level = level+1
            else:
                break

        return(f"User {user} is at level {level-1}, achieved on {level_time}\nCoins : {coins}\nFTP: {cFtp}\n")
    except:
        sys.exit("Some json() error" )



def main():

    """
    user data in {user}/appdata/LocalLow/VirtualTraining/ROUVY/data/users
    career.json
    achievements.json
    other data in 
    {user}/appdata/LocalLow/VirtualTraining/ROUVY/data/career
    histogram.json
    levels.json


    """

    #if len(sys.argv) == 2 :
    path = os.getenv('APPDATA').replace("Roaming", "LocalLow\\VirtualTraining\\ROUVY\\data\\users")
    array = os.listdir(path)

    for dir in array:
        
        subdirs = dir.split('\\')

        if len(subdirs) > 0:

            if subdirs[len(subdirs)-1] != "-1":
                user = subdirs[len(subdirs)-1]
                
                file = path + "\\" + dir +"\\career\\career.json"
                header =  get_career_stats(user, file)

                print(header)

                file = path + "\\" + dir +"\\career\\achievements.json"

                write_html( file, header, "..\\html-css-python\\rouvy\\rouvystats.html")

                #analyze_achievements(user, file)
                break
            
        

if __name__ == "__main__":
    main()