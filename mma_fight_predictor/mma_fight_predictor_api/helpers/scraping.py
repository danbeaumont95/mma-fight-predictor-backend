from .helpers import get_soup_from_url, return_response
from ..Fighter.models import Fighter
from ..Fights.models import Fight
import re
from progress.bar import Bar
from rest_framework import status
from rest_framework.response import Response
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString
def get_text_after_colon(input_string):
    # Split the input_string by the colon (':') and get the second part
    parts = input_string.split(':', 1)
    if len(parts) > 1:
        return parts[1].strip()  # Return the text after the colon (remove leading/trailing whitespace)
    else:
        return None  # Return None if no colon is found in the string

def get_text(td):
  return td.text.strip().lower()

def scrape_raw_fighter_details():
    lowercase_letters = list("abcdefghijklmnopqrstuvwxyz")
    bar = Bar('Processing', max=26)

    for item in lowercase_letters:
        url = f"http://ufcstats.com/statistics/fighters?char={item}&page=all"
        soup = get_soup_from_url(url)

        fighter_details = soup.select('tbody .b-statistics__table-row')
        for fighter in fighter_details:
            tds = fighter.find_all('td')
            first_name = ""
            last_name = ""
            nickname = ""
            height = ""
            weight = ""
            reach = ""
            stance = ""
            record = ""
            belt = ""
            dob = ""
            slpm = ""
            str_acc = ""
            sapm = ""
            str_def = ""
            td_avg = ""
            td_acc = ""
            td_def = ""
            sub_avg = ""

            for index, td in enumerate(tds):
                if index == 0:
                    first_name = get_text(td)
                elif index == 1:
                    last_name = get_text(td)
                    fighter_anchor = td.find('a')
                    if fighter_anchor:
                        fighter_link = fighter_anchor['href']
                elif index == 2:
                    nickname = get_text(td)
                elif index == 3:
                    height = get_text(td)
                elif index == 4:
                    weight = get_text(td)
                elif index == 5:
                    reach = get_text(td)
                elif index == 6:
                    stance = get_text(td)
                elif index == 7:
                    record += get_text(td) + '/'
                elif index == 8:
                    record += get_text(td) + '/'
                elif index == 9:
                    record += get_text(td)
                elif index == 10:
                    belt = get_text(td)

            # Check if the fighter already exists in the database
            fighter_obj, created = Fighter.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={
                    'record': record,
                    'height': height,
                    'stance': stance,
                    'dob': dob,
                    'weight': weight,
                    'reach': reach,
                    'slpm': slpm if slpm != '' else 0,
                    'str_acc': str_acc,
                    'sapm': sapm if sapm != '' else 0,
                    'str_def': str_def,
                    'td_avg': td_avg if td_avg != '' else 0,
                    'td_acc': td_acc,
                    'td_def': td_def,
                    'sub_avg': sub_avg if sub_avg != '' else 0,
                }
            )

            if created:
                print(f"New fighter created: {fighter_obj.first_name} {fighter_obj.last_name}")
            else:
                print(f"Fighter already exists: {fighter_obj.first_name} {fighter_obj.last_name}")
            if created:
              if 'fighter_link' in locals():

                if len(fighter_link) > 0:
                    fighter_soup = get_soup_from_url(fighter_link)
                    ul_tag = fighter_soup.find('ul', class_='b-list__box-list')
                    if ul_tag:
                        for li_tag in ul_tag.find_all('li', class_='b-list__box-list-item'):
                            title = li_tag.find('i', class_='b-list__box-item-title').text.strip()
                            content = li_tag.get_text(strip=True, separator=' ')
                            if title == "DOB:":
                                dob = content.replace("DOB:", "").strip()

                    second_div_tag = fighter_soup.find('div', class_='b-list__info-box-left clearfix')
                    for li_tag in second_div_tag.find_all('li', class_='b-list__box-list-item b-list__box-list-item_type_block'):
                        title = li_tag.find('i', class_='b-list__box-item-title').text.strip()
                        content = li_tag.get_text(strip=True, separator=' ')
                        if title == "SLpM:":
                            slpm = content.replace("SLpM:", "").strip()
                        elif title == "Str. Acc.:":
                            str_acc = content.replace('Str. Acc.:', '').strip()
                        elif title == "SApM:":
                            sapm = content.replace('SApM:', '').strip()
                        elif title == "Str. Def:":
                            str_def = content.replace('Str. Def:', '').strip()
                        elif title == "TD Avg.:":
                            td_avg = content.replace('TD Avg.:', '').strip()
                        elif title == "TD Acc.:":
                            td_acc = content.replace('TD Acc.:', '').strip()
                        elif title == "TD Def.:":
                            td_def = content.replace('TD Def.:', '').strip()
                        elif title == "Sub. Avg.:":
                            sub_avg = content.replace('Sub. Avg.:', '').strip()
                    fighter_to_update = Fighter.objects.filter(first_name=first_name, last_name=last_name).first()
                    fighter_to_update.slpm = slpm
                    fighter_to_update.str_acc = str_acc
                    fighter_to_update.sapm = sapm
                    fighter_to_update.str_def = str_def
                    fighter_to_update.td_avg = td_avg
                    fighter_to_update.td_acc = td_acc
                    fighter_to_update.td_def = td_def
                    fighter_to_update.sub_avg = sub_avg
                    fighter_to_update.dob = dob
                    fighter_to_update.save()
        bar.next()

    bar.finish()
    return {'Success': True}


def extract_text(tag):
    if isinstance(tag, NavigableString):
        return tag.strip()
    else:
        return tag.get_text().strip()
      
      
def scrape_raw_fight_details():
  print('raw fight scraper')
  exception_arrs = []
  url = f"http://ufcstats.com/statistics/events/completed?page=all"
  soup = get_soup_from_url(url)
  skipped_events = 0

  all_events = soup.select('.b-statistics__table-row')
  for event in all_events:
    if skipped_events < 2:
        skipped_events += 1
        continue

    a_tag = event.find('a', class_='b-link_style_black')
    date_tag = event.find('span', class_='b-statistics__date')
    if date_tag:
      date = date_tag.get_text(strip=True)
      input_format_str = "%B %d, %Y"
      output_format_str = "%Y-%m-%d"

      # Parse the input date string to a datetime object
      input_date = datetime.strptime(date, input_format_str)

      # Format the datetime object to the desired output format
      date = input_date.strftime(output_format_str)
    else:
      print('no date tag')
      break
    if a_tag:
      href_value = a_tag['href']
      href_soup = get_soup_from_url(href_value)
      location_element = href_soup.find("i", text=re.compile(r"\s*Location\s*:\s*", re.IGNORECASE))
      location = location_element.next_sibling.strip()
      fights = href_soup.select('.b-fight-details__table-body tr')
      for fight in fights:
        # Find the first fighter's name (blue fighter)
        blue_fighter_tag = fight.find('td', class_='b-fight-details__table-col l-page_align_left')
        blue_fighter_name = blue_fighter_tag.find('a', class_='b-link_style_black').text.strip()

        blue_fighter_full_name = blue_fighter_name.lower().split()
        blue_fighter_first_name = blue_fighter_full_name[0]
        blue_fighter_last_name = " ".join(blue_fighter_full_name[1:])
        # try:
          
        blue_fighter = Fighter.objects.filter(first_name=blue_fighter_first_name, last_name=blue_fighter_last_name)
        if len(blue_fighter) == 0:
          
      # except Fighter.DoesNotExist:
          print(f'{blue_fighter_full_name} does not exist')
          
          blue_first = ' '.join(blue_fighter_full_name[:-1])
          blue_last = blue_fighter_full_name[-1]
          blue_fighter = Fighter.objects.filter(first_name=blue_first, last_name=blue_last)
        blue_fighter_exists = blue_fighter.exists()
        if blue_fighter_exists == True:
          fight_already_exists = Fight.objects.filter(blue_fighter=blue_fighter.first(), date=date).exists()
          if fight_already_exists == True:
            print(f'Fight already exists in database {blue_fighter_full_name}, {datetime.now()}')
            break
        red_fighter_tags = fight.find_all('a', class_='b-link_style_black')
        red_fighter_name = red_fighter_tags[1].text.strip()
        red_fighter_full_name = red_fighter_name.lower().split()
        red_fighter_first_name = red_fighter_full_name[0]
        red_fighter_last_name = " ".join(red_fighter_full_name[1:])
        # try:
        red_fighter = Fighter.objects.filter(first_name=red_fighter_first_name, last_name=red_fighter_last_name)
        if len(red_fighter) == 0:
          
          print(f'{red_fighter_name} does not exist')
          red_first = ' '.join(red_fighter_full_name[:-1])
          red_last = red_fighter_full_name[-1]
          red_fighter = Fighter.objects.filter(first_name=red_first, last_name=red_last)
          
        # single_fight_href = 
        anchor_tag = fight.find('a', class_='b-flag_style_green')
        link = None
        # Check if the <a> tag is found and get the value of "href" attribute
        if anchor_tag:
            link = anchor_tag.get('href')
        else:
            print("The desired <a> tag is not found.")
        
        if link is not None:
          weight = None
          method = None
          round = None
          time = None
          time_format = None
          win_by = None
          referee = None
          single_fight_soup = get_soup_from_url(link)
          for div in single_fight_soup.findAll("div", {"class": "b-fight-details__person"}):

            if (
                div.find(
                    "i",
                    {
                        "class": "b-fight-details__person-status b-fight-details__person-status_style_green"
                    },
                )
                is not None
            ):
                winner = (
                    div.find("h3", {"class": "b-fight-details__person-name"})
                    .text.replace(" \n", "")
                    .replace("\n", "")
                )
            if (
                div.find(
                    "i",
                    {
                        "class": "b-fight-details__person-status b-fight-details__person-status_style_gray"
                    },
                )
                is not None
            ):
                loser = (
                    div.find("h3", {"class": "b-fight-details__person-name"})
                    .text.replace(" \n", "")
                    .replace("\n", "")
                )
                

          
          basic_fight_stats = single_fight_soup.find('div', {'class': 'b-fight-details__fight'})
          weight = basic_fight_stats.find('i').text.strip()
          method_element = basic_fight_stats.find("i", text=re.compile(r"\s*Method\s*:\s*", re.IGNORECASE))
          round_element = basic_fight_stats.find('i', {'class': 'b-fight-details__text-item'})
          text = round_element.get_text(strip=True)
          round = text.split(":",1)[1]
          if method_element:
            method= method_element.find_next("i").get_text(strip=True)

          time_element = basic_fight_stats.find("i", text=re.compile(r"\s*Time\s*:\s*", re.IGNORECASE))
          time = time_element.next_sibling.strip()
          time_format_element = basic_fight_stats.find("i", text=re.compile(r"\s*Time Format\s*:\s*", re.IGNORECASE))
          time_format = time_format_element.next_sibling.strip()
          win_by = basic_fight_stats.find('i', {'class': 'b-fight-details__text-item_first'}).text.strip()

          win_by = get_text_after_colon(win_by)

          referee_element = basic_fight_stats.find("i", text=re.compile(r"\s*Referee\s*:\s*", re.IGNORECASE))

          referee = referee_element.find_next_sibling("span").text.strip()

          all_elements = single_fight_soup.find_all(class_="b-fight-details__section js-fight-section")
          if len(all_elements) >= 2:
            total_strikes = all_elements[1]

            table = total_strikes.find('table')

            tbody = table.find('tbody')

            # Find all rows (tr) in the table body
            rows = tbody.find_all('tr')

            # Initialize a list to store fighter stats
            fighters_stats = []

            # Iterate through each row and extract the stats for each fighter
            for row in rows:
                # Find all columns (td) in the row
                columns = row.find_all('td')
                
                # Extract the fighter name from the first column (l-page_align_left)
                fighter_name_elements = columns[0].find_all('a', class_='b-link_style_black')
                fighter_names = [element.get_text(strip=True) for element in fighter_name_elements]
                
                # Extract stats from the remaining columns and store them in a dictionary
                fighter_stats = {
                    'Fighter': fighter_names,
                    'KD': [stat.get_text(strip=True) for stat in columns[1].find_all('p')],
                    'Sig. str.': [stat.get_text(strip=True) for stat in columns[2].find_all('p')],
                    'Sig. str. %': [stat.get_text(strip=True) for stat in columns[3].find_all('p')],
                    'Total str.': [stat.get_text(strip=True) for stat in columns[4].find_all('p')],
                    'Td': [stat.get_text(strip=True) for stat in columns[5].find_all('p')],
                    'Td %': [stat.get_text(strip=True) for stat in columns[6].find_all('p')],
                    'Sub. att': [stat.get_text(strip=True) for stat in columns[7].find_all('p')],
                    'Rev.': [stat.get_text(strip=True) for stat in columns[8].find_all('p')],
                    'Ctrl': [stat.get_text(strip=True) for stat in columns[9].find_all('p')],
                }
                
                # Append the fighter stats to the list
                fighters_stats.append(fighter_stats)

            # Print the extracted fighter stats

            b_kd = fighters_stats[0]['KD'][0]
            r_kd = fighters_stats[0]['KD'][1]
            b_sig_str = fighters_stats[0]['Sig. str.'][0]
            r_sig_str = fighters_stats[0]['Sig. str.'][1]
            b_sig_str_pct = fighters_stats[0]['Sig. str. %'][0]
            r_sig_str_pct = fighters_stats[0]['Sig. str. %'][1]
            b_total_str = fighters_stats[0]['Total str.'][0]
            r_total_str = fighters_stats[0]['Total str.'][1]
            b_td = fighters_stats[0]['Td'][0]
            r_td = fighters_stats[0]['Td'][1]
            b_td_pct = fighters_stats[0]['Td %'][0]
            r_td_pct = fighters_stats[0]['Td %'][1]
            b_sub_att = fighters_stats[0]['Sub. att'][0]
            r_sub_att = fighters_stats[0]['Sub. att'][1]
            b_rev = fighters_stats[0]['Rev.'][0]
            r_rev = fighters_stats[0]['Rev.'][1]
            b_ctrl = fighters_stats[0]['Ctrl'][0]
            r_ctrl = fighters_stats[0]['Ctrl'][1]
            
            significant_strikes = single_fight_soup.find_all('table')
            significant_strikes_table = significant_strikes[2]

            tbody = significant_strikes_table.find('tbody')

            # Find all rows (tr) in the table body
            rows = tbody.find_all('tr')

            # Initialize a list to store fighter stats
            fighters_significant_stats = []

            # Iterate through each row and extract the stats for each fighter
            for row in rows:

              columns = row.find_all('td')
                
              # Extract the fighter name from the first column (l-page_align_left)
              fighter_name_elements = columns[0].find_all('a', class_='b-link_style_black')
              fighter_names = [element.get_text(strip=True) for element in fighter_name_elements]
              
              # Extract stats from the remaining columns and store them in a dictionary
              fighter_stats = {
                  'Fighter': fighter_names,
                  'Sig. str.': [stat.get_text(strip=True) for stat in columns[1].find_all('p')],
                  'Sig. str. %': [stat.get_text(strip=True) for stat in columns[2].find_all('p')],
                  'Head': [stat.get_text(strip=True) for stat in columns[3].find_all('p')],
                  'Body': [stat.get_text(strip=True) for stat in columns[4].find_all('p')],
                  'Leg': [stat.get_text(strip=True) for stat in columns[5].find_all('p')],
                  'Distance': [stat.get_text(strip=True) for stat in columns[6].find_all('p')],
                  'Clinch': [stat.get_text(strip=True) for stat in columns[7].find_all('p')],
                  'Ground': [stat.get_text(strip=True) for stat in columns[8].find_all('p')],
              }
              
              # Append the fighter stats to the list
              fighters_significant_stats.append(fighter_stats)

            b_head = fighters_significant_stats[0]['Head'][0]
            r_head = fighters_significant_stats[0]['Head'][1]
            b_body = fighters_significant_stats[0]['Body'][0]
            r_body = fighters_significant_stats[0]['Body'][1]
            b_leg = fighters_significant_stats[0]['Leg'][0]
            r_leg = fighters_significant_stats[0]['Leg'][1]
            b_distance = fighters_significant_stats[0]['Distance'][0]
            r_distance = fighters_significant_stats[0]['Distance'][1]
            b_clinch = fighters_significant_stats[0]['Clinch'][0]
            r_clinch = fighters_significant_stats[0]['Clinch'][1]
            b_ground = fighters_significant_stats[0]['Ground'][0]
            r_ground = fighters_significant_stats[0]['Ground'][1]
            
            
            try:
              first = {
                'dan': blue_fighter.first()
              }
              dict1 = {
                'blue_fighter': blue_fighter.first(), 
                'red_fighter':red_fighter.first(), 
                'b_kd':b_kd,
                'r_kd':r_kd, 
                'b_sig_str': b_sig_str,
                'r_sig_str': r_sig_str, 
                'b_sig_str_pct': b_sig_str_pct,
                'r_sig_str_pct': r_sig_str_pct, 
                'b_total_str': b_total_str, 
                'r_total_str': r_total_str, 
                'b_td':b_td, 
                'r_td': r_td, 
                'b_td_pct': b_td_pct, 
                'r_td_pct': r_td_pct, 
                'b_sub_att': b_sub_att, 
                'r_sub_att': r_sub_att, 
                'b_rev': b_rev, 
                'r_rev': r_rev, 
                'b_ctrl': b_ctrl, 
                'b_head': b_head, 
                'r_head': r_head, 
                'b_body': b_body,
                'r_body': r_body, 
                'b_leg': b_leg, 
                'r_leg': r_leg, 
                'b_distance': b_distance, 
                'r_distance': r_distance, 
                'b_clinch': b_clinch, 
                'r_clinch': r_clinch,
                'b_ground': b_ground, 
                'r_ground': r_ground, 
                'win_by': win_by, 
                'last_round': round, 
                'last_round_time': time, 
                'referee': referee, 
                'date': date, 
                'location': location, 
                'fight_type': weight, 
                'winner': winner, 
                'loser': loser
              }
              
              Fight.objects.create(blue_fighter=blue_fighter.first(), red_fighter=red_fighter.first(), b_kd=b_kd, r_kd=r_kd, b_sig_str=b_sig_str, r_sig_str=r_sig_str, b_sig_str_pct=b_sig_str_pct, r_sig_str_pct=r_sig_str_pct, b_total_str=b_total_str, r_total_str=r_total_str, b_td=b_td, r_td=r_td, b_td_pct=b_td_pct, r_td_pct=r_td_pct, b_sub_att=b_sub_att, r_sub_att=r_sub_att, b_rev=b_rev, r_rev=r_rev, b_ctrl=b_ctrl, r_ctrl=r_ctrl, b_head=b_head, r_head=r_head, b_body=b_body, r_body=r_body, b_leg=b_leg, r_leg=r_leg, b_distance=b_distance, r_distance=r_distance, b_clinch=b_clinch, r_clinch=r_clinch, b_ground=b_ground, r_ground=r_ground, win_by=win_by, last_round=round, last_round_time=time, referee=referee, date=date, location=location, fight_type=weight, winner=winner, loser=loser, format=time_format)
            except Exception as e:
              exception_arrs.append({'error': e, 'fight': f'{blue_fighter_full_name} - {red_fighter_full_name}'})
              print(e, f'Error creating fight between {blue_fighter_full_name} - {red_fighter_full_name}')
            
    else:
      print('no a tag')
  print(exception_arrs, 'exception_arrs123')
  with open('errors-4.txt', 'w') as f:
    for line in exception_arrs:
        f.write(f"{line}\n")
