from .models import Image
from ..Fighter.models import Fighter
from django import forms
from rest_framework.decorators import api_view
from rest_framework import status
from ..helpers.helpers import return_response
from .helpers import insert_image

@api_view(['POST'])
def upload_image(request):
  inserted = insert_image(request.GET.get('fighter'), request.POST, request.FILES)
  if inserted == True:
    return return_response({}, 'Success', status.HTTP_200_OK)
    