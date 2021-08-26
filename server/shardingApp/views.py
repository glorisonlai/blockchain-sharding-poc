from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response
from . import services

# Create your views here.
@api_view(['POST'])
def shard(req: Request):
	transaction = services.process_transaction_request(req.data)
	res = services.shard_transaction_request()
	return Response(res, status=status.HTTP_200_OK)

@api_view(['POST'])
def normal(req: Request):
	transaction = services.process_transaction_request(req.data)
	# TODO: Perform some error handling if bad data
	res = services.serial_transaction_request()
	return Response(res, status=status.HTTP_200_OK)

@api_view(['POST'])
def transactions(req: Request):
	queued_transactions = sum(
		map(lambda transaction: services.process_transaction_request(transaction), req.data)
	)
	return Response(queued_transactions, statuts=status.HTTP_200_OK)

@api_view(['GET'])
def user(req: Request):
	return Response(services.get_user_wallets(), status=status.HTTP_200_OK)

@api_view(['GET'])
def test(req: Request):
	return Response(services.test(), status=status.HTTP_200_OK)