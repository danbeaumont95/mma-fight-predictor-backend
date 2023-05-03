from .User.user import UserList

from django.urls import re_path as url, path
urlpatterns = [
    # path('api', OrganisationApiView.as_view()),
    path('user/', UserList.as_view(), name='user-list'),

]
