from .models import Image
from ..Fighter.models import Fighter
from django import forms
from rest_framework.decorators import api_view
from rest_framework import status
from ..helpers.helpers import return_response


class ImageForm(forms.Form):
    image = forms.ImageField()
    
def insert_image(fighter_name, post, files):

    name_parts = fighter_name.split()
    first_name = name_parts[0]
    if len(name_parts) > 1:
      if len(name_parts) > 2:
        last_name = " ".join(name_parts[1:])
      else:
        last_name = name_parts[1]
    else:
      last_name = None


    form = ImageForm(post, files)
    if form.is_valid():
        image_data = form.cleaned_data['image'].read()
        fighter = Fighter.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).first()
        if fighter is not None:
          existing_image = Image.objects.filter(fighter=fighter).first()

          if existing_image:
              existing_image.image_data = image_data
              existing_image.save()
          else:
              image_model = Image(image_data=image_data, fighter=fighter)
              image_model.save()
          return True
