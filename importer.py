import requests
import json
import sys
import csv
import argparse
from types import SimpleNamespace
import configparser

def setConfig(configFile):
	config = configparser.ConfigParser()
	config.read(configFile)

	configMap = {
		"admimUrl": config['DEFAULT']['admimUrl'],
		"adminLogin": config['DEFAULT']['adminLogin'],
		"adminPassword": config['DEFAULT']['adminPassword'],
		"realm": config['DEFAULT']['realm'],
		"client": config['DEFAULT']['client'],

		"csvMap": {
			"firstName": config['CSV']['firstName'],
			"lastName": config['CSV']['lastName'],
			"userName": config['CSV']['userName'],
			"email": config['CSV']['email'],
			"clientRole": config['CSV']['clientRole'],
			"realmRole": config['CSV']['realmRole'],
			"password": config['CSV']['password'],
		}
	}

	configMapping = SimpleNamespace(**configMap)
	configMapping.csvMap = SimpleNamespace(**configMap["csvMap"])

	return configMapping

def getKcBearer(url, user, password):
  head={
  	"Accept":       "application/json",
    "Content-Type": "application/x-www-form-urlencoded",
    "username":     user,
    "password":     password,
    "grant_type":   "password",
    "client_id":    "admin-cli",
  }

  result = requests.post(url+"/realms/master/protocol/openid-connect/token",head,proxies={'http':None})
  
  if result.status_code != 200:
  	print("error : " + str(result.status_code) + " " + result.text)

  return result.json()["access_token"]

def prepareKcApiHeaders(bearer):
  head = {
  	"Accept":       "application/json",
    "Content-Type": "application/json",
    "Authorization": "Bearer "+bearer
  }

  return head

def getRealmRole(url,user,password,realm, roleName):
	bearer = getKcBearer(url,user, password)
	head = prepareKcApiHeaders(bearer)

	# GET /admin/realms/{realm}/roles/{role-name}
	result = requests.get(url+"/admin/realms/" + realm + "/roles/" + roleName, headers=head,proxies={'http':None})

	role = result.json()
	#del role["containerId"]

	if result.status_code != 200:
  		print("getRole error : " + str(result.status_code) + " " + result.text)

	return role

def getClientRole(url,user,password,realm, clientId, roleName):
	bearer = getKcBearer(url, user, password)
	head = prepareKcApiHeaders(bearer)
	
	# GET /admin/realms/{realm}/clients/{id}/roles/{role-name}
	result = requests.get(url+"/admin/realms/" + realm + "/clients/" + clientId + "/roles/" + roleName, headers=head,proxies={'http':None})

	if result.status_code != 200:
  		print("getRole error : " + str(result.status_code) + " " + result.text)

	role = result.json()

	return role

def addRealmRolesToUser(url,user,password,realm, userId, roles):
	bearer = getKcBearer(url, user, password)
	head = prepareKcApiHeaders(bearer)
	
	# POST /admin/realms/{realm}/users/{userId}/role-mappings/realm
	result = requests.post(url + "/admin/realms/" + realm + "/users/" + userId + "/role-mappings/realm", json=roles, headers=head,proxies={'http':None})


	if result.status_code != 204:
  		print("addRealmRolesToUser return : " + str(result.status_code) + " " + result.text)

	return True

def addClientRoleToUser(url,user,password,realm, client, userId, roles):
	bearer = getKcBearer(url, user, password)
	head = prepareKcApiHeaders(bearer)

	#POST /admin/realms/{realm}/users/{id}/role-mappings/clients/{client}
	result = requests.post(url + "/admin/realms/" + realm + "/users/" + userId + "/role-mappings/clients/" + client, json=roles, headers=head,proxies={'http':None})

	if result.status_code != 204:
  		print("addClientRoleToUser return : " + str(result.status_code) + " " + result.text)

	return True

def getUser(url,user,password,realm, username):
	bearer = getKcBearer(url, user, password)
	head = prepareKcApiHeaders(bearer)
	result = requests.get(url+"/admin/realms/" + realm + "/users?username=" + username, headers=head,proxies={'http':None})

	if result.status_code != 200:
  		print("getUser return : " + str(result.status_code) + " " + result.text)

	user = result.json()

	return user

def deleteUser(url,user,password,realm,userId):
	bearer = getKcBearer(url, user, password)
	head = prepareKcApiHeaders(bearer)

	# DELETE /admin/realms/{realm}/users/{id}
	result = requests.delete(url+"/admin/realms/" + realm + "/users/" + userId,headers=head,proxies={'http':None})

	if result.status_code != 204:
  		print("deleteUser return : " + str(result.status_code) + " " + result.text)

	return True

def addUser(url,user,password,realm,userData):
	bearer = getKcBearer(url, user, password)
	head = prepareKcApiHeaders(bearer)

	result = requests.post(url+"/admin/realms/" + realm + "/users", json=userData,headers=head,proxies={'http':None})
	if result.status_code != 201:
		print("addUser return : " + str(result.status_code) + " " + result.text)

	return True

def addTempPassword(url,user,password,realm, userId, userPassword):
	bearer = getKcBearer(url, user, password)
	head = prepareKcApiHeaders(bearer)

	credentials = { "type": "password", "temporary": True, "value": userPassword }

	# PUT /admin/realms/{realm}/users/{id}/reset-password
	result = requests.put(url+"/admin/realms/" + realm + "/users/" + userId + "/reset-password", json=credentials,headers=head,proxies={'http':None})

	if result.status_code != 204:
  		print("addTempPassword return : " + str(result.status_code) + " " + result.text)

	return True

if __name__ == "__main__":

	parser = argparse.ArgumentParser(description='Import users to Keycloak from CSV')
	parser.add_argument("-f", "--file", dest="filename", help="CSV file that contains users", metavar="FILE")
	parser.add_argument("-c", "--config", dest="config", help="Config file", metavar="FILE")
	parser.add_argument("--delete", help="delete user list in CSV default add", action="store_true")
	parser.add_argument("-l", "--limit", help="limit CSV user to add", type=int)

	args = parser.parse_args()

	configFile="config.ini"
	if args.config:
		configFile=args.config

	csvFile = "users.csv"
	if args.filename:
		csvFile = args.filename

	configMap = setConfig(configFile)

	limit = 0
	if args.limit:
		limit = args.limit
	
	#exit()

	with open(csvFile) as csvfile:
		reader = csv.DictReader(csvfile)
		currentRow=0
		for csv_row in reader:
			
			if limit > 0 and currentRow >= limit: 
				break

			currentRow+=1
			
			userData = {
				"enabled": True,
			    "username": csv_row[configMap.csvMap.userName],
			    "email": csv_row[configMap.csvMap.email],
			    "firstName": csv_row[configMap.csvMap.firstName],
			    "lastName": csv_row[configMap.csvMap.lastName],
			    "emailVerified": True
			}

			if args.delete:
				user = getUser(configMap.admimUrl, configMap.adminLogin, configMap.adminPassword, configMap.realm, userData["username"])
				
				if len(user) == 1:
					deleteUser(configMap.admimUrl, configMap.adminLogin, configMap.adminPassword, configMap.realm,user[0]["id"])

			else:
				addUser(configMap.admimUrl, configMap.adminLogin, configMap.adminPassword, configMap.realm, userData)
				user = getUser(configMap.admimUrl, configMap.adminLogin, configMap.adminPassword, configMap.realm, userData["username"])

				if len(user) == 1:
					if(csv_row[configMap.csvMap.clientRole]):
						clientRole = getClientRole(configMap.admimUrl, configMap.adminLogin, configMap.adminPassword, configMap.realm, configMap.client, csv_row[configMap.csvMap.clientRole])
						addClientRoleToUser(configMap.admimUrl, configMap.adminLogin, configMap.adminPassword, configMap.realm, configMap.client, user[0]["id"], [clientRole])

					if(csv_row[configMap.csvMap.realmRole]):
						realmRole = getRealmRole(configMap.admimUrl, configMap.adminLogin, configMap.adminPassword, configMap.realm, csv_row[configMap.csvMap.realmRole])
						addRealmRolesToUser(configMap.admimUrl,configMap.adminLogin,configMap.adminPassword,configMap.realm, user[0]["id"], [realmRole])

					if(csv_row[configMap.csvMap.password]):
						addTempPassword(configMap.admimUrl,configMap.adminLogin,configMap.adminPassword,configMap.realm, user[0]["id"], csv_row[configMap.csvMap.password])
