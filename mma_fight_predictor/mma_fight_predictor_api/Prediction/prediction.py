from rest_framework.views import APIView
from .models import Prediction
from rest_framework.response import Response
from ..helpers.helpers import add_fight_prediction_to_db, return_response, get_soup_from_url, get_all_fights_in_event, get_basic_fight_stats_from_event
from rest_framework import status
from rest_framework.decorators import api_view

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
    # all_preds = Prediction.objects.all()
    # all_preds.delete()
    # Prediction.objects.all().delete()

    # Prediction.objects.all().delete()
    # predictions = Prediction.objects.all()

    # # Iterate over the Prediction objects and delete them
    # for prediction in predictions:
    #     # Delete the Prediction object, which will also delete related records due to the foreign key constraints
    #     prediction.delete()
    Prediction.objects.filter(red_fighter_id=False).delete()
  
  @api_view(['POST'])
  def bulk_insert_predictions(request):
    date = request.data.get('date')
    next_fight_card_already_in_db = Prediction.objects.filter(fight_date=date).exists()
    if next_fight_card_already_in_db == True:
      return return_response({}, 'Success! Fight event already in database', status.HTTP_200_OK)
    upcoming_events_url = 'http://ufcstats.com/statistics/events/upcoming'
    soup = get_soup_from_url(upcoming_events_url)

    second_a_tag = soup.find_all('a', href=lambda href: href and href.startswith("http://ufcstats.com/event-details/"))[1]

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

