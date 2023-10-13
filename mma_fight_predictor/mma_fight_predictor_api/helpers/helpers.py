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
from ..helpers.lookups import name_lookups
from django.db.models import F, Func
from .constants import WEIGHT_CLASSES, PREDICTION_LOOKUP, FIGHT_MATRIX_DATE_LOOKUP, WEIGHT_CLASS_LOOKUP, FIGHT_MATRIX_WEIGHT_CLASS_LOOKUP, FIGHT_WEIGHT_CLASS_LOOKUP_TO_WEIGHT
from pandas_schema import Column, Schema
from ..Fighter.models import Fighter
from ..Fights.models import Fight
from datetime import datetime
from django.db.models import F, Q
import json
from rest_framework.decorators import api_view
from rest_framework import status
from django.db.models import F, Count
import re
from django.db.models import Count, Case, When, FloatField, OuterRef,Value, CharField
from django.db.models.functions import Coalesce, Lower, Trim, Substr, Concat
from django.db import connection
from ..Prediction.models import Prediction
from datetime import datetime
import sys
import boto3
from botocore.exceptions import ClientError
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from ..Tokens.models import Token
from django.contrib.auth.models import User

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
        return fraction1[2]
    elif numerator1 < numerator2:
        return fraction2[2]
    else:
        return "Equal"


fraction1 = (8, 3)
fraction2 = (21, 3)


def get_fighters_fighting_style(name):
  try:
    name_parts = name.split()
    first_name = name_parts[0]
    if len(name_parts) > 1:
      if len(name_parts) > 2:
        last_name = " ".join(name_parts[1:])
      else:
        last_name = name_parts[1]
    else:
      last_name = None
    user_in_db = Fighter.objects.filter(first_name__iexact=first_name.lower() if first_name != None else first_name, last_name__iexact=last_name.lower() if last_name != None else last_name).exists()
    if user_in_db == True:
      fighter = Fighter.objects.filter(first_name__iexact=first_name.lower(), last_name__iexact=last_name.lower()).first()
      style = fighter.style
      if style is not None:
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
    best_fight_style = get_fight_style_with_best_win_percentage()
    try:
      Fighter.objects.filter(first_name=first_name.lower(), last_name=last_name.lower()).update(style=style)
    except Exception as e:
      print(e, 'error updating fighter style in database')
        
    return style

  except Exception as e:
    print(e, 'error getting style')
    
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
    user_in_db = Fighter.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).exists()
    if user_in_db == True:
      fighter = Fighter.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).first()
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
    
from django.db.models import Q
  
def get_fighter_1_opponent_list_from_db(fighter_name):
  fighter_name = fighter_name.lower()
  all_fighter_fights = Fight.objects.filter(Q(winner__iexact=fighter_name) | Q(loser__iexact=fighter_name))

  arr = []
  for item in all_fighter_fights:
    arr.append(f'{item.winner} {item.loser}')
  return arr
  
def get_fighters_record_again_each_opponents_fight_style(fighter_name,url):
  fighter_1_fights_table_soup = get_soup_from_url(url)
  fighter_1_table = fighter_1_fights_table_soup.find('table')
  fighter_1_dfs = pd.read_html(str(fighter_1_table))
  fighter_1_df = fighter_1_dfs[0]
  fighter_1_df = fighter_1_df.dropna()
  fighter_1_df.to_csv('filename.csv', index=False)
  fighter_1_opponent_list = get_fighter_1_opponent_list_from_db(fighter_name)
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

def get_fight_style_with_best_win_percentage(return_type=None):

      query_with_winner_style = """
      SELECT
      f.*,
      w.style AS winner_style
  FROM
      "mma_fight_predictor_api_fight" AS f
      INNER JOIN "mma_fight_predictor_api_fighter" AS w ON LOWER(TRIM(f.winner)) = LOWER(TRIM(CONCAT(w.first_name, ' ', w.last_name)))

      """
      result4query = """
      SELECT
      w.style AS winner_style,
      COUNT(*) AS winner_style_count
  FROM
      "mma_fight_predictor_api_fight" AS f
      INNER JOIN "mma_fight_predictor_api_fighter" AS w ON LOWER(TRIM(f.winner)) = LOWER(TRIM(CONCAT(w.first_name, ' ', w.last_name)))
  GROUP BY
      w.style
  """
      with connection.cursor() as cursor:
          cursor.execute(result4query)
          most_common_winning_styles = cursor.fetchall()
          ordered_data = sorted([x for x in most_common_winning_styles if x[0] is not None], key=lambda x: x[1], reverse=True)
      return ordered_data
        
@api_view(['GET'])
def get_fight_style_with_best_win_percentage_api_call(request):
    data = get_fight_style_with_best_win_percentage()
    return return_response(data, 'Success', status.HTTP_200_OK)

def get_last_name(fighter_name):
  words_after_first = fighter_name.split()[1:]
  lowercase_words = [word.lower() for word in words_after_first]
  joined_string = ' '.join(lowercase_words)
  return joined_string

def create_new_fighter(fighter_name, fight_link):
  new_fighter = Fighter()
  new_fighter.first_name = fighter_name.split()[0].lower()
  new_fighter.last_name = get_last_name(fighter_name)
  new_fighter.save()
  # Dan TO-DO get soup from fight_link and insert additional details to DB
  # Sometimes the row is empty so need to account for that here and in other places
  
def get_fighter(fighter_name):
  last_name=get_last_name(fighter_name)
  fighter = Fighter.objects.filter(first_name=fighter_name.split()[0].lower(), last_name=last_name).first()
  return fighter

def get_fighter_name(fighter):
  return f"{fighter.first_name} {fighter.last_name}"

def add_fight_prediction_to_db(data, fight_date, fight_link=None):
  items_that_have_winners = ['Wins/Losses/Draws', 'Reach', 'Strikes Landed per Min. (SLpM)', 'Striking Accuracy', 'Strikes Absorbed per Min. (SApM)', 'Defense', 'Takedowns Average/15 min.', 'Takedown Accuracy', 'Takedown Defense', 'Submission Average/15 min.']
  new_prediction = Prediction()
  
  for item in data:
    for key, value in item.items():
        if key == 'Tale of the tape':
          blue_fighter_name = next(iter(value))
          red_fighter_name = next(iter(value.keys() - {blue_fighter_name}))
          blue_fighter = get_fighter(blue_fighter_name)
          if blue_fighter is None:
            print('blue fighter doesnt exist')
            if fight_link is not None:
              print('creating new blue fighter')
              # Dan TO-DO insert fighter into db here
              create_new_fighter(blue_fighter_name, fight_link)
              blue_fighter = get_fighter(blue_fighter_name)
          red_fighter = get_fighter(red_fighter_name)
          if red_fighter is None:
            print('red fighter doesnt exist')
            if fight_link is not None:
              print('creating new red fighter')
              create_new_fighter(red_fighter_name, fight_link)
              red_fighter = get_fighter(red_fighter_name)
            # Dan TO-DO insert fighter into db here
          new_prediction.blue_fighter =blue_fighter
          new_prediction.red_fighter =red_fighter
          date_object = datetime.strptime(fight_date, "%B %d, %Y")
          formatted_date = date_object.strftime("%Y-%m-%d")
          already_in_db = Prediction.objects.filter(red_fighter=red_fighter, blue_fighter=blue_fighter, fight_date=formatted_date).exists()

          if already_in_db == False:
            new_prediction.fight_date = formatted_date
          else:
            return 'Fight already in database'
        if key in items_that_have_winners:
          lookup_val = PREDICTION_LOOKUP[key] 
          if 'winner' in value:
            winner = Fighter.objects.filter(first_name=value['winner'].split()[0].lower(), last_name=value['winner'].split()[-1].lower()).first()
            setattr(new_prediction, lookup_val, winner)
          if key == 'Wins/Losses/Draws':
            new_prediction.blue_fighter_wld_record = value[blue_fighter_name]
            new_prediction.red_fighter_wld_record = value[red_fighter_name]
        
          if key == 'Reach':
            new_prediction.blue_fighter_reach = value[blue_fighter_name]
            new_prediction.red_fighter_reach = value[red_fighter_name]
          if key == 'Strikes Landed per Min. (SLpM)':
            new_prediction.blue_fighter_slpm = value[blue_fighter_name]
            new_prediction.red_fighter_slpm = value[red_fighter_name]
            
          if key == 'Striking Accuracy':
            new_prediction.blue_fighter_striking_accuracy = value[blue_fighter_name]
            new_prediction.red_fighter_striking_accuracy = value[red_fighter_name]
            
          if key == 'Strikes Absorbed per Min. (SApM)':
            new_prediction.blue_fighter_sapm= value[blue_fighter_name]
            new_prediction.red_fighter_sapm= value[red_fighter_name]
            
            
          if key == 'Defense':
            new_prediction.blue_fighter_defense= value[blue_fighter_name]
            new_prediction.red_fighter_defense= value[red_fighter_name]
            
          if key == 'Takedowns Average/15 min.':
            new_prediction.blue_fighter_takedown_average_15_min= value[blue_fighter_name]
            new_prediction.red_fighter_takedown_average_15_min= value[red_fighter_name]
            
          if key == 'Takedown Accuracy':
            new_prediction.blue_fighter_takedown_accuracy= value[blue_fighter_name]
            new_prediction.red_fighter_takedown_accuracy= value[red_fighter_name]
            
          if key == 'Takedown Defense':
            new_prediction.blue_fighter_takedown_defense= value[blue_fighter_name]
            new_prediction.red_fighter_takedown_defense= value[red_fighter_name]
            
          if key == 'Submission Average/15 min.':
            new_prediction.blue_fighter_submission_average_15_min_average= value[blue_fighter_name]
            new_prediction.red_fighter_submission_average_15_min_average= value[red_fighter_name]
            
            
        if key == 'count':
          fighter_name_with_highest_count = max(value, key=value.get)
          fighter_with_highest_count = get_fighter(fighter_name_with_highest_count)
          new_prediction.count_winner = fighter_with_highest_count
          
          new_prediction.blue_fighter_count = value[blue_fighter_name]
          new_prediction.red_fighter_count = value[red_fighter_name]
        
          

    new_prediction.save()
    return 'New fight added'


def get_all_fights_in_event(url):
    if 'link' in url:
      url = url['link']
    soup = get_soup_from_url(url)
    
    date_element = soup.find('li', class_='b-list__box-list-item').text.strip().split('\n')[-1].strip()    
    fights_html = soup.find_all('tr', {'class': 'js-fight-details-click'})
    
    fights_data = []
    for item in fights_html:
      link = item.get("data-link")
      fighter_names = item.find_all('td', {'class': 'b-fight-details__table-col l-page_align_left'})[0].find_all('a')
      fighter_1_name = fighter_names[0].get_text(strip=True)
      fighter_2_name = fighter_names[1].get_text(strip=True)
      weight_class = item.find_all('td', {'class': 'b-fight-details__table-col l-page_align_left'})[1].get_text(strip=True)
      fight_data = {'fighter_1': fighter_1_name, 'fighter_2': fighter_2_name, 'weight_class': weight_class, 'link': link, 'date': date_element}
      fights_data.append(fight_data)
    return fights_data

def get_basic_fight_stats_from_event(url):
  soup = get_soup_from_url(url)

  table = soup.find('table')

  dfs = pd.read_html(str(table))
  df = dfs[0]
  df = df.dropna()
  first_column_name = df.columns[0]
  renamed_df = df.rename(columns={first_column_name: 'Statistic'})

  result = {}
  
  column_names = renamed_df.iloc[:, 0].tolist()
  fighters = renamed_df.iloc[:, 1:].columns.tolist()
  fighter_1 = fighters[0]
  fighter_2 = fighters[1]
  
  winner_dict = {fighter_1: 0, fighter_2: 0}

  for col in column_names:
      col_data = renamed_df.loc[renamed_df['Statistic'] == col].iloc[:, 1:].T.reset_index()
      col_data.columns = ['Fighter', col]

      col_data.set_index('Fighter', inplace=True)
      col_data.index.name = None

      # Convert the column data to a dictionary
      col_dict = col_data.to_dict()[col]
      
      # TO-DO change this to take into account this might not be correct if 10-2 fighter facing 1-0 as 1-0 would win this but has had way less fights===less experience
      if col == 'Wins/Losses/Draws':
        fighter_1_record = col_dict[fighter_1]
        fighter_2_record = col_dict[fighter_2]
        figter_1_wins, fighter_1_losses, fighter_1_draws = fighter_1_record.split("-")

        figter_1_wins = int(figter_1_wins.split()[0])
        fighter_1_losses = int(fighter_1_losses.split()[0])
        fighter_1_draws = int(fighter_1_draws.split()[0])
        
        figter_2_wins, fighter_2_losses, fighter_2_draws = fighter_2_record.split("-")

        figter_2_wins = int(figter_2_wins.split()[0])
        fighter_2_losses = int(fighter_2_losses.split()[0])
        fighter_2_draws = int(fighter_2_draws.split()[0])
        
        compared_wins_winner = compare_fractions((figter_1_wins, fighter_1_losses, fighter_1), (figter_2_wins, fighter_2_losses, fighter_2))
        if compared_wins_winner != 'Equal':
          col_dict['winner'] = compared_wins_winner
          winner_dict[compared_wins_winner] +=1

      if col == 'Reach':
        if col_dict[fighter_1] > col_dict[fighter_2]:
          col_dict['winner'] = fighter_1
          winner_dict[fighter_1] +=1
        elif col_dict[fighter_2] > col_dict[fighter_1]:
          col_dict['winner'] = fighter_2
          winner_dict[fighter_2] +=1
        else:
          print('both fighters have the same reach')
      
      if col == 'Strikes Landed per Min. (SLpM)':
        if col_dict[fighter_1] > col_dict[fighter_2]:
          col_dict['winner'] = fighter_1
          winner_dict[fighter_1] +=1
        elif col_dict[fighter_2] > col_dict[fighter_1]:
          col_dict['winner'] = fighter_2
          winner_dict[fighter_2] +=1
        else:
          print('both fighters have the same significant strikes lander per min')

      if col == 'Striking Accuracy':
        fighter_1_striking_accuracy_num = float(col_dict[fighter_1].strip("%"))
        fighter_2_striking_accuracy_num = float(col_dict[fighter_2].strip("%"))
        if fighter_1_striking_accuracy_num > fighter_2_striking_accuracy_num:
          col_dict['winner'] = fighter_1
          winner_dict[fighter_1] +=1
        elif fighter_2_striking_accuracy_num > fighter_1_striking_accuracy_num:
            col_dict['winner'] = fighter_2
            winner_dict[fighter_2] +=1
        else:
          print('both fighters have the same striking accuracy')
          
      if col == 'Strikes Absorbed per Min. (SApM)':
        if col_dict[fighter_1] > col_dict[fighter_2]:
          col_dict['winner'] = fighter_2
          winner_dict[fighter_2] +=1
        elif col_dict[fighter_2] > col_dict[fighter_1]:
          col_dict['winner'] = fighter_1
          winner_dict[fighter_1] +=1
        else:
          print('both fighters have the same Strikes Absorbed per Min')
      
      if col == 'Defense':
        fighter_1_striking_defence_num = float(col_dict[fighter_1].strip("%"))
        fighter_2_striking_defence_num = float(col_dict[fighter_2].strip("%"))
        if fighter_1_striking_defence_num > fighter_2_striking_defence_num:
          col_dict['winner'] = fighter_1
          winner_dict[fighter_1] +=1
        elif fighter_2_striking_defence_num > fighter_1_striking_defence_num:
            col_dict['winner'] = fighter_2
            winner_dict[fighter_2] +=1
        else:
          print('both fighters have the same defence')
      
      if col == 'Takedowns Average/15 min.':
        if col_dict[fighter_1] > col_dict[fighter_2]:
          col_dict['winner'] = fighter_1
          winner_dict[fighter_1] +=1
        elif col_dict[fighter_2] > col_dict[fighter_1]:
          col_dict['winner'] = fighter_2
          winner_dict[fighter_2] +=1
        else:
          print('both fighters have the same takedowns average/15 min')
      
      if col == 'Takedown Accuracy':
        if col_dict[fighter_1] > col_dict[fighter_2]:
          col_dict['winner'] = fighter_1
          winner_dict[fighter_1] +=1
        elif col_dict[fighter_2] > col_dict[fighter_1]:
          col_dict['winner'] = fighter_2
          winner_dict[fighter_2] +=1
        else:
          print('both fighters have the same takedowns accuracy')
      
      if col == 'Takedown Defense':
        if col_dict[fighter_1] > col_dict[fighter_2]:
          col_dict['winner'] = fighter_1
          winner_dict[fighter_1] +=1
        elif col_dict[fighter_2] > col_dict[fighter_1]:
          col_dict['winner'] = fighter_2
          winner_dict[fighter_2] +=1
        else:
          print('both fighters have the same takedowns accuracy')
      
      if col == 'Submission Average/15 min.':
        if col_dict[fighter_1] > col_dict[fighter_2]:
          col_dict['winner'] = fighter_1
          winner_dict[fighter_1] +=1
        elif col_dict[fighter_2] > col_dict[fighter_1]:
          col_dict['winner'] = fighter_2
          winner_dict[fighter_2] +=1
        else:
          print('both fighters have the same submission average/15 min.')

      if col == 'Most recent fights (Newest First)':
        print(col_dict, 'col_dict')
      result[col] = col_dict

  result['count'] = winner_dict
  if winner_dict[fighter_1] > winner_dict[fighter_2]:
    result['winner'] = fighter_1
  elif winner_dict[fighter_2] > winner_dict[fighter_1]:
    result['winner'] = fighter_2
  else:
    result['winner'] = 'Draw'
  return result

def get_fighter_previous_opponents(fighter,only_wins=False):
  fights = Fight.objects.filter(Q(red_fighter=fighter) | Q(blue_fighter=fighter))
  opponents = []
  for fight in fights:
        if fight.red_fighter.filter(id=fighter.id).exists():
            opponent = fight.blue_fighter.first()
            if only_wins == True:
              name = get_fighter_name(fighter)
              fight_winner = fight.winner.lower()
              if fight_winner == name:
                opponents.append({'name': f"{opponent.first_name} {opponent.last_name}", 'date': fight.date, 'weight_class': fight.fight_type})
            else:
              opponents.append({'name': f"{opponent.first_name} {opponent.last_name}", 'date': fight.date, 'weight_class': fight.fight_type})
        else:
            opponent = fight.red_fighter.first()
            if only_wins == True:
              name = get_fighter_name(fighter)
              fight_winner = fight.winner.lower()
              if fight_winner == name:
                opponents.append({'name': f"{opponent.first_name} {opponent.last_name}", 'date': fight.date, 'weight_class': fight.fight_type})
            else:
              opponents.append({'name': f"{opponent.first_name} {opponent.last_name}", 'date': fight.date, 'weight_class': fight.fight_type})
  return opponents


def find_closest_date(target_date):
    target_date = target_date.strftime('%m/%d/%Y')
    closest_dates = [date for date in FIGHT_MATRIX_DATE_LOOKUP.values() if datetime.strptime(date, '%m/%d/%Y') < datetime.strptime(target_date, '%m/%d/%Y')]
    if closest_dates:
        closest_date = max(closest_dates, key=lambda x: datetime.strptime(x, '%m/%d/%Y'))
        return datetime.strptime(closest_date, '%m/%d/%Y').date()
    else:
        return None

def get_fighters_wins_if_in_top_10(fighter_name):
    fighter = get_fighter(fighter_name)
    all_fighter_previous_opponents = get_fighter_previous_opponents(fighter,only_wins=True)
    opps = []
    for item in all_fighter_previous_opponents:
      opponent = get_fighter(item['name'])
      opponent_weight = opponent.weight
      weight_class_fight_was_at = FIGHT_WEIGHT_CLASS_LOOKUP_TO_WEIGHT[item['weight_class']]

      closest_date = find_closest_date(item['date'])
      formatted_closest_date = closest_date.strftime('%m/%d/%Y')
      matrix_date_key = next(key for key, value in FIGHT_MATRIX_DATE_LOOKUP.items() if value == formatted_closest_date)

      opponent_weight_lookup = WEIGHT_CLASS_LOOKUP[opponent_weight]

      matrix_weight_class_value = FIGHT_MATRIX_WEIGHT_CLASS_LOOKUP[weight_class_fight_was_at]

    # https://www.fightmatrix.com/historical-mma-rankings/generated-historical-rankings/?Issue=69&Division=4

      url = f"https://www.fightmatrix.com/historical-mma-rankings/generated-historical-rankings/?Issue={matrix_date_key}&Division={matrix_weight_class_value}"
      soup = get_soup_from_url(url)
      table = soup.find('table', {'class': 'tblRank'} )
      a_tags = table.find_all('a', href=lambda href: href and href.startswith('/fighter-profile/'))
      for a_tag in a_tags:
          tr_tag = a_tag.find_parent('tr')
          opponent_name = tr_tag.find('strong').text.strip().lower()
          opponent_ranking = tr_tag.find('td', {'class', 'tdRank'})
          if opponent_ranking != None:
            opponent_ranking = opponent_ranking.text.strip()
          if item['name'] == opponent_name:
            opps.append({'opponent_name': opponent_name,'ranking': opponent_ranking})
    filtered_opps = filter(lambda x: x['ranking'] == 'c' or (x['ranking'] is not None and int(x['ranking']) <= 10), opps)
    opps_that_were_champ_or_top_ten = list(filtered_opps)
    return opps_that_were_champ_or_top_ten

@api_view(['GET'])
def get_test_price_id(request):
  price = request.GET.get('price')
  if price == '40':
    secret_name = "test-mma-fourty-price-id"
  else:
    secret_name = "test-mma-five-price-id"
  region_name = "eu-west-2"

  # Create a Secrets Manager client
  session = boto3.session.Session()
  client = session.client(
      service_name='secretsmanager',
      region_name=region_name
  )

  try:
      get_secret_value_response = client.get_secret_value(
          SecretId=secret_name
      )
  except ClientError as e:
      # For a list of exceptions thrown, see
      # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
      raise e

  # Decrypts secret using the associated KMS key.
  secret = get_secret_value_response['SecretString']
  secret = json.loads(secret)
  if price == '40':
    price_id = secret['test-mma-fourty-price-id']
  else:
    price_id = secret['test-mma-payment-five-price-id']
  return Response({'price_id': price_id})

@api_view(['GET'])
def get_test_publishing_id(request):
  secret_name = "test-mma-five-publishing-id"
  region_name = "eu-west-2"

  # Create a Secrets Manager client
  session = boto3.session.Session()
  client = session.client(
      service_name='secretsmanager',
      region_name=region_name
  )

  try:
      get_secret_value_response = client.get_secret_value(
          SecretId=secret_name
      )
  except ClientError as e:
      # For a list of exceptions thrown, see
      # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
      raise e

  # Decrypts secret using the associated KMS key.
  secret = get_secret_value_response['SecretString']
  secret = json.loads(secret)
  publishing_id = secret['test-mma-five-publishing-id']
  return Response({'publishing_id':publishing_id})

def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

def has_length(input):
  if len(input) > 0:
    return True
  return False


@api_view(['POST'])
def save_tokens(request):
  try:
    refresh = request.data.get('refresh')
    access = request.data.get('access')
    email = request.data.get('email')
    user = User.objects.filter(email=email).first()
    if user is None:
      return return_response({}, 'Error! Unable to find user.', status.HTTP_400_BAD_REQUEST)
    token = Token.objects.filter(user=user)
    if token.exists():
      token_obj = token.first()
      token_obj.access_token = access
      token_obj.refresh_token = refresh
      token_obj.save()
    else:
      Token.objects.create(user=user, access_token=access, refresh_token=refresh)
    return return_response({}, 'Success!', status.HTTP_201_CREATED)
  except Exception as e:
    return return_response({}, 'Error! Unable to save token', status.HTTP_500_INTERNAL_SERVER_ERROR)  
  

@api_view(['POST'])
def get_username_from_email(request):
  email = request.data.get('email')
  username = User.objects.filter(email=email).first()
  if username is None:
    return return_response(username, 'Error!', status.HTTP_400_BAD_REQUEST)
  return return_response(username.username, 'Success!', status.HTTP_200_OK)

def get_upcoming_events():
    url = 'http://ufcstats.com/statistics/events/upcoming?page=all'
    soup = get_soup_from_url(url)
    event_name = soup.find_all('a', {'class': 'b-link b-link_style_black'})
    events = ({'name': item.get_text(strip=True), 'link': item.get("href")} for item in event_name)
    return events

# Below iterates over list/dict to change all words to lowercase
def recursive_lowercase(obj):
    if isinstance(obj, dict):
        return {key.lower(): recursive_lowercase(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [recursive_lowercase(item) for item in obj]
    elif isinstance(obj, str):
        return obj.lower()
    else:
        return obj
      
# This only works for names longer than 1      
def get_fighters_odds(odds_data, fighter_one, fighter_two, main):
  fighter_odds = {fighter_one: [], fighter_two: []}
  fighter_counts = {fighter_one: 0, fighter_two: 0}
  if main == 'red':
    bookmakers_odds = odds_data[fighter_one]['bookmakers']
  else:

    if fighter_two in odds_data:
      bookmakers_odds = odds_data[fighter_two]['bookmakers']
    else:
      fighter_two_first = fighter_two.split()[0]
      for item in name_lookups[fighter_two_first]:
        odds_key = next(iter(odds_data)) 
        if odds_key.split()[0] == item:
          name = f'{item} {fighter_two.split()[1]}'
          bookmakers_odds = odds_data[name]['bookmakers']
  bookmakers_odds_lowercase = recursive_lowercase(bookmakers_odds)
  
  # Loop through the bookmakers' odds and extract odds for each fighter
  for bookmaker in bookmakers_odds_lowercase:
      for market in bookmaker['markets']:
          for outcome in market['outcomes']:
              fighter_name = outcome['name']
              if fighter_name not in fighter_odds:
                first_name = fighter_name.split()[0]
                last_name = fighter_name.split()[1]
                if first_name in name_lookups:
                  for name in name_lookups[first_name]:
                    if f'{name} {last_name}' in fighter_odds:
                      fighter_name = f'{name} {last_name}'
              fighter_price = outcome['price']
              if fighter_name in fighter_odds:
                fighter_odds[fighter_name].append(fighter_price)
                fighter_counts[fighter_name] += 1

  average_odds = {}
  for fighter_name, odds_list in fighter_odds.items():
      total_odds = sum(odds_list)
      average_odds[fighter_name] = total_odds / fighter_counts[fighter_name]

  arr = []
  for fighter_name, average_odd in average_odds.items():
      arr.append(f'{fighter_name}: {average_odd:.2f}')
  return arr
