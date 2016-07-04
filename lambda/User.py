"""
# User.py
# Created: 23/06/2016
# Author: Adam Campbell
# Edited By: Miguel Saavedra
"""

import boto3
import botocore
import uuid
from Response import Response
from passlib.apps import custom_app_context as pwd_context
from boto3.dynamodb.conditions import Key, Attr

class User(object):

	def __init__(self, event, context):
		self.event = event
		self.context = context

	def register(self):
		# Get password for hashing
		password = self.event["user"]["password"]
		hashed = pwd_context.encrypt(password)
		# Get user register params
		register_params = {
			"ID": {"S": str(uuid.uuid4())},
			"Username": {"S": self.event["user"]["username"]},
			"Email": {"S": self.event["user"]["email"]},
			"Password": {"S": hashed},
			"Roles": {"S": str(1)}
		}
		# Attempt to add to dynamo
		try:
			dynamodb = boto3.client('dynamodb')
			dynamodb.put_item(
				TableName='User',
				Item=register_params,
				ReturnConsumedCapacity='TOTAL'
			)
		except botocore.exceptions.ClientError as e:
			print e.response['Error']['Code']
			response = Response("Error")
			response.errorMessage = "Unable to register new user: %s" % e.response['Error']['Code']
			return response.to_JSON()
		
		return Response("Success").to_JSON()

	def login(self):
		password =  self.event["User"]["Password"]
		# hash password for comparison
		hashed = pwd_context.encrypt(password)

		# Attempt to check dynamo
		try:
			dynamodb = boto3.resource('dynamodb')
			table = dynamodb.Table('User')
			password =  self.event["User"]["Password"]
			result = table.query(IndexName='Username', KeyConditionExpression=Key('Username').eq(self.event["User"]["Username"]))

			for i in result['Items']:
				if(i['Password'] == hashed):
					return Response("Success").to_JSON()
		except botocore.exceptions.ClientError as e:
			print e.response['Error']['Code']
			response = Response("Error", None)
			response.errorMessage = "Unable to log in: %s" % e.response['Error']['Code']
			return response.to_JSON()

		response = Response("Success", None)
		#Cookie Code here
		return response.to_JSON()

	def logout(self):
		# get user credentials
		token = self.event['tokenString']
    		user = self.event['userID']

		try:			
			# fetch dynamo table
			dynamodb = boto3.resource('dynamodb')
		    	table = dynamodb.Table('Token')

		    	# remove token from user
		    	response = table.delete_item(
		            Key={
		    	        'TokenString': token,
		                'UserID': user
	            		}
	        	)
		except botocore.exceptions.ClientError as e:
			print e.response['Error']['Code']
			response = Response("Error")
			response.errorMessage = "Unable to log out: %s" % e.response['Error']['Code']
			return response.to_JSON()
   
    		return Response("Success").to_JSON()