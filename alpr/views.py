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
import io

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

            data = faceRecognition(abs_path)

            context = {
                'form' : form,
                'img' : '/media/alpr/'+filename,
                'data' : data
            }

    else:
        form = AlprForm()

        context = {
            'form': form,
            'data' : {
                'FaceMatches' : {
                    'id1': {'name': 'sankalp', 'confidence': 99},
                    'id2': {'name': 'sankalp', 'confidence': 99}
                }
            }
        }

    return render(request, 'alpr/alpr.html', context)


def faceRecognition(abs_path):

    # start here #
    rekognition = boto3.client('rekognition', 
        region_name=os.getenv('AWS_DEFAULT_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        # aws_session_token=SESSION_TOKEN
        )
    dynamodb = boto3.client('dynamodb', 
        region_name=os.getenv('AWS_DEFAULT_REGION'),
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
        # aws_session_token=SESSION_TOKEN
        )

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

        data['FaceMatches'][match['Face']['FaceId']] = {}
        
        data['FaceMatches'][match['Face']['FaceId']]['confidence'] = match['Face']['Confidence']
        
        face = dynamodb.get_item(
            TableName='face_recognition_demo',  
            Key={'RekognitionId': {'S': match['Face']['FaceId']}}
            )
        
        if 'Item' in face:
            data['FaceMatches'][match['Face']['FaceId']]['name'] =  face['Item']['FullName']['S']
        else:
            data['FaceMatches'][match['Face']['FaceId']]['name'] = 'no match found in person lookup'

    # ends here #

    return data
