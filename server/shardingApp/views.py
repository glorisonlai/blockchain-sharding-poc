from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .services import generate_user_wallet

# Create your views here.
@api_view(['POST'])
def shard(req):
	return Response('blah', status=status.HTTP_200_OK)

@api_view(['POST'])
def normal(req):
	return Response('normal', status=status.HTTP_200_OK)

@api_view(['GET'])
def user(req):
	return Response(generate_user_wallet(), status=status.HTTP_200_OK)