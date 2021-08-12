from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Create your views here.
@api_view(['GET', 'POST'])
def main(req):
	return Response('blah', status=status.HTTP_200_OK)