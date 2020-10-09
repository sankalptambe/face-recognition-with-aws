from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import AlprForm
import sys
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import datetime
import requests
from pprint import pprint
import os
import boto3
from PIL import Image

@login_required
def alpr(request):

    if request.method == 'POST':

        form = AlprForm(request.POST, request.FILES)

        if form.is_valid():  

            myfile = request.FILES['image']
            
            fs = FileSystemStorage(location='media/alpr/')

            filename = fs.save(myfile.name, myfile)

            messages.success(request, f'Your image is being processed. Kindly wait...')

            uploaded_file_url = fs.url(filename)
            
            abs_path =  os.path.join(os.path.dirname(os.path.dirname(__file__)),'media/alpr/'+filename)

            # start here #
            image = Image.open(abs_path)
            stream = io.BytesIO()
            image.save(stream,format="JPEG")
            image_binary = stream.getvalue()

            response = rekognition.search_faces_by_image(
                    CollectionId='face_recognition_demo',
                    Image={'Bytes':image_binary}                                       
                    )
            
            data ={}

            data['FaceMatches'] = {}

            for match in response['FaceMatches']:

                data['FaceMatches'][match['Face']['FaceId']] = match['Face']['Confidence']
                
                face = dynamodb.get_item(
                    TableName='face_recognition_demo',  
                    Key={'RekognitionId': {'S': match['Face']['FaceId']}}
                    )
                
                if 'Item' in face:
                    data['FaceMatches'][match['Face']['FaceId']] =  face['Item']['FullName']['S']
                else:
                    data['FaceMatches'][match['Face']['FaceId']] = 'no match found in person lookup'

            # ends here #

            context = {
                'form': form,
                'data' : data
            }

    else:
        form = AlprForm()

        context = {
            'form': form
        }

    return render(request, 'alpr/alpr.html', context)
