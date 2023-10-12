from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
# from .models import User
# from .models import User
from bcrypt import hashpw, gensalt, checkpw
from ..helpers.helpers import return_response, is_valid_email, has_length
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from ..Tokens.models import Token

class UserList(APIView):
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
      
    def post(self, request):
      print(request.data, 'reqdata')
      serializer = UserSerializer(data=request.data)
      print(serializer, 'serializer1')
      if serializer.is_valid():
          print(serializer.validated_data, 'serializer.validated_data')
          User.objects.create_user(**serializer.validated_data)
          return Response(serializer.data, status=status.HTTP_201_CREATED)
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def check_access_token(request):
  try:
    access = request.data.get('access')
    email = request.data.get('email')
    user = User.objects.filter(email=email).first()
    if user is None:
      return return_response({}, 'Error! Unable to find user.', status.HTTP_400_BAD_REQUEST)
    token = Token.objects.filter(user=user)
    if token.exists():
      db_access_token = token.first().access_token
      if db_access_token == access:
        return return_response(True, 'Success!', status.HTTP_200_OK)
      else:
        return return_response(False, 'Error! Invalid token.', status.HTTP_200_OK)
  except Exception as e:
      return return_response(False, 'Error! Unable to check token status.', status.HTTP_500_INTERNAL_SERVER_ERROR)
    
  