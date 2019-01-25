
"""
----------------------------------------------------------------------
|				!!!--FOR POST_DEPLOYMENT--!!!						 |	
| Takes input from the PRE_DEPLOYMENT csv which contains			 |
| the   																	 |
----------------------------------------------------------------------
"""

from salesforce_bulk import SalesforceBulk
import pandas as pd
import unicodecsv 
import csv
import time

print("Program Started")

df = pd.read_csv('Report3.csv')

#-----Create where clause condition-----

#profileName
profileNameSet = df.ProfileName.unique()
profile = []

for prof in profileNameSet:
    profile.append("'"+str(prof)+"'")
profileName = ','.join(profile)

#userRole
userRoleNameSet = df.UserRoleName.unique()
userRole = []

for word in userRoleNameSet:
    userRole.append("'"+str(word)+"'")
    
userRoleName = ','.join(userRole)

#-----Login into Salesforce-----

print("logging into Salesforce")

bulk = SalesforceBulk(username= 'username',
                      password= 'password',
                      security_token= 'security_token',
                      sandbox = 'Boolean')

print("login Successful")

#-----Profile Map Creation from profile object-----

print("Profile Query Started")

profileNameIdMap = {}
profileQuery = "SELECT Id,Name FROM Profile Where Name in "+'( '+profileName+' )'
profileJob = bulk.create_query_job("Profile", contentType='CSV')
profileBatch = bulk.query(profileJob,profileQuery)
bulk.close_job(profileJob)
while not bulk.is_batch_done(profileBatch):
        time.sleep(10)
        print("Job In progress...")

print("Profile Job Completed")
    

for result in bulk.get_all_results_for_query_batch(profileBatch):
        reader = unicodecsv.DictReader(result, encoding='utf-8')
        for row in reader:
               profileNameIdMap.update({dict(row).get('Name'):dict(row).get('Id')})    
                                    

#-----UserRole Map Creation from UserRole object-----

print("UserRole Query Started")

userNameIdMap = {}
userRoleQuery = "SELECT Id,Name FROM UserRole Where Name in  "+'( '+userRoleName+' )'
userRoleJob = bulk.create_query_job("UserRole", contentType='CSV')
userRoleBatch = bulk.query(userRoleJob,userRoleQuery)
bulk.close_job(userRoleJob) 
while not bulk.is_batch_done(userRoleBatch):
        time.sleep(10)
        print("Job In progress...")

print("UserRole Data Extracted")



for result in bulk.get_all_results_for_query_batch(userRoleBatch):
        reader = unicodecsv.DictReader(result, encoding='utf-8')
        for row in reader:
               userNameIdMap.update({dict(row).get('Name'):dict(row).get('Id')}) 


#-----Read from pre-refresh file and write in a new csv file-----

finalUpdateList = []
finalInsertList = []

with open('Report3.csv', 'r') as readFile:	#mention the pre-refresh user file.
    reader = csv.reader(readFile)
    lines = list(reader)
    finalUpdateList.append(lines[0])
    finalInsertList.append(lines[0])
    for line in lines[2:]:
        if line[1]:		
            finalUpdateList.append( [ line[0],line[1],line[2],profileNameIdMap.get(line[3]),userNameIdMap.get(line[4]) ])
        else:
            finalInsertList.append( [ line[0],line[1],line[2],profileNameIdMap.get(line[3]),userNameIdMap.get(line[4]),line[5],line[6],line[7] ])

#-----Write into a new csv files-----

with open("updateUserFile.csv", "w") as uf:
    writer = csv.writer(uf)
    writer.writerows(finalUpdateList)
    
with open("insertUserFile.csv", "w") as af:
    writer = csv.writer(af)
    writer.writerows(finalInsertList)	
	
print("Update/Insert file(s) created.")

#-----process the permission sets
