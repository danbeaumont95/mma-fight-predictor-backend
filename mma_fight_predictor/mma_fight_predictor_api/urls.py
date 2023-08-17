from .User.user import UserList
from .Events.events import EventsList
from .Fighter.fighter import FighterList
from .Prediction.prediction import PredictionList
from django.urls import re_path as url, path
from .helpers.helpers import update_loser_field, get_fight_style_with_best_win_percentage_api_call
from .helpers.scraping import scrape_raw_fighter_details

urlpatterns = [
    # path('api', OrganisationApiView.as_view()),
    path('user/', UserList.as_view(), name='user-list'),
    path('events/', EventsList.as_view(), name="events_list"),
    # path('events/<str:event_id>', EventsList.as_view({'get': 'get_event_by_id'}), name="get_event_by_id")
    path('events/get_event_details', EventsList.get_event_by_id, name="get_event_by_id"),
    path('events/get_basic_fight_stats', EventsList.get_basic_fight_stats, name="get_basic_fight_stats"),
    path('events/get_in_depth_stats', EventsList.get_in_depth_stats, name="get_in_depth_stats"),
    path('events/get_next_event_poster', EventsList.get_next_event_poster, name="get_next_event_poster"),
    path('fighters/', FighterList.as_view(), name='fighters'),
    path('fighter/read_csv', FighterList.read_fighters_csv, name='read_fighters_csv'),
    path('fighter/read_fight_csv', FighterList.read_fight_csv, name='read_fight_csv'),
    path('fighter/test_many', FighterList.test_many, name='test_many'),
    path('fighter/get_stats_from_db', FighterList.get_stats_from_db, name='get_stats_from_db'),
    path('fighter/update_loser_field', update_loser_field, name='update_loser_field'),
    path('fighter/get_fighter_image', FighterList.get_fighter_image, name='get_fighter_image'),
    path('fighter/get_stats_for_match_up', FighterList.get_stats_for_match_up, name='get_stats_for_match_up'),
    path('get_fight_style_with_most_wins', get_fight_style_with_best_win_percentage_api_call, name='your-get_fight_style_with_most_wins-name'),
    path('prediction/', PredictionList.as_view(), name='prediction'),
    path('prediction/bulk_insert_predictions', PredictionList.bulk_insert_predictions, name='bulk_insert_predictions'),
    # path('fighter/scrape_fighter_stats', scrape_raw_fighter_details, name='scrape_raw_fighter_details')
    path('fighter/scrape_fighter_stats', FighterList.scrape_fighter_details, name='scrape_fighter_details'),
    path('fighter/scrape_fight_stats', FighterList.scrape_fight_details, name='scrape_fight_details'),
    path('prediction/add_winners_to_predictions', PredictionList.add_winners_to_predictions, name='add_winners_to_predictions'),
]
