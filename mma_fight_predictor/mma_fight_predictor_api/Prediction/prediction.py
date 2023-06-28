from rest_framework.views import APIView
from .models import Prediction
from rest_framework.response import Response
from ..helpers.helpers import add_fight_prediction_to_db, return_response
from rest_framework import status

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

