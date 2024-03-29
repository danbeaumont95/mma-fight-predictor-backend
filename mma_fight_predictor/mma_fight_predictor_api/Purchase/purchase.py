from .models import Purchase
# from ..User.models import User
from django.contrib.auth.models import User
from rest_framework.views import APIView
from ..helpers.helpers import return_response
from rest_framework import status
from datetime import date
from ..Tokens.models import Token

class PurchaseList(APIView):
  
  def put(self, request):
    event_name = request.data.get('event_name')
    access = request.data.get('access')
    token = Token.objects.filter(access_token=access).first()
    if token is None:
      return return_response({}, 'Error! User does not exist.', status.HTTP_400_BAD_REQUEST)
    user = token.user
    purchase_exists = Purchase.objects.filter(user=user, event_name=event_name).exists()
    if purchase_exists == True:
      return return_response(True, 'Success', status.HTTP_200_OK)
    else:
      return return_response(False, 'User has not purchased event.', status.HTTP_200_OK)
    
    
  def post(self, request):
    username = request.data.get('username')
    subscription_type = request.data.get('subscription_type')
    event_name = request.data.get('event_name')
    today = date.today()

    user = User.objects.filter(username=username).first()
    
    if user is None:
      return return_response({}, 'Error! User does not exist.', status.HTTP_400_BAD_REQUEST)

    purchase = Purchase.objects.filter(user=user)
    
    if purchase.exists() == True:
      purchase = purchase.first()
      if subscription_type == 'single':
        purchase.is_yearly_subscription = False
      else:
         purchase.is_yearly_subscription = True
      purchase.purchase_date = today
      purchase.event_name = event_name
      purchase.save()
      return return_response({}, 'Success', status.HTTP_200_OK)

    purchase = Purchase(
        user=user,
        purchase_date=today,
        is_yearly_subscription=False if subscription_type == 'single' else True,
        event_name=event_name
    )

    purchase.save()
    return return_response({}, 'Success', status.HTTP_200_OK)
