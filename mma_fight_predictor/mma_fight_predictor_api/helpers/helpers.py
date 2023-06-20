from rest_framework.response import Response
import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict
import pandas as pd
import copy
from io import StringIO
import csv
import re
from pandas_schema.validation import CustomElementValidation
from django.db.models import F
from .constants import WEIGHT_CLASSES
from pandas_schema import Column, Schema
from ..Fighter.models import Fighter
from ..User.models import User
from ..Fights.models import Fight
from datetime import datetime
from django.db.models import F, Q
import json
from rest_framework.decorators import api_view
from rest_framework import status
from django.db.models import F
import re

def convert_snake_to_camel(string: str) -> str:
    string = re.sub(r'(?<=[a-z0-9])(?=[A-Z0-9])|[^a-zA-Z0-9]',
                    ' ', string).strip().replace(' ', '_')

    return ''.join(string.lower())

def return_response(data, message, status):
    return Response({'data': data, 'message': message, 'status': status})

def get_soup_from_url(url):
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(url, headers=headers)
    html_content = response.content
    soup = BeautifulSoup(html_content, "html.parser")
    return soup

def compare_fractions(fraction1, fraction2):
    # Convert the fractions to a common denominator
    denominator = fraction1[1] * fraction2[1]
    numerator1 = fraction1[0] * fraction2[1]
    numerator2 = fraction2[0] * fraction1[1]

    # Compare the numerators
    if numerator1 > numerator2:
        # return "The first fraction {} is larger than the second fraction {}.".format(fraction1, fraction2)
        return fraction1[2]
    elif numerator1 < numerator2:
        return fraction2[2]
    else:
        return "Equal"


fraction1 = (8, 3)
fraction2 = (21, 3)


def get_fighters_fighting_style(name):
  name_parts = name.split()
  first_name = name_parts[0]
  if len(name_parts) > 1:
    if len(name_parts) > 2:
      last_name = " ".join(name_parts[1:])
    else:
      last_name = name_parts[1]
  else:
    last_name = None
  user_in_db = Fighter.objects.filter(first_name=first_name, last_name=last_name).exists()

  if user_in_db == True:
    fighter = Fighter.objects.filter(first_name=first_name, last_name=last_name).first()
    style = fighter.style
    return style
  url = f'https://www.ufc.com/athlete/{name.replace(" ", "-")}'
  headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
  response = requests.get(url, headers=headers)
  soup = BeautifulSoup(response.content, 'html.parser')
  fighting_style_div = soup.find('div', text='Fighting style')
  if fighting_style_div == None:
    return None
  style = fighting_style_div.find_next_sibling('div').get_text()
  return style

def get_fighters_fighting_stance(name):
    name_parts = name.split()
    first_name = name_parts[0]
    if len(name_parts) > 1:
      if len(name_parts) > 2:
        last_name = " ".join(name_parts[1:])
      else:
        last_name = name_parts[1]
    else:
      last_name = None
    user_in_db = Fighter.objects.filter(first_name=first_name, last_name=last_name).exists()
    if user_in_db == True:
      fighter = Fighter.objects.filter(first_name=first_name, last_name=last_name).first()
      stance = fighter.stance
      return stance
    else:
      fighter_1_stats_search_url = f'http://ufcstats.com/statistics/fighters/search?query={name_parts[0]}&page=all'

      fighter_1_search_soup = get_soup_from_url(fighter_1_stats_search_url)
      fighter_1_a_tag = fighter_1_search_soup.find('a', text=re.compile(name_parts[1].lower(), re.I))
      fighter_1_stats_url_href =  fighter_1_a_tag.get('href')
      fighter_1_search_soup = get_soup_from_url(fighter_1_stats_url_href)
      ulist = fighter_1_search_soup.find('ul', class_='b-list__box-list')
      item = ulist.find(lambda tag: tag.name == 'li' and 'STANCE:' in tag.get_text())
      word = item.get_text(strip=True).split(':', 1)[1].strip()

      return word
    
def get_fighters_record_again_each_opponents_fight_style(fighter_name,url):
  fighter_1_fights_table_soup = get_soup_from_url(url)
  fighter_1_table = fighter_1_fights_table_soup.find('table')
  fighter_1_dfs = pd.read_html(str(fighter_1_table))
  fighter_1_df = fighter_1_dfs[0]
  fighter_1_df = fighter_1_df.dropna()
  fighter_1_df.to_csv('filename.csv', index=False)
  fighter_1_opponent_list = fighter_1_df['Fighter'].tolist()
  fighter_1_opponent_list_without_fighter_1 = [name.replace(fighter_name.title(), "").strip() for name in fighter_1_opponent_list]
  opponents_fighting_style = []
  opponents = []
  result_against_opponents = {}
  for row, column in fighter_1_df.iterrows():
    opponent = column['Fighter'].lower().replace(fighter_name.lower(), "").strip() # this has broken below get_fighters_fighting_style as its now lower, was title before
  
    opponents.append(opponent)
    if opponent not in result_against_opponents:
      result_against_opponents[opponent.lower()] = []
    result = column['W/L']
    result_against_opponents[opponent.lower()].append(result)
    method = column['Method']
    round = column['Round']
    time = column['Time']
    kd = column['Kd']
    strikes = column['Str']
    td = column['Td']
    sub = column['Sub']
    event = column['Event']
    opponent_fighting_stance = get_fighters_fighting_stance(opponent)
    try:
      opponent_fighting_style = get_fighters_fighting_style(opponent)
      opponents_fighting_style.append({'opponent': opponent, 'style': opponent_fighting_style, 'result': result, 'stance': opponent_fighting_stance})
    except:

      opponents_fighting_style.append({'opponent': opponent, 'style': 'unable to find', 'result': result, 'stance': opponent_fighting_stance})
    
  fighter_1_opponent_styles = {d['style'] for d in opponents_fighting_style if 'style' in d}
  fighter_1_opponent_stance = {d['stance'] for d in opponents_fighting_style if 'stance' in d}

  fighter_1_record_agains_each_opponent_style = {style: [d['result'] for d in opponents_fighting_style if d.get('style') == style] for style in fighter_1_opponent_styles}
  fighter_1_record_agains_each_opponent_stance = {stance: [d['result'] for d in opponents_fighting_style if d.get('stance') == stance] for stance in fighter_1_opponent_stance}
  return {'record': fighter_1_record_agains_each_opponent_style, 'opponents': opponents, 'result_against_opponents': result_against_opponents, 'fighter_1_record_agains_each_opponent_stance': fighter_1_record_agains_each_opponent_stance}

def read_fighters_file(file):

    row_id = 0
    new_users = {}
    error_rows = defaultdict(list)
    already_existing_users = {}
    duplicate_identifier = []

    copy_file = copy.copy(file)

    upload_file = copy_file

    if type(file) == str:
        file_to_read = upload_file

    elif isinstance(file, pd.DataFrame):
        file_to_read = upload_file

    else:

        file_to_read = upload_file

        if isinstance(upload_file, dict):
            file_to_read = upload_file
        else:
            file_to_read = upload_file.read().decode('utf-8')

    if not isinstance(file, pd.DataFrame):

        if isinstance(file_to_read, dict):
            data = file_to_read
        else:
            data = StringIO(file_to_read)
    else:
        data = file.astype(str)

    copy_of_csv = copy.deepcopy(data)

    buffered_users = {}

    index_of_manager = {}

    reader = csv.reader(copy_of_csv, delimiter=',')






    if isinstance(file, pd.DataFrame):

        new_headers = []

        for header in file_to_read.columns:

            stripped = header.replace('"', '')

            new_key = stripped.rstrip("\r").split(",")

            key = new_key[0]

            header = key
            new_headers.append(header)

        file_to_read.columns = new_headers

        columns = file_to_read.columns.values
    else:
        csv_copy = copy.deepcopy(data)
        if isinstance(data, dict):

            read_csv = pd.DataFrame(csv_copy)

            columns = list(read_csv.columns.values)
        else:
            string_with_escaped_chars = re.sub(
                '[^A-Za-z0-9]+', '', csv_copy.getvalue())

            if csv_copy.getvalue() == '\r\n':
                return {'Empty_File': 'empty file'}
            if string_with_escaped_chars == '':
                return {'Empty_File': 'empty file'}
            read_csv = pd.read_csv(csv_copy)

            columns = list(read_csv.columns.values)

    column_dict = dict()
    for index, value in enumerate(columns):

        stripped = value.replace('"', '')
        new_val = stripped.rstrip("\r").split(",")
        val = new_val[0]

        column_dict[convert_snake_to_camel(val)] = val

    missing_required_columns = []

    too_many_column_errors = []

    if 'fighter_name' not in columns:
        missing_required_columns.append('fighter_name')

    amount_of_users_to_upload = len(buffered_users)

    schema_list = []

    if isinstance(file, pd.DataFrame):
        read_csv = file_to_read
    if len(schema_list) > 0:
        schema = Schema(schema_list)
        schema_errors = schema.validate(
            read_csv, columns=schema.get_column_names())

        for error in schema_errors:
            error_rows[int(
                error.row) + 1].append({convert_snake_to_camel(error.column): error.message})
    print(read_csv, 'read_csv1')
    if isinstance(file, pd.DataFrame):
        file_to_read.fillna("", inplace=True)

    if isinstance(file, dict):
        iteration = pd.DataFrame.from_dict(file)
    elif isinstance(file, pd.DataFrame):
        iteration = file_to_read
    else:
        iteration = pd.read_csv(data, delimiter=',', quotechar='"', converters={
                                'follower_email': str, 'manager_email': str}, na_filter=False)

    data_to_iterate = iteration

    empty_users = 0

    for column, row_data in data_to_iterate.iterrows():

        try:

            row_id = row_id + 1

            fighter_name = row_data.get(column_dict['fighter_name'])
            height = row_data.get(column_dict['height'])
            weight = row_data.get(column_dict['weight'])
            reach = row_data.get(column_dict['reach'])
            stance = row_data.get(column_dict['stance'])
            dob = row_data.get(column_dict['dob'])
            slpm = row_data.get(column_dict['slp_m'])
            str_acc = row_data.get(column_dict['str_acc'])
            sapm = row_data.get(column_dict['sap_m'])
            str_def = row_data.get(column_dict['str_def'])
            td_avg = row_data.get(column_dict['td_avg'])
            td_acc = row_data.get(column_dict['td_acc'])
            td_def = row_data.get(column_dict['td_def'])
            sub_avg = row_data.get(column_dict['sub_avg'])
            
            name_parts = fighter_name.split()
            if len(name_parts) > 2:
                first_name = name_parts[0]
                last_name = " ".join(name_parts[1:]) if len(fighter_name.split()) > 1 else None
            else:
                first_name = name_parts[0]
                last_name = name_parts[1] if len(fighter_name.split()) > 1 else None

            fighter_already_exists = Fighter.objects.filter(
                first_name=first_name, last_name=last_name).count()

            if fighter_already_exists == 1:
                already_existing_users[row_id] = fighter_name
            else:
              fighters_style = get_fighters_fighting_style(fighter_name)

              Fighter.objects.create(first_name=first_name, last_name=last_name, height=height, weight=weight, reach=reach, stance=stance, dob=dob, slpm=slpm, str_acc=str_acc, sapm=sapm, str_def=str_def, td_avg=td_avg, td_acc=td_acc, td_def=td_def, sub_avg=sub_avg, style=fighters_style)

            new_users[fighter_name] = [
                fighter_name, 
                ]
        except Exception as e:
            print(e, 'error mapping row values')

    users_not_updating = amount_of_users_to_upload - \
        len(already_existing_users)

    if (len(error_rows) > 0):

        return {'Error': error_rows, 'Already_Existing_Users': already_existing_users, 'Column_Error': missing_required_columns, 'too_many_column_errors': too_many_column_errors, 'Duplicate_Identifier': duplicate_identifier}
    return {'New_Users': new_users, 'Already_Existing_Users': already_existing_users, 'Column_Error': missing_required_columns,  'too_many_column_errors': too_many_column_errors, 'Duplicate_Identifier': duplicate_identifier}


def find_max(fighter_1_record, fighter_2_record):
  if fighter_1_record[1] == None and fighter_2_record[1] != None and fighter_2_record[1] > 0:
    return fighter_2_record[0]
  if fighter_2_record[1] == None and fighter_1_record[1] != None and fighter_1_record[1] > 0:
    return fighter_1_record[0]
  if fighter_1_record[1] == None or fighter_2_record[1] == None:
    return None
  if  fighter_1_record[1] > fighter_2_record[1]:
    return fighter_1_record[0]
  elif fighter_2_record[1] > fighter_1_record[1]:
    return fighter_2_record[0]
  else:
    return None


def read_fight_file(file):
  row_id = 0
  new_users = {}
  error_rows = defaultdict(list)
  already_existing_users = {}
  duplicate_identifier = []

  copy_file = copy.copy(file)

  upload_file = copy_file

  if type(file) == str:
      file_to_read = upload_file

  elif isinstance(file, pd.DataFrame):
      file_to_read = upload_file

  else:

      file_to_read = upload_file

      if isinstance(upload_file, dict):
          file_to_read = upload_file
      else:
          file_to_read = upload_file.read().decode('utf-8')

  if not isinstance(file, pd.DataFrame):

      if isinstance(file_to_read, dict):
          data = file_to_read
      else:
          data = StringIO(file_to_read)
  else:
      data = file.astype(str)

  copy_of_csv = copy.deepcopy(data)

  buffered_users = {}

  index_of_manager = {}

  reader = csv.reader(copy_of_csv, delimiter=',')






  if isinstance(file, pd.DataFrame):

      new_headers = []

      for header in file_to_read.columns:

          stripped = header.replace('"', '')

          new_key = stripped.rstrip("\r").split(",")

          key = new_key[0]

          header = key
          new_headers.append(header)

      file_to_read.columns = new_headers

      columns = file_to_read.columns.values
  else:
      csv_copy = copy.deepcopy(data)
      if isinstance(data, dict):

          read_csv = pd.DataFrame(csv_copy)

          columns = list(read_csv.columns.values)
      else:
          string_with_escaped_chars = re.sub(
              '[^A-Za-z0-9]+', '', csv_copy.getvalue())

          if csv_copy.getvalue() == '\r\n':
              return {'Empty_File': 'empty file'}
          if string_with_escaped_chars == '':
              return {'Empty_File': 'empty file'}
          read_csv = pd.read_csv(csv_copy)

          columns = list(read_csv.columns.values)

  column_dict = dict()
  for index, value in enumerate(columns):
      stripped = value.replace('"', '')
      new_val = stripped.rstrip(";").split(",")
      val = new_val[0]
      column_dict[convert_snake_to_camel(val)] = val

  missing_required_columns = []

  too_many_column_errors = []
  columns = [x.lower() for x in columns]
  if 'fighter_name' not in columns:
      missing_required_columns.append('fighter_name')

  amount_of_users_to_upload = len(buffered_users)

  schema_list = []

  if isinstance(file, pd.DataFrame):
      read_csv = file_to_read
  if len(schema_list) > 0:
      schema = Schema(schema_list)
      schema_errors = schema.validate(
          read_csv, columns=schema.get_column_names())

      for error in schema_errors:
          error_rows[int(
              error.row) + 1].append({convert_snake_to_camel(error.column): error.message})
  print(read_csv, 'read_csv1')
  if isinstance(file, pd.DataFrame):
      file_to_read.fillna("", inplace=True)

  if isinstance(file, dict):
      iteration = pd.DataFrame.from_dict(file)
  elif isinstance(file, pd.DataFrame):
      iteration = file_to_read
  else:
      iteration = pd.read_csv(data, delimiter=';', quotechar='"', converters={
                              'follower_email': str, 'manager_email': str}, na_filter=False)
  iteration = iteration.rename(columns=lambda x: x.lower())
  iteration = iteration.rename(columns={'r_sig_str.': 'r_sig_str', 'b_sig_str.': 'b_sig_str', 'r_total_str.': 'r_total_str', 'b_total_str.': 'b_total_str'})
  data_to_iterate = iteration

  empty_users = 0
  for column, row_data in data_to_iterate.iterrows():

      try:

          row_id = row_id + 1

          r_fighter = row_data['r_fighter']
          r_fighter = r_fighter.lower()

          b_fighter = row_data['b_fighter']
          b_fighter = b_fighter.lower()

          r_kd = row_data['r_kd']

          b_kd = row_data['b_kd']

          r_sig_str = row_data['r_sig_str']

          b_sig_str = row_data['b_sig_str']

          r_sig_str_pct = row_data['r_sig_str_pct']

          b_sig_str_pct = row_data['b_sig_str_pct']

          r_total_str = row_data['r_total_str']

          b_total_str = row_data['b_total_str']

          r_td = row_data['r_td']

          b_td = row_data['b_td']

          r_td_pct = row_data['r_td_pct']

          b_td_pct = row_data['b_td_pct']

          r_sub_att = row_data['r_sub_att']

          b_sub_att = row_data['b_sub_att']

          r_rev = row_data['r_rev']

          b_rev = row_data['b_rev']

          r_ctrl = row_data['r_ctrl']

          b_ctrl = row_data['b_ctrl']

          r_head = row_data['r_head']

          b_head = row_data['b_head']

          r_body = row_data['r_body']

          b_body = row_data['b_body'] 

          r_leg = row_data['r_leg']

          b_leg = row_data['b_leg']

          r_distance = row_data['r_distance']

          b_distance = row_data['b_distance']

          r_clinch = row_data['r_clinch']

          b_clinch = row_data['b_clinch']

          r_ground = row_data['r_ground']

          b_ground = row_data['b_ground']

          win_by = row_data['win_by']

          last_round = row_data['last_round']

          last_round_time = row_data['last_round_time']

          format = row_data['format']

          referee = row_data['referee']

          date = row_data['date']
          date = datetime.strptime(date, '%B %d, %Y').date()

          location = row_data['location']

          fight_type = row_data['fight_type']

          winner = row_data['winner']
          r_fighter_name_parts = r_fighter.split()
          r_fighter_first_name = r_fighter_name_parts[0]
          if len(r_fighter_name_parts) > 1:
            if len(r_fighter_name_parts) > 2:
              r_fighter_last_name = " ".join(r_fighter_name_parts[1:])
            else:
              r_fighter_last_name = r_fighter_name_parts[1]
          else:
            r_fighter_last_name = None
          b_fighter_name_parts = b_fighter.split()
          b_fighter_first_name = b_fighter_name_parts[0]
          if len(b_fighter_name_parts) > 1:
            if len(b_fighter_name_parts) > 2:
              b_fighter_last_name = " ".join(b_fighter_name_parts[1:])
            else:
              b_fighter_last_name = b_fighter_name_parts[1]
          else:
            b_fighter_last_name = None
          try:
            
            fight = Fight.objects.create(
              r_kd=int(r_kd),
              b_kd=int(b_kd),
              r_sig_str=r_sig_str,
              b_sig_str=b_sig_str,
              r_sig_str_pct=int(r_sig_str_pct.replace('%', '')),
              b_sig_str_pct=int(b_sig_str_pct.replace('%', '')),
              r_total_str=r_total_str,
              b_total_str=b_total_str,
              r_td=r_td,
              b_td=b_td,
              r_td_pct=int(r_td_pct.replace('%', '')) if r_td_pct != '---' else None,
              b_td_pct=int(b_td_pct.replace('%', '')) if b_td_pct != '---' else None,
              r_sub_att=int(r_sub_att),
              b_sub_att=int(b_sub_att),
              r_rev=int(r_rev),
              b_rev=int(b_rev),
              r_ctrl=r_ctrl,
              b_ctrl=b_ctrl,
              r_head=r_head,
              b_head=b_head,
              r_body=r_body,
              b_body=b_body,
              r_leg=r_leg,
              b_leg=b_leg,
              r_distance=r_distance,
              b_distance=b_distance,
              r_clinch=r_clinch,
              b_clinch=b_clinch,
              r_ground=r_ground,
              b_ground=b_ground,
              win_by=win_by,
              last_round=int(last_round),
              last_round_time=last_round_time,
              format=format,
              referee=referee,
              date=date,
              location=location,
              fight_type=fight_type,
              winner=winner
              )
            
            red_fighter, created = Fighter.objects.get_or_create(first_name=r_fighter_first_name,
                                                        last_name=r_fighter_last_name)
            blue_fighter, created = Fighter.objects.get_or_create(first_name=b_fighter_first_name,
                                                        last_name=b_fighter_last_name)
              # Add fighters to the fight
            fight.red_fighter.set([red_fighter])
            fight.blue_fighter.set([blue_fighter])
            fight.save()
          except Exception as e:
            print(e, 'error creating fight')

      except Exception as e:
          print(e, 'error mapping row values')

  users_not_updating = amount_of_users_to_upload - \
      len(already_existing_users)

  if (len(error_rows) > 0):

      return {'Error': error_rows, 'Already_Existing_Users': already_existing_users, 'Column_Error': missing_required_columns, 'too_many_column_errors': too_many_column_errors, 'Duplicate_Identifier': duplicate_identifier}
  return {'New_Users': new_users, 'Already_Existing_Users': already_existing_users, 'Column_Error': missing_required_columns,  'too_many_column_errors': too_many_column_errors, 'Duplicate_Identifier': duplicate_identifier}

def get_fights_ending_in_ko():
  amount_of_fights_ending_in_ko = Fight.objects.filter(win_by='KO/TKO').count()
  return amount_of_fights_ending_in_ko


def extract_weight_class(fight_type):
    # Remove unwanted words and whitespace from the fight type
    clean_fight_type = re.sub(r'(UFC|Title)', '', fight_type).strip()
    clean_fight_type = re.sub(r'\s+', ' ', clean_fight_type)
    return clean_fight_type

def get_fighters_with_weight_class_change():
  fighters = Fighter.objects.all()
  fights = Fight.objects.filter(red_fighter__in=fighters) | Fight.objects.filter(blue_fighter__in=fighters)
  fights = fights.order_by('date')
  fighters_with_weight_class_change = []
  amount_that_lost = 0
  amount_that_won = 0
  amount_that_went_up_and_lost = 0
  amount_that_went_down_and_lost = 0
  amount_that_went_up_and_won = 0
  amount_that_went_down_and_won = 0
  amount_that_went_up = 0
  amount_that_went_down = 0
  amount_that_lost_and_went_down_and_lost_again = 0
  amount_that_lost_and_went_down_and_won = 0
  amount_that_won_and_went_down_and_won_again = 0
  amount_that_won_and_went_down_and_lost = 0
  for index, fight in enumerate(fights):
    red_fighter = fight.red_fighter.first()
    blue_fighter = fight.blue_fighter.first()
    fight_winner = fight.winner.lower()
    fight_loser = fight.loser.lower()

    red_fighter_next_fight = fights.filter((Q(red_fighter=red_fighter) | Q(blue_fighter=red_fighter)), date__gt=fight.date).exclude(pk=fight.pk).first()
    blue_fighter_next_fight = fights.filter((Q(red_fighter=blue_fighter) | Q(blue_fighter=blue_fighter)), date__gt=fight.date).exclude(pk=fight.pk).first()

    fight_lookup_number = WEIGHT_CLASSES[fight.fight_type] if fight.fight_type in WEIGHT_CLASSES else None

    if red_fighter_next_fight and extract_weight_class(red_fighter_next_fight.fight_type) != extract_weight_class(fight.fight_type):
      
      next_fight_lookup_number = WEIGHT_CLASSES[red_fighter_next_fight.fight_type] if red_fighter_next_fight.fight_type in WEIGHT_CLASSES else None

      red_fighter_gone_up_or_down = None
      if fight_lookup_number != None and next_fight_lookup_number != None:
        if next_fight_lookup_number > fight_lookup_number:
          red_fighter_gone_up_or_down = 'up'
          amount_that_went_up += 1
        if fight_lookup_number > next_fight_lookup_number:
          red_fighter_gone_up_or_down = 'down'
          amount_that_went_down += 1
      
        
      if fight.fight_type != 'Catch Weight Bout' and fight.fight_type != 'Open Weight Bout' and 'Tournament' not in fight.fight_type and red_fighter_next_fight.fight_type != 'Catch Weight Bout' and red_fighter_next_fight.fight_type != 'Open Weight Bout' and 'Tournament' not in red_fighter_next_fight.fight_type:
        next_fight_winner = red_fighter_next_fight.winner.lower()
        next_fight_loser = red_fighter_next_fight.loser.lower()
        red_fighter_name = f"{red_fighter.first_name} {red_fighter.last_name}".lower()
        did_red_fighter_win = True if red_fighter_name == next_fight_winner else False
        if did_red_fighter_win == False:
          amount_that_lost += 1

          if red_fighter_gone_up_or_down == 'up':
            amount_that_went_up_and_lost += 1
            
          if red_fighter_gone_up_or_down == 'down':
            amount_that_went_down_and_lost += 1
            if next_fight_loser == fight_loser:
              amount_that_lost_and_went_down_and_lost_again += 1
            if fight_winner == next_fight_loser:
              amount_that_won_and_went_down_and_lost += 1

        else:
          amount_that_won += 1
          if red_fighter_gone_up_or_down == 'up':
            amount_that_went_up_and_won += 1
            
          if red_fighter_gone_up_or_down == 'down':
            amount_that_went_down_and_won += 1
            if fight_loser == next_fight_winner:
              amount_that_lost_and_went_down_and_won += 1
            if fight_winner == next_fight_winner:
              amount_that_won_and_went_down_and_won_again += 1
        fighters_with_weight_class_change.append({'fighter': f"{red_fighter.first_name} {red_fighter.last_name}", 'first_weight': f"{fight.fight_type}", "next_weight": f"{red_fighter_next_fight.fight_type}", "up_down": red_fighter_gone_up_or_down, 'did_win': did_red_fighter_win })
      
    if blue_fighter_next_fight and extract_weight_class(blue_fighter_next_fight.fight_type) != extract_weight_class(fight.fight_type):

      next_fight_lookup_number = WEIGHT_CLASSES[blue_fighter_next_fight.fight_type] if blue_fighter_next_fight.fight_type in WEIGHT_CLASSES else None
      blue_fighter_gone_up_or_down = None
      if fight_lookup_number != None and next_fight_lookup_number != None:
        if next_fight_lookup_number > fight_lookup_number:
          blue_fighter_gone_up_or_down = 'up'
          amount_that_went_up += 1
        if fight_lookup_number > next_fight_lookup_number:
          blue_fighter_gone_up_or_down = 'down'
          amount_that_went_down += 1
      if fight.fight_type != 'Catch Weight Bout' and fight.fight_type != 'Open Weight Bout' and 'Tournament' not in fight.fight_type and blue_fighter_next_fight.fight_type != 'Catch Weight Bout' and blue_fighter_next_fight.fight_type != 'Open Weight Bout' and 'Tournament' not in blue_fighter_next_fight.fight_type:
        next_fight_winner = blue_fighter_next_fight.winner.lower()
        next_fight_loser = blue_fighter_next_fight.loser.lower()
        blue_fighter_name = f"{blue_fighter.first_name} {blue_fighter.last_name}".lower()
        did_blue_fighter_win = True if blue_fighter_name == next_fight_winner else False
        if did_blue_fighter_win == False:
          amount_that_lost += 1

          if blue_fighter_gone_up_or_down == 'up':
            amount_that_went_up_and_lost += 1
          if blue_fighter_gone_up_or_down == 'down':
            amount_that_went_down_and_lost += 1
            if next_fight_loser == fight_loser:
              amount_that_lost_and_went_down_and_lost_again += 1
            if fight_winner == next_fight_loser:
              amount_that_won_and_went_down_and_lost += 1
            
        else:
          amount_that_won += 1
          if blue_fighter_gone_up_or_down == 'up':
            amount_that_went_up_and_won += 1
          if blue_fighter_gone_up_or_down == 'down':
            amount_that_went_down_and_won += 1
            if fight_loser == next_fight_winner:
              amount_that_lost_and_went_down_and_won += 1
            if fight_winner == next_fight_winner:
              amount_that_won_and_went_down_and_won_again += 1
        fighters_with_weight_class_change.append({'fighter': f"{blue_fighter.first_name} {blue_fighter.last_name}", 'first_weight': f"{fight.fight_type}", "next_weight": f"{blue_fighter_next_fight.fight_type}", "up_down": blue_fighter_gone_up_or_down, 'did_win': did_blue_fighter_win  })
  file_path = "fighters_with_weight_class_change.json"
  with open(file_path, "w") as json_file:
    # Use the json.dump() function to write the list to the file
    json.dump(fighters_with_weight_class_change, json_file)
  amount_of_weight_changes = len(fighters_with_weight_class_change)

  data_dict = {
    'amount_of_weight_changes': amount_of_weight_changes,
    'amount_that_lost': amount_that_lost,
    'amount_that_won': amount_that_won,
    'amount_that_went_up': amount_that_went_up,
    'amount_that_went_up_and_lost': amount_that_went_up_and_lost,
    'amount_that_went_up_and_won': amount_that_went_up_and_won,
    'amount_that_went_down': amount_that_went_down,
    'amount_that_went_down_and_lost': amount_that_went_down_and_lost,
    'amount_that_went_down_and_won': amount_that_went_down_and_won,
    'amount_that_lost_and_went_down_and_lost_again': amount_that_lost_and_went_down_and_lost_again,
    'amount_that_lost_and_went_down_and_won': amount_that_lost_and_went_down_and_won,
    'amount_that_won_and_went_down_and_won_again': amount_that_won_and_went_down_and_won_again,
    'amount_that_won_and_went_down_and_lost': amount_that_won_and_went_down_and_lost
    }
  return data_dict


@api_view(['GET', 'POST'])
def update_loser_field(request):
    if request.method == 'GET':
        fights = Fight.objects.all()
        for fight in fights:
            red_fighter_names = [f"{fighter.first_name.lower()} {fighter.last_name.lower()}" for fighter in fight.red_fighter.all() if fighter.first_name and fighter.last_name]
            blue_fighter_names = [f"{fighter.first_name.lower()} {fighter.last_name.lower()}" for fighter in fight.blue_fighter.all() if fighter.first_name and fighter.last_name]

            winner = fight.winner
            loser = ''

            if winner:
                if isinstance(winner, Fighter):
                    winner_name = f"{winner.first_name.lower()} {winner.last_name.lower()}"
                else:
                    winner_name = str(winner).lower()

                if winner_name in red_fighter_names:
                    losers = [f"{fighter.first_name} {fighter.last_name}" for fighter in fight.blue_fighter.all() if fighter.first_name and fighter.last_name and f"{fighter.first_name.lower()} {fighter.last_name.lower()}" != winner_name]
                    loser = losers[0] if losers else ''
                elif winner_name in blue_fighter_names:
                    losers = [f"{fighter.first_name} {fighter.last_name}" for fighter in fight.red_fighter.all() if fighter.first_name and fighter.last_name and f"{fighter.first_name.lower()} {fighter.last_name.lower()}" != winner_name]
                    loser = losers[0] if losers else ''

            fight.loser = loser
            fight.save()

        return Response('Loser field updated successfully.')

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
