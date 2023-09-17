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
    