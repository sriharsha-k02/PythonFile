import os
import time
from gevent import monkey
import requests
import gc
from datetime import datetime
from bs4 import BeautifulSoup as BS
from simple_salesforce import Salesforce
import json
import base64
import csv
import xlsxwriter
sourceparams = {
    "grant_type": "password",
    "client_id": "3MVG9llQY5kM9T6ft1Y9n7M2VbU4KnChEQXJ4rjAkZeR77hUj6X5MEFvF4sj1wEMzSRmizXczJq0OJLNdtG9w", # Consumer Key
    "client_secret": "8129957159604394102", # Consumer Secret
    "username": "abhilash.r.adavelly@pos.eu.preview", # The email you use to login
    "password": "" # Concat your password and your security token
	}
permsetquery = 'SELECT Label, (SELECT PermissionsCreate,PermissionsDelete,PermissionsEdit,PermissionsModifyAllRecords,PermissionsRead,PermissionsViewAllRecords,SobjectType FROM ObjectPerms as Table1), (SELECT Field,SobjectType,PermissionsEdit,PermissionsRead FROM FieldPerms As Table2) FROM PermissionSet'
fieldpermquery = 'SELECT Parent.Name, Field,SobjectType,PermissionsEdit,PermissionsRead FROM FieldPermissions where SobjectType IN (\''+str('Account')+'\''+','+'\''+str('Contact')+'\''+','+'\''+str('Opportunity')+'\''+','+'\''+str('OpportunityLineItem')+'\''+')'
print(fieldpermquery)
objpermquery = 'SELECT Parent.Name, PermissionsCreate,PermissionsDelete,PermissionsEdit,PermissionsModifyAllRecords,PermissionsRead,PermissionsViewAllRecords,SobjectType FROM ObjectPermissions where SobjectType IN (\''+str('Account')+'\''+','+'\''+str('Contact')+'\''+','+'\''+str('Opportunity')+'\''+','+'\''+str('OpportunityLineItem')+'\''+')'
print(objpermquery)
FinalObjectpermList = set()
FinalFieldpermList = set()
FinalUserPermissionList = set()
print('*******************')
print('* Permission Sets Repository *')
print('*******************')
print('Please Update the Source and Target Parameters in Scripts based on requirement')
print('Also Update the API version being used: if it changes')
print('***********************************************************************')
def restapiauthentication(params):
	r = requests.post("https://test.salesforce.com/services/oauth2/token", params=params)
	print(r.status_code)
	if r.status_code == 200:
		access_token = r.json().get("access_token")
		instance_url = r.json().get("instance_url")
		return {access_token, instance_url}
	else:
		print('Authentication Error Please Check the credentials')
		exit(0)
print('***********************************************************************')
print('Authenticating the Source Environment')
print('***********************************************************************')
sourceauthresult =list(restapiauthentication(sourceparams))
print('Source Sandbox Authenticated')
def sf_api_call(accesstoken, instanceurl, action, parameters = {}, method = 'get', data = {}):
	headers = {
        'Content-type': 'application/json',
        'Accept-Encoding': 'gzip',
        'Authorization': 'Bearer %s' % accesstoken
    }
	if method == 'get':
		r = requests.request(method, instanceurl+action, headers=headers, params=parameters, timeout=60)
	elif method in ['post', 'patch']:
		r = requests.request(method, instanceurl+action, headers=headers, json=data, params=parameters, timeout=10)
	else:
		raise ValueError('Method should be get or post or patch.')
	#print('Debug: API %s call: %s' % (method, r.url) )
	if r.status_code < 300:
		if method=='patch':
			return None
		else:
			return r.json()
	else:
		raise Exception('API error when calling %s : %s' % (r.url, r.content))
for item in sourceauthresult:
	if 'http' in item:
		sourceinstance = item
	else:
		sourceaccess_token = item
def UserRecordsProfile(instance, access_token):
	UserRecordsquery = 'SELECT Name, Id, username FROM User where Profile.Name=\''+str('PwC Integration')+'\''
	userrecordresult = json.dumps(sf_api_call(access_token, instance,'/services/data/v43.0/query/', { 'q': UserRecordsquery }), indent=2)
	userresultdict = json.loads(userrecordresult)
	for userresultrecord in userresultdict['records']:
		print('Integration User:',userresultrecord['Name'])
		userpermissionsetrecordsquery = 'SELECT AssigneeId,PermissionSetId FROM PermissionSetAssignment where AssigneeId=\''+str(userresultrecord['Id'])+'\''
		userpermqueryresult = json.dumps(sf_api_call(access_token, instance,'/services/data/v43.0/query/', { 'q': userpermissionsetrecordsquery }), indent=2)
		userpermresultdict = json.loads(userpermqueryresult)
		print('Permission Sets:')
		for userpermresultrecord in userpermresultdict['records']:
			permissionsetNamequery = 'SELECT Id, Name FROM PermissionSet where Id = \''+str(userpermresultrecord['PermissionSetId'])+'\''
			permissionsetNameresult = json.dumps(sf_api_call(access_token, instance,'/services/data/v43.0/query/', { 'q': permissionsetNamequery }), indent=2)
			permsetNamedict = json.loads(permissionsetNameresult)
			if permsetNamedict['records'][0]['Name'][0]!='X':
				FinalUserPermissionList.add((userresultrecord['Name'], permsetNamedict['records'][0]['Name']))
def fieldpermission(instance, access_token, query):
	query_results = json.dumps(sf_api_call(access_token, instance,'/services/data/v43.0/query/', { 'q': query }), indent=2)
	queryresultdict = json.loads(query_results)
	for fieldpermrecord in queryresultdict['records']:
		if(fieldpermrecord['Parent']['Name'][0]!='X'):
			FinalFieldpermList.add((fieldpermrecord['Parent']['Name'], fieldpermrecord['SobjectType'], fieldpermrecord['Field'].split('.')[1], fieldpermrecord['PermissionsEdit'], fieldpermrecord['PermissionsRead']))
fieldpermission(sourceinstance, sourceaccess_token, fieldpermquery)
def objectpermission(instance, access_token, query):
	query_results = json.dumps(sf_api_call(access_token, instance,'/services/data/v43.0/query/', { 'q': query }), indent=2)
	queryresultdict = json.loads(query_results)
	for objectpermrecord in queryresultdict['records']:
		if(objectpermrecord['Parent']['Name'][0]!='X'):
			FinalObjectpermList.add((objectpermrecord['Parent']['Name'], objectpermrecord['SobjectType'],objectpermrecord['PermissionsCreate'],objectpermrecord['PermissionsDelete'], objectpermrecord['PermissionsEdit'], objectpermrecord['PermissionsModifyAllRecords'], objectpermrecord['PermissionsRead'], objectpermrecord['PermissionsViewAllRecords']))
objectpermission(sourceinstance, sourceaccess_token, objpermquery)
def CreateExcelObjFieldPerm(FinalObjectpermList, FinalFieldpermList, FinalUserPermissionList):
	workbook = xlsxwriter.Workbook('PermissionSetPreview.xlsx')
	objectsheet = workbook.add_worksheet('Object Permissions')
	fieldsheet = workbook.add_worksheet('Field Permissions')
	userpermsheet = workbook.add_worksheet('User Permissions')
	objrow = 0
	objcol = 0
	objectsheet.write(objrow, objcol,'Permission Set')
	objcol = objcol+1
	objectsheet.write(objrow, objcol,'Sobject type')
	objcol = objcol+1
	objectsheet.write(objrow, objcol,'Create')
	objcol = objcol+1
	objectsheet.write(objrow, objcol,'Delete')
	objcol = objcol+1
	objectsheet.write(objrow, objcol,'Edit')
	objcol = objcol+1
	objectsheet.write(objrow, objcol,'ModifyAllRecords')
	objcol = objcol+1
	objectsheet.write(objrow, objcol,'Read')
	objcol = objcol+1
	objectsheet.write(objrow, objcol,'ViewAllRecords')
	for objpermissionset in FinalObjectpermList:
		objrow=objrow + 1
		objcol = 0
		for objpermset in objpermissionset:
			objectsheet.write(objrow, objcol, objpermset)
			objcol = objcol+1
	fieldrow = 0
	fieldcol = 0
	fieldsheet.write(fieldrow, fieldcol, 'Permission Set')
	fieldcol = fieldcol+1
	fieldsheet.write(fieldrow, fieldcol,'Sobject type')
	fieldcol = fieldcol+1
	fieldsheet.write(fieldrow, fieldcol,'Field')
	fieldcol = fieldcol+1
	fieldsheet.write(fieldrow, fieldcol,'Edit')
	fieldcol = fieldcol+1
	fieldsheet.write(fieldrow, fieldcol,'Read')
	for fieldpermissionset in FinalFieldpermList:
		fieldrow = fieldrow + 1
		fieldcol = 0
		for fieldpermset in fieldpermissionset:
			fieldsheet.write(fieldrow, fieldcol,fieldpermset)
			fieldcol = fieldcol + 1
	userpermrow = 0
	userpermcol = 0
	userpermsheet.write(userpermrow, userpermcol, 'User')
	userpermcol = userpermcol+1
	userpermsheet.write(userpermrow, userpermcol,'Permission Set')
	for userpermissonset in FinalUserPermissionList:
		userpermrow = userpermrow + 1
		userpermcol = 0
		for userpermset in userpermissonset:
			userpermsheet.write(userpermrow, userpermcol, userpermset)
			userpermcol = userpermcol + 1
	workbook.close()
UserRecordsProfile(sourceinstance, sourceaccess_token)
CreateExcelObjFieldPerm(FinalObjectpermList, FinalFieldpermList, FinalUserPermissionList)