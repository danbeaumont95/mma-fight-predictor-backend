from .User.user import UserList
from .Events.events import EventsList
from .Fighter.fighter import FighterList
from django.urls import re_path as url, path
from .helpers.helpers import update_loser_field

urlpatterns = [
    # path('api', OrganisationApiView.as_view()),
    path('user/', UserList.as_view(), name='user-list'),
    path('events/', EventsList.as_view(), name="events_list"),
    # path('events/<str:event_id>', EventsList.as_view({'get': 'get_event_by_id'}), name="get_event_by_id")
    path('events/get_event_details', EventsList.get_event_by_id, name="get_event_by_id"),
    path('events/get_basic_fight_stats', EventsList.get_basic_fight_stats, name="get_basic_fight_stats"),
    path('events/get_in_depth_stats', EventsList.get_in_depth_stats, name="get_in_depth_stats"),
    path('fighters/', FighterList.as_view(), name='fighters'),
    path('fighter/read_csv', FighterList.read_fighters_csv, name='read_fighters_csv'),
    path('fighter/read_fight_csv', FighterList.read_fight_csv, name='read_fight_csv'),
    path('fighter/test_many', FighterList.test_many, name='test_many'),
    path('fighter/get_stats_from_db', FighterList.get_stats_from_db, name='get_stats_from_db'),
    path('fighter/update_loser_field', update_loser_field, name='update_loser_field'),
]
