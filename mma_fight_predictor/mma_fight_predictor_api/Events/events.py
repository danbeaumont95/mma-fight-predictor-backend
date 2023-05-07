import requests
from bs4 import BeautifulSoup
from rest_framework.views import APIView
from ..helpers.helpers import return_response, get_soup_from_url, compare_fractions
from rest_framework import status
from rest_framework.decorators import api_view
import pandas as pd

class EventsList(APIView):
  def get(self, request):
    url = 'http://ufcstats.com/statistics/events/upcoming?page=all'
    # Send a request to the website and get the HTML content
    soup = get_soup_from_url(url)

    event_name = soup.find_all('a', {'class': 'b-link b-link_style_black'})

    events = ({'name': item.get_text(strip=True), 'link': item.get("href")} for item in event_name)

    return return_response(events, 'Sucess', status.HTTP_200_OK)
  
  @api_view(['GET'])
  def get_event_by_id(request):
    # url = f'http://ufcstats.com/event-details/3c6976f8182d9527'
    url = request.data.get('event_url')
    soup = get_soup_from_url(url)
    fights_html = soup.find_all('tr', {'class': 'js-fight-details-click'})
    
    fights_data = []
    for item in fights_html:
      link = item.get("data-link")
      fighter_names = item.find_all('td', {'class': 'b-fight-details__table-col l-page_align_left'})[0].find_all('a')
      fighter_1_name = fighter_names[0].get_text(strip=True)
      fighter_2_name = fighter_names[1].get_text(strip=True)
      weight_class = item.find_all('td', {'class': 'b-fight-details__table-col l-page_align_left'})[1].get_text(strip=True)
      fight_data = {'fighter_1': fighter_1_name, 'fighter_2': fighter_2_name, 'weight_class': weight_class, 'link': link}
      fights_data.append(fight_data)
    return return_response(fights_data, 'Success', status.HTTP_200_OK)
  
  @api_view(['GET'])
  def get_basic_fight_stats(request):
    url = request.data.get('fight_url')
    soup = get_soup_from_url(url)

    table = soup.find('table')

    dfs = pd.read_html(str(table))
    df = dfs[0]
    df = df.dropna()
    first_column_name = df.columns[0]
    renamed_df = df.rename(columns={first_column_name: 'Statistic'})

    result = {}
    
    column_names = renamed_df.iloc[:, 0].tolist()
    fighters = renamed_df.iloc[:, 1:].columns.tolist()
    fighter_1 = fighters[0]
    fighter_2 = fighters[1]
    
    winner_dict = {fighter_1: 0, fighter_2: 0}

    # Loop through the columns and extract the data for each fighter
    for col in column_names:
        # Get the data for the column and drop the first row
        col_data = renamed_df.loc[renamed_df['Statistic'] == col].iloc[:, 1:].T.reset_index()
        col_data.columns = ['Fighter', col]

        # Set the fighter names as the index and drop the index name
        col_data.set_index('Fighter', inplace=True)
        col_data.index.name = None

        # Convert the column data to a dictionary
        col_dict = col_data.to_dict()[col]
        
        # TO-DO change this to take into account this might not be correct if 10-2 fighter facing 1-0 as 1-0 would win this but has had way less fights===less experience
        if col == 'Wins/Losses/Draws':
          fighter_1_record = col_dict[fighter_1]
          fighter_2_record = col_dict[fighter_2]
          figter_1_wins, fighter_1_losses, fighter_1_draws = fighter_1_record.split("-")

          figter_1_wins = int(figter_1_wins.split()[0])
          fighter_1_losses = int(fighter_1_losses.split()[0])
          fighter_1_draws = int(fighter_1_draws.split()[0])
          
          figter_2_wins, fighter_2_losses, fighter_2_draws = fighter_2_record.split("-")

          figter_2_wins = int(figter_2_wins.split()[0])
          fighter_2_losses = int(fighter_2_losses.split()[0])
          fighter_2_draws = int(fighter_2_draws.split()[0])
          
          compared_wins_winner = compare_fractions((figter_1_wins, fighter_1_losses, fighter_1), (figter_2_wins, fighter_2_losses, fighter_2))
          if compared_wins_winner != 'Equal':
            col_dict['winner'] = compared_wins_winner
            winner_dict[compared_wins_winner] +=1

        if col == 'Reach':
          if col_dict[fighter_1] > col_dict[fighter_2]:
            col_dict['winner'] = fighter_1
            winner_dict[fighter_1] +=1
          elif col_dict[fighter_2] > col_dict[fighter_1]:
            col_dict['winner'] = fighter_2
            winner_dict[fighter_2] +=1
          else:
            print('both fighters have the same reach')
        
        if col == 'Strikes Landed per Min. (SLpM)':
          if col_dict[fighter_1] > col_dict[fighter_2]:
            col_dict['winner'] = fighter_1
            winner_dict[fighter_1] +=1
          elif col_dict[fighter_2] > col_dict[fighter_1]:
            col_dict['winner'] = fighter_2
            winner_dict[fighter_2] +=1
          else:
            print('both fighters have the same significant strikes lander per min')

        if col == 'Striking Accuracy':
          fighter_1_striking_accuracy_num = float(col_dict[fighter_1].strip("%"))
          fighter_2_striking_accuracy_num = float(col_dict[fighter_2].strip("%"))
          if fighter_1_striking_accuracy_num > fighter_2_striking_accuracy_num:
            col_dict['winner'] = fighter_1
            winner_dict[fighter_1] +=1
          elif fighter_2_striking_accuracy_num > fighter_1_striking_accuracy_num:
             col_dict['winner'] = fighter_2
             winner_dict[fighter_2] +=1
          else:
            print('both fighters have the same striking accuracy')
            
        if col == 'Strikes Absorbed per Min. (SApM)':
          if col_dict[fighter_1] > col_dict[fighter_2]:
            col_dict['winner'] = fighter_2
            winner_dict[fighter_2] +=1
          elif col_dict[fighter_2] > col_dict[fighter_1]:
            col_dict['winner'] = fighter_1
            winner_dict[fighter_1] +=1
          else:
            print('both fighters have the same Strikes Absorbed per Min')
        
        if col == 'Defense':
          fighter_1_striking_defence_num = float(col_dict[fighter_1].strip("%"))
          fighter_2_striking_defence_num = float(col_dict[fighter_2].strip("%"))
          if fighter_1_striking_defence_num > fighter_2_striking_defence_num:
            col_dict['winner'] = fighter_1
            winner_dict[fighter_1] +=1
          elif fighter_2_striking_defence_num > fighter_1_striking_defence_num:
             col_dict['winner'] = fighter_2
             winner_dict[fighter_2] +=1
          else:
            print('both fighters have the same defence')
        
        if col == 'Takedowns Average/15 min.':
          if col_dict[fighter_1] > col_dict[fighter_2]:
            col_dict['winner'] = fighter_1
            winner_dict[fighter_1] +=1
          elif col_dict[fighter_2] > col_dict[fighter_1]:
            col_dict['winner'] = fighter_2
            winner_dict[fighter_2] +=1
          else:
            print('both fighters have the same takedowns average/15 min')
        
        if col == 'Takedown Accuracy':
          if col_dict[fighter_1] > col_dict[fighter_2]:
            col_dict['winner'] = fighter_1
            winner_dict[fighter_1] +=1
          elif col_dict[fighter_2] > col_dict[fighter_1]:
            col_dict['winner'] = fighter_2
            winner_dict[fighter_2] +=1
          else:
            print('both fighters have the same takedowns accuracy')
        
        if col == 'Takedown Defense':
          if col_dict[fighter_1] > col_dict[fighter_2]:
            col_dict['winner'] = fighter_1
            winner_dict[fighter_1] +=1
          elif col_dict[fighter_2] > col_dict[fighter_1]:
            col_dict['winner'] = fighter_2
            winner_dict[fighter_2] +=1
          else:
            print('both fighters have the same takedowns accuracy')
        
        if col == 'Submission Average/15 min.':
          if col_dict[fighter_1] > col_dict[fighter_2]:
            col_dict['winner'] = fighter_1
            winner_dict[fighter_1] +=1
          elif col_dict[fighter_2] > col_dict[fighter_1]:
            col_dict['winner'] = fighter_2
            winner_dict[fighter_2] +=1
          else:
            print('both fighters have the same submission average/15 min.')

        # Add the column dictionary to the result dictionary
        result[col] = col_dict

    result['count'] = winner_dict
    if winner_dict[fighter_1] > winner_dict[fighter_2]:
      result['winner'] = fighter_1
    elif winner_dict[fighter_2] > winner_dict[fighter_1]:
      result['winner'] = fighter_2
    else:
      result['winner'] = 'Draw'
    return return_response(result, 'Success', status.HTTP_200_OK)
          

