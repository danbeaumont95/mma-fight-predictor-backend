from rest_framework.response import Response
import requests
from bs4 import BeautifulSoup

def return_response(data, message, status):
    return Response({'data': data, 'message': message, 'status': status})

def get_soup_from_url(url):
    response = requests.get(url)
    html_content = response.content
    soup = BeautifulSoup(html_content, "html.parser")
    return soup

def compare_fractions(fraction1, fraction2):
    # Convert the fractions to a common denominator
    denominator = fraction1[1] * fraction2[1]
    numerator1 = fraction1[0] * fraction2[1]
    numerator2 = fraction2[0] * fraction1[1]

    # Compare the numerators
    if numerator1 > numerator2:
        # return "The first fraction {} is larger than the second fraction {}.".format(fraction1, fraction2)
        return fraction1[2]
    elif numerator1 < numerator2:
        return fraction2[2]
    else:
        return "Equal"


fraction1 = (8, 3)
fraction2 = (21, 3)
