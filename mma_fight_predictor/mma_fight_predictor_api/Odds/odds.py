import requests
from rest_framework.decorators import api_view
from ..helpers.helpers import get_upcoming_events, get_fighters_odds, return_response
from ..Prediction.models import Prediction
from datetime import datetime, timedelta
from ..helpers.lookups import name_lookups
from ..Fighter.models import Fighter
import copy
import json
from django.db.models import Q
from rest_framework import status
from dotenv import load_dotenv
import os

load_dotenv()
@api_view(['GET'])
def insert_odds_for_next_fight_event_in_db(request):
  ODDS_API_API_KEY = os.getenv('ODDS_API_API_KEY')
  sports_response = requests.get(
    'https://api.the-odds-api.com/v4/sports/mma_mixed_martial_arts/odds/?apiKey=0eee2115e38c9c17e15c69aec935d3eb&regions=us&markets=h2h', 
    params={
        'api_key': ODDS_API_API_KEY
    }
  )
  if sports_response.status_code != 200:
    print('invalid response')
  else:
    res = sports_response.json()
    file_path = 'res.json'

    # Write the JSON response to the file
    with open(file_path, 'w') as file:
        json.dump(res, file)

    next_event_prediction = Prediction.objects.last()
    next_event_date = next_event_prediction.fight_date
    start_date = datetime.strptime(str(next_event_date), '%Y-%m-%d')

    # Calculate the date one day after 'start_date'
    next_date = start_date + timedelta(days=1)
    day_after_next_event_date = next_date.strftime('%Y-%m-%d')

    filtered = filter(lambda item: item['commence_time'][:item['commence_time'].index("T")] in (str(next_event_date), str(day_after_next_event_date)), res)
    fights_on_next_event_date = list(filtered)
    new_list = []

    for item in fights_on_next_event_date:
        new_dict = {item['home_team'].lower(): item}
        new_list.append(new_dict)
    
    all_predicted_fights_on_fight_night = Prediction.objects.filter(fight_date=next_event_date)
    found = []

# # GET /v4/sports/{sport}/odds/?apiKey={apiKey}&regions={regions}&markets={markets}
# # Potential Winnings = Stake (in this case, £1) * Odds
    new_arr = []

    for item in all_predicted_fights_on_fight_night:
      red_fighter = item.red_fighter
      blue_fighter = item.blue_fighter
      red_fighter_name = red_fighter.get_full_name()
      blue_fighter_name = blue_fighter.get_full_name()
      
      for pred in new_list:
        key = next(iter(pred)) 
        if len(red_fighter_name.split()) > 1:
          if red_fighter_name.split()[1] == key.split()[1]:
            new_arr.append(red_fighter_name)
            odds = get_fighters_odds(pred, red_fighter_name, blue_fighter_name, 'red')
            found.append(odds)
        if len(blue_fighter_name.split()) > 1:
          if blue_fighter_name.split()[1] == key.split()[1]:
            new_arr.append(blue_fighter_name)
            odds = get_fighters_odds(pred, red_fighter_name, blue_fighter_name, 'blue')
            found.append(odds)
    
    # This only works for names that have 1 first and 1 last
    for item in found:
      if item is not None:
        red_first = item[0].split()[0]
        red_last = item[0].split()[1]
        red_last = red_last.replace(":", "")
        
        red_fighter = Fighter.objects.filter(
          Q(first_name__iexact=red_first) &
          Q(last_name__iexact=red_last)
        ).first()
        if red_fighter is not None:
          red_odds = item[0].split(':')[1].strip()
          blue_odds = item[1].split(':')[1].strip()
          prediction = Prediction.objects.filter(fight_date=next_event_date, red_fighter=red_fighter).first()
          prediction.red_fighter_betting_odds = red_odds
          prediction.blue_fighter_betting_odds = blue_odds
          prediction.save()
        
  return return_response({}, 'Success! Odds for next fight added', status.HTTP_200_OK)      
            
      
