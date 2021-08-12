from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.
@api_view(['POST'])
def shard(req):
	return Response('blah', status=status.HTTP_200_OK)

@api_view(['POST'])
def normal(req):
	return Response('normal', status=status.HTTP_200_OK)

@api_view(['GET'])
def user(req):
	return Response('user', status=status.HTTP_200_OK)