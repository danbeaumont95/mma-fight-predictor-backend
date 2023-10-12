
from django.contrib.auth.models import User
from datetime import date

from django.http import HttpResponse
from ..Purchase.models import Purchase

from .helpers import return_response
from rest_framework import status
from django.core.mail import send_mail
from twilio.rest import Client
import json
import os
import stripe
from rest_framework.decorators import api_view
from .helpers import get_upcoming_events
from dotenv import load_dotenv
import os
load_dotenv()

# Can setup stripe to call this when live
@api_view(['POST'])
def webhook(request):
  ODDS_API_API_KEY = os.getenv('ODDS_API_API_KEY')
  STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
  STRIPE_ENDPOINT_SECRET = os.getenv('STRIPE_ENDPOINT_SECRET')
  TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
  TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
  MY_PHONE_NUMBER = os.getenv('MY_PHONE_NUMBER')
  odds_api_key= ODDS_API_API_KEY
  # The library needs to be configured with your account's secret key.
  stripe.api_key = STRIPE_API_KEY

  # This is your Stripe CLI webhook secret for testing your endpoint locally.
  endpoint_secret = STRIPE_ENDPOINT_SECRET
  try:
      event = None
      payload = request.body
      try:
          event = stripe.Event.construct_from(
        json.loads(payload), stripe.api_key
      )
      except ValueError as e:
          # Invalid payload
          raise e
      except stripe.error.SignatureVerificationError as e:
          # Invalid signature
          raise e

      if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object # contains a stripe.PaymentIntent
        # Then define and call a method to handle the successful payment intent.
        # handle_payment_intent_succeeded(payment_intent)
      elif event.type == 'payment_method.attached':
        payment_method = event.data.object # contains a stripe.PaymentMethod
        # Then define and call a method to handle the successful attachment of a PaymentMethod.
        # handle_payment_method_attached(payment_method)
      # ... handle other event types
      elif event.type == 'charge.succeeded':
        account_sid = TWILIO_ACCOUNT_SID
        auth_token = TWILIO_AUTH_TOKEN
        client = Client(account_sid, auth_token)
        email = event.data.object.billing_details.email
        # message = client.messages.create(
        #               body=f"New payment received from email: {email}",
        #               from_='+447458152280',
        #               to=MY_PHONE_NUMBER
        #           )
        # print(message.sid)
        user = User.objects.filter(email=email).first()
        today = date.today()
        events = list(get_upcoming_events())
        next_event = events[0]
        event_name = next_event['name']
        Purchase.objects.create(user=user,is_yearly_subscription=False, purchase_date=today, event_name=event_name)
      else:
        print('Unhandled event type {}'.format(event.type))

      return HttpResponse(status=200)
  except Exception as e:
    print(e, 'error123')
