
"""
----------------------------------------------------------------------
|				!!!--FOR POST_DEPLOYMENT--!!!						 |	
| Takes input from the PRE_DEPLOYMENT csv which contains			 |
| the  premission set data											 |
----------------------------------------------------------------------
"""

from salesforce_bulk import SalesforceBulk
import pandas as pd
import unicodecsv 
import csv
import time

print("Program Started")

df = pd.read_csv('PermissionSet.csv')

#-----Create where clause condition-----

#Id
idSet = df.Id.unique()
ids = []

for id in idSet:
    ids.append("'"+str(id)+"'")
psIds = ','.join(ids)

#-----Login into Salesforce-----

print("logging into Salesforce")

bulk = SalesforceBulk(username= 'sri.harsha.kondabolu@pos.eu.mock120191',
                      password= 'infy@1234',
                      security_token= 'fPYit2AXZ7LbUfZD80gQizF3O',
                      sandbox = True)

print("login Successful")


#-----Profile Map Creation from profile object-----

print("PermissionSet Query Started")

psIdList = []
psQuery = "SELECT Id,Name FROM PermissionSet Where id in "+'( '+psIds+' )'
psJob = bulk.create_query_job("PermissionSet", contentType='CSV')
psBatch = bulk.query(psJob,psQuery)
bulk.close_job(psJob)
while not bulk.is_batch_done(psBatch):
        time.sleep(10)
        print("Job In progress...")

print("Permission Set Job Completed")
    

for result in bulk.get_all_results_for_query_batch(psBatch):
        reader = unicodecsv.DictReader(result, encoding='utf-8')
        for row in reader:
               psIdList.append(dict(row).get('Id')) 


#-----Comparing PS Length-----

if len(ids) != len(psIdList):
    print('Please use the pre-deploy premissionSetAssignment file for permissionset assignment')
    exit
else:
    print('length doesnt match, processing further')


idss = list(idSet)

notInIds = []
notInPsIds = []
if len(ids) > len(psIdList):
    for rec in idss:
        if rec not in psIdList:
            notInIds.append(rec)
else:
    for rec in psIdList:
        if rec not in idss:
            notInPsIds.append(rec)

print(notInIds)
print(notInPsIds)