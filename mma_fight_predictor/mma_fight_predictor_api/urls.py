from .User.user import UserList
from .Events.events import EventsList
from django.urls import re_path as url, path

urlpatterns = [
    # path('api', OrganisationApiView.as_view()),
    path('user/', UserList.as_view(), name='user-list'),
    path('events/', EventsList.as_view(), name="events_list"),
    # path('events/<str:event_id>', EventsList.as_view({'get': 'get_event_by_id'}), name="get_event_by_id")
    path('events/get_event_details', EventsList.get_event_by_id, name="get_event_by_id"),
    path('events/get_basic_fight_stats', EventsList.get_basic_fight_stats, name="get_basic_fight_stats")

]
