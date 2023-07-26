from .helpers import get_soup_from_url, return_response
from ..Fighter.models import Fighter
import sys
from progress.bar import Bar
from rest_framework import status
from rest_framework.response import Response

def get_text(td):
  return td.text.strip().lower()

def scrape_raw_fighter_details():
    lowercase_letters = list("abcdefghijklmnopqrstuvwxyz")
    bar = Bar('Processing', max=26)

    for item in lowercase_letters:
        url = f"http://ufcstats.com/statistics/fighters?char={item}&page=all"
        soup = get_soup_from_url(url)

        fighter_details = soup.select('tbody .b-statistics__table-row')
        for fighter in fighter_details:
            tds = fighter.find_all('td')
            first_name = ""
            last_name = ""
            nickname = ""
            height = ""
            weight = ""
            reach = ""
            stance = ""
            record = ""
            belt = ""
            dob = ""
            slpm = ""
            str_acc = ""
            sapm = ""
            str_def = ""
            td_avg = ""
            td_acc = ""
            td_def = ""
            sub_avg = ""

            for index, td in enumerate(tds):
                if index == 0:
                    first_name = get_text(td)
                elif index == 1:
                    last_name = get_text(td)
                    fighter_anchor = td.find('a')
                    if fighter_anchor:
                        fighter_link = fighter_anchor['href']
                elif index == 2:
                    nickname = get_text(td)
                elif index == 3:
                    height = get_text(td)
                elif index == 4:
                    weight = get_text(td)
                elif index == 5:
                    reach = get_text(td)
                elif index == 6:
                    stance = get_text(td)
                elif index == 7:
                    record += get_text(td) + '/'
                elif index == 8:
                    record += get_text(td) + '/'
                elif index == 9:
                    record += get_text(td)
                elif index == 10:
                    belt = get_text(td)

            # Check if the fighter already exists in the database
            fighter_obj, created = Fighter.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={
                    'record': record,
                    'height': height,
                    'stance': stance,
                    'dob': dob,
                    'weight': weight,
                    'reach': reach,
                    'slpm': slpm if slpm != '' else 0,
                    'str_acc': str_acc,
                    'sapm': sapm if sapm != '' else 0,
                    'str_def': str_def,
                    'td_avg': td_avg if td_avg != '' else 0,
                    'td_acc': td_acc,
                    'td_def': td_def,
                    'sub_avg': sub_avg if sub_avg != '' else 0,
                }
            )

            if created:
                print(f"New fighter created: {fighter_obj.first_name} {fighter_obj.last_name}")
            else:
                print(f"Fighter already exists: {fighter_obj.first_name} {fighter_obj.last_name}")
            if created:
              if 'fighter_link' in locals():

                if len(fighter_link) > 0:
                    fighter_soup = get_soup_from_url(fighter_link)
                    ul_tag = fighter_soup.find('ul', class_='b-list__box-list')
                    if ul_tag:
                        for li_tag in ul_tag.find_all('li', class_='b-list__box-list-item'):
                            title = li_tag.find('i', class_='b-list__box-item-title').text.strip()
                            content = li_tag.get_text(strip=True, separator=' ')
                            if title == "DOB:":
                                dob = content.replace("DOB:", "").strip()

                    second_div_tag = fighter_soup.find('div', class_='b-list__info-box-left clearfix')
                    for li_tag in second_div_tag.find_all('li', class_='b-list__box-list-item b-list__box-list-item_type_block'):
                        title = li_tag.find('i', class_='b-list__box-item-title').text.strip()
                        content = li_tag.get_text(strip=True, separator=' ')
                        if title == "SLpM:":
                            slpm = content.replace("SLpM:", "").strip()
                        elif title == "Str. Acc.:":
                            str_acc = content.replace('Str. Acc.:', '').strip()
                        elif title == "SApM:":
                            sapm = content.replace('SApM:', '').strip()
                        elif title == "Str. Def:":
                            str_def = content.replace('Str. Def:', '').strip()
                        elif title == "TD Avg.:":
                            td_avg = content.replace('TD Avg.:', '').strip()
                        elif title == "TD Acc.:":
                            td_acc = content.replace('TD Acc.:', '').strip()
                        elif title == "TD Def.:":
                            td_def = content.replace('TD Def.:', '').strip()
                        elif title == "Sub. Avg.:":
                            sub_avg = content.replace('Sub. Avg.:', '').strip()
                    fighter_to_update = Fighter.objects.filter(first_name=first_name, last_name=last_name).first()
                    fighter_to_update.slpm = slpm
                    fighter_to_update.str_acc = str_acc
                    fighter_to_update.sapm = sapm
                    fighter_to_update.str_def = str_def
                    fighter_to_update.td_avg = td_avg
                    fighter_to_update.td_acc = td_acc
                    fighter_to_update.td_def = td_def
                    fighter_to_update.sub_avg = sub_avg
                    fighter_to_update.dob = dob
                    fighter_to_update.save()
        bar.next()

    bar.finish()
    return {'Success': True}
