from rest_framework.views import APIView
from .models import Prediction
from rest_framework.response import Response
from ..helpers.helpers import add_fight_prediction_to_db, return_response, get_soup_from_url, get_all_fights_in_event, get_basic_fight_stats_from_event
from rest_framework import status
from rest_framework.decorators import api_view
from ..Fighter.models import Fighter
from ..Fights.models import Fight
from django.db.models import Q
from datetime import datetime

class PredictionList(APIView):
  def get(self, request):
    all_predictions = Prediction.objects.all()
    return Response(all_predictions)
  
  def post(self, request):
    data = request.data.get('fights')
    fight_date =  request.data.get('fight_date')
    added_prediction = add_fight_prediction_to_db(data, fight_date)
    return return_response({}, added_prediction, status.HTTP_200_OK)
    
  def delete(self, request):
    Prediction.objects.filter(red_fighter_id=False).delete()
  
  @api_view(['POST'])
  def bulk_insert_predictions(request):
    date = request.data.get('date')
      
    next_fight_card_already_in_db = Prediction.objects.filter(fight_date=date).exists()
    if next_fight_card_already_in_db == True:
      return return_response({}, 'Success! Fight event already in database', status.HTTP_200_OK)
    upcoming_events_url = 'http://ufcstats.com/statistics/events/upcoming'
    soup = get_soup_from_url(upcoming_events_url)

    second_a_tag = soup.find_all('a', href=lambda href: href and href.startswith("http://ufcstats.com/event-details/"))[0]

    # Print the href attribute of the found <a> tag
    if second_a_tag:
        next_event_url = second_a_tag['href']
        next_event_soup = get_soup_from_url(next_event_url)
        next_fight_date = next_event_soup.find('li', class_='b-list__box-list-item').text.strip().split('\n')[-1].strip()
        all_fights_in_event = get_all_fights_in_event(next_event_url)
        
        for fight in all_fights_in_event:
          basic_fight_stats = get_basic_fight_stats_from_event(fight['link'])
          data = [basic_fight_stats]
          added_prediction = add_fight_prediction_to_db(data, next_fight_date, fight['link'])
        return return_response({}, 'Success! Fight event added in database', status.HTTP_200_OK)
    else:
        print("No matching <a> tag found.")
        return return_response({}, 'Error! Fight event date not found', status.HTTP_200_OK)

  @api_view(['PUT'])
  def add_winners_to_predictions(request):
    date = request.data.get('date')
    url = 'http://ufcstats.com/statistics/events/completed?page=all'
    soup = get_soup_from_url(url)
    first_row = soup.find(class_='b-statistics__table-row_type_first')
    next_row = first_row.find_next_sibling('tr', class_='b-statistics__table-row')
    date_tag = next_row.find('span', class_='b-statistics__date')
    date = None
    if date_tag:
      date = date_tag.get_text(strip=True)
      input_format_str = "%B %d, %Y"
      output_format_str = "%Y-%m-%d"
      input_date = datetime.strptime(date, input_format_str)
      date = input_date.strftime(output_format_str)

    next_row = first_row.find_next_sibling(class_='b-statistics__table-row')
    link_element = next_row.find('a', class_='b-link b-link_style_black')
    href = link_element.get('href')
    event_soup = get_soup_from_url(href)
    fights = event_soup.select('.b-fight-details__table-body tr')
    for fight in fights:
      anchor_tag = fight.find('a', class_='b-flag_style_green')
      link = None
      winner = None
      if anchor_tag:
        link = anchor_tag.get('href')
      else:
        print("The desired <a> tag is not found.")
      if link is not None:
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
      if winner is not None:
        winner_fighter = None
        name_parts = winner.lower().split()
        first_name = name_parts[0]
        last_name = " ".join(name_parts[1:])
        winner_fighter_exists = Fighter.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).exists()
        if winner_fighter_exists == True:
          winner_fighter = Fighter.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).first()
        else:
          first_name = ' '.join(name_parts[:-1])
          last_name = name_parts[-1]
          winner_fighter = Fighter.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).first()
        db_fighter = Prediction.objects.filter(Q(blue_fighter=winner_fighter) | Q(red_fighter=winner_fighter), fight_date=date).first()
        if db_fighter is not None:
          prediction_winner = db_fighter.count_winner
          was_predicion_correct = prediction_winner == winner_fighter
          db_fighter.did_prediction_winner_win = was_predicion_correct
          db_fighter.fight_winner = winner_fighter
          db_fighter.save()
 
    return return_response({}, 'Success! Fight event winners saved', status.HTTP_200_OK)    
