import requests
import websocket
import argparse
import json
from requests.auth import HTTPBasicAuth
import logging
from httplib import HTTPConnection

#subscribe to presence events and print out the notifications
def subscribe(klRootUrlWebSocket,klRestUserRootUrl,username,password):

	subscriptionUrl,notificationUrl=getWebSocketSubscription(klRestUserRootUrl,username,password,["Presence"])
	notificationUrl=klRootUrlWebSocket+notificationUrl
	ws=websocket.create_connection(notificationUrl)
	print "Listening on ",notificationUrl

	while(True):
		notifyResponseData=ws.recv()
		notifyResponseDict=json.loads(notifyResponseData)["notificationMessage"]
		if(notifyResponseDict["eventType"]=="presenceWatcher"):
			presenceData=notifyResponseDict["presenceWatcherNotificationParams"]
			presenceNoteActivity=""
			if "note" in presenceData.keys():
				presenceNoteActivity=presenceData["note"]
			elif "activity" in presenceData.keys():
				presenceNoteActivity=presenceData["activity"]
			print presenceData["name"],presenceData["status"],presenceNoteActivity
			
		else:
			print notifyResponseDict
			
	ws.close()

#utility to send subscription request
def getWebSocketSubscription(klRestUserRootUrl,username,password,services):
	subscriptionUrl=None
	notificationUrl=None

	# request dictionary object built and then dumped into JSON
	subscribeRequest={}
	subscribeRequest["expires"]="7200"
	subscribeRequest["localization"]="English_US"
	subscribeRequest["notificationType"]="WebSocket"
	subscribeRequest["service"]=services
	subscribeRequest={"subscribeRequest":subscribeRequest}
	print subscribeRequest

	# make the subscription request 
	subscribeResponse=requests.post(klRestUserRootUrl+"subscription",json=subscribeRequest,auth=HTTPBasicAuth(username,password))
	subscribeResponse=subscribeResponse.json()["subscribeResponse"]

	if(subscribeResponse["statusCode"]==0):
		subscriptionUrl=subscribeResponse["subscription"]
		notificationUrl=subscribeResponse["subscriptionParams"]["notificationChannel"]

	return subscriptionUrl,notificationUrl

def publish(klRestUserRootUrl,username,password,data):

	presenceRequest={}
	presenceRequest["status"]="open"
	presenceRequest["activity"]="other"
	presenceRequest["note"]=data
	presenceRequest={"presenceRequest":presenceRequest}

	print presenceRequest
	presenceResponse=requests.post(klRestUserRootUrl+"presence",json=presenceRequest,auth=HTTPBasicAuth(username,password))
	print presenceResponse.json()

if __name__ == "__main__":

	parser = argparse.ArgumentParser()
	parser.add_argument("username")
	parser.add_argument("password")
	parser.add_argument("httpHostColonPort")
	parser.add_argument("wsHostColonPort")
	parser.add_argument("--publish",default=None,help="provide data to publish or omit argument to subscribe")
	parser.add_argument("--http",action="store_true")

	args = parser.parse_args()

	if args.http:
		HTTPConnection.debuglevel = 1
		logging.basicConfig() 
		logging.getLogger().setLevel(logging.DEBUG)
		requests_log = logging.getLogger("requests.packages.urllib3")
		requests_log.setLevel(logging.DEBUG)
		requests_log.propagate = True

	klRootUrlHttp="https://"+args.httpHostColonPort
	klRootUrlWebSocket="wss://"+args.wsHostColonPort
	klRestUserRootUrl=klRootUrlHttp+"/rest/version/1/user/"+args.username+"/"

	if args.publish is None:
		subscribe(klRootUrlWebSocket,klRestUserRootUrl,args.username,args.password)

	else:
		publish(klRestUserRootUrl,args.username,args.password,args.publish)
