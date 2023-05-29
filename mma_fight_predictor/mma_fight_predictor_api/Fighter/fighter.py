from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import FighterSerializer
from .models import Fighter
from ..Fights.models import Fight
from ..helpers.helpers import read_fighters_file, read_fight_file, get_fights_ending_in_ko,get_fighters_with_weight_class_change
from ..helpers.constants import WEIGHT_CLASSES
from rest_framework.decorators import api_view
import copy
import json
import pandas as pd
import numpy as np
from django.db.models import Q
import datetime
import re

class FighterList(APIView):
    def get(self, request):
        fighters = Fighter.objects.all()
        serializer = FighterSerializer(fighters, many=True)
        return Response(serializer.data)
      
    @api_view(['POST'])
    def read_fighters_csv(request):
      print('reading csv')
      if 'files' in request.FILES:
          request_file = copy.deepcopy(request.FILES['files'])

          types = request.FILES['files']
      else:
          file_dict = dict(zip(json.loads(request.POST['files']).keys(
          ), json.loads(request.POST['files']).values()))

          files_to_send = file_dict

          request_file = copy.deepcopy(files_to_send)
          types = files_to_send

      if isinstance(types, str):

          new_df = pd.DataFrame.from_dict(json.loads(request_file))
          new_df.dropna(how="all", inplace=True)
          new_df.replace(np.nan, '', inplace=True)
          new_df.insert(0, 'id', range(0, 0 + len(new_df)))

      if 'files' in request.FILES:
          read_file = read_fighters_file(request.FILES['files'])
      else:
          if isinstance(types, str):
              read_file = read_fighters_file(new_df)
          else:
              read_file = read_fighters_file(files_to_send)

    @api_view(['POST'])
    def read_fight_csv(request):
      print('reading fight csv')
      if 'files' in request.FILES:
          request_file = copy.deepcopy(request.FILES['files'])

          types = request.FILES['files']
      else:
          file_dict = dict(zip(json.loads(request.POST['files']).keys(
          ), json.loads(request.POST['files']).values()))

          files_to_send = file_dict

          request_file = copy.deepcopy(files_to_send)
          types = files_to_send

      if isinstance(types, str):

          new_df = pd.DataFrame.from_dict(json.loads(request_file))
          new_df.dropna(how="all", inplace=True)
          new_df.replace(np.nan, '', inplace=True)
          new_df.insert(0, 'id', range(0, 0 + len(new_df)))

      if 'files' in request.FILES:
          read_file = read_fight_file(request.FILES['files'])
      else:
          if isinstance(types, str):
              read_file = read_fight_file(new_df)
          else:
              read_file = read_fight_file(files_to_send)
      
    @api_view(['GET'])
    def test_many(request):
      fighter = Fighter.objects.filter(first_name='conor', last_name='mcgregor').first()
      many = Fight.objects.filter(red_fighter=fighter.id)
      
    @api_view(['GET'])
    def get_stats_from_db(request):
      fights_ending_in_ko = get_fights_ending_in_ko()
      print(fights_ending_in_ko, 'fights_ending_in_ko')
      fights_that_ended_in_ko = Fight.objects.filter(win_by='KO/TKO')
      
      losers_that_lost_their_next_fight = 0
      losers_that_lost_their_next_fight_by_ko = 0
      for fight in fights_that_ended_in_ko:
        fight_type = fight.fight_type
        clean_fight_type = re.sub(r'\b(UFC|Title)\b', '', fight_type).strip()
        clean_fight_type = re.sub(r'\s+', ' ', clean_fight_type)

        fight_type_point = None
        if clean_fight_type != 'Catch Weight Bout':
          try:
            fight_type_point = WEIGHT_CLASSES[clean_fight_type]
          except:
            print('invalid fight_type')

        red_first = fight.red_fighter.first()
        blue_first = fight.blue_fighter.first()
        fight_winner = fight.winner
        fight_winner = fight_winner.lower()
        red_first_name = None
        red_last_name = None
        blue_first_name = None
        blue_last_name = None
        if red_first.first_name != None:
          red_first_name = red_first.first_name
        if red_first.last_name != None:
          red_last_name = red_first.last_name
        if blue_first.first_name != None:
          blue_first_name = blue_first.first_name
        if blue_first.last_name != None:
          blue_last_name = blue_first.last_name
        
        winning_color = None
        red_full_name = f"{red_first_name} {red_last_name}"
        blue_full_name = f"{blue_first_name} {blue_last_name}"
        if fight_winner == red_full_name:
          winning_color = 'red'
        if fight_winner == blue_full_name:
          winning_color = 'blue'

        fight_date = fight.date
        losers_next_fight = None
        loser_color = None
        if winning_color == 'blue':
          loser = 'red'
          losers_next_fight = Fight.objects.filter(Q(red_fighter__first_name=red_first_name, red_fighter__last_name=red_last_name) | Q(blue_fighter__first_name=red_first_name, blue_fighter__last_name=red_last_name), date__gt=fight_date).first()
        
        if winning_color == 'red':
          losers_next_fight = Fight.objects.filter(Q(red_fighter__first_name=blue_first_name, red_fighter__last_name=blue_last_name) | Q(blue_fighter__first_name=blue_first_name, blue_fighter__last_name=blue_last_name), date__gt=fight_date).first()
          loser = 'blue'
        
        losers_next_fight_winner = losers_next_fight.winner if losers_next_fight != None else None

        if loser == 'blue':
          if losers_next_fight_winner != None:
            if losers_next_fight_winner.lower() != blue_full_name:
              losers_that_lost_their_next_fight += 1
              if losers_next_fight.win_by == 'KO/TKO':
                losers_that_lost_their_next_fight_by_ko += 1
        if loser == 'red':
          if losers_next_fight_winner != None:
            if losers_next_fight_winner.lower() != red_full_name:
              losers_that_lost_their_next_fight += 1
              if losers_next_fight.win_by == 'KO/TKO':
                losers_that_lost_their_next_fight_by_ko += 1
          print(losers_next_fight_winner, 'losers_next_fight_winner111')

      print(fights_that_ended_in_ko.count(), 'fights_that_ended_in_koamount')
      print(losers_that_lost_their_next_fight, 'losers_that_lost_their_next_fight123')
      print(losers_that_lost_their_next_fight_by_ko, 'losers_that_lost_their_next_fight_by_ko123')
      
      percentage_of_fighters_that_lost_their_next_fight = losers_that_lost_their_next_fight / fights_that_ended_in_ko.count()
      percentage_of_fighters_that_lost_their_next_fight_by_ko = losers_that_lost_their_next_fight_by_ko / fights_that_ended_in_ko.count()
      print(percentage_of_fighters_that_lost_their_next_fight, 'percentage_of_fighters_that_lost_their_next_fight1§')
      print(percentage_of_fighters_that_lost_their_next_fight_by_ko, 'percentage_of_fighters_that_lost_their_next_fight_by_ko11')
            
      
      fighters_with_weight_class_change_stats = get_fighters_with_weight_class_change()
      print(fighters_with_weight_class_change_stats, 'fighters_with_weight_class_change_stats')  
      return Response(fighters_with_weight_class_change_stats)
