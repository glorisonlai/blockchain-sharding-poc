from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from . import services

# Create your views here.
@api_view(['POST'])
def shard(req: Request):
	transaction = services.process_transaction_request(req.data)
	res = services.shard_transaction_request(transaction)
	return Response(res, status=status.HTTP_200_OK)

@api_view(['POST'])
def normal(req: Request):
	transaction = services.process_transaction_request(req.data)
	# TODO: Perform some error handling if bad data
	res = services.serial_transaction_request(transaction)
	return Response(res, status=status.HTTP_200_OK)

@api_view(['GET'])
def user(req: Request):
	return Response(services.get_user_wallets(), status=status.HTTP_200_OK)