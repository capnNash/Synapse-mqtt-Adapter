#############################################################################
#### Clearblade-Synapse-Adapter.py                                    #######
# Description: A Clearblade mqtt adapter that controls the          #########
#              synapse light nodes SN087 over synapse network     ###########
#              and publishes data to IoTRight platform over mqtt ############
# Author: Anish Nesarkar                                        #############
#############################################################################

from clearblade.ClearBladeCore import System, Query
import random
import time
from clearblade.ClearBladeCore import cbLogs
import json
import os
from snapconnect import snap
global comm
data = []
responseFlag = False
# global dim_level
addressMap = {
            '08160B' : "\x08\x16\x0B",
            '081CC0' : "\x08\x1C\xC0"           
        }
dim_level = 0


# Disable console logging
cbLogs.DEBUG = False
cbLogs.MQTT_DEBUG = False
# System credentials
SystemKey = "a8ec94c80ba2fba4d4e5c2d1f0f701"
SystemSecret = "A8EC94C80BCA8BFBD28AECD6CFA801"
url = "https://platform.iotright.com"

mySystem = System(SystemKey, SystemSecret, url, safe=False)

# Log in as Anish
anish = mySystem.User("anesarkar@iotright.com", "anish9461")

# Use Anish to access a messaging client
mqtt = mySystem.Messaging(anish)

# Query the device to get all the lights
q = Query()
q.equalTo("type","light")
devices = mySystem.getDevices(anish, q)
nodes = []
for device in devices:
    nodes.append(device['light_id'])

# Set Initial light state
def setInitLights():
    global data
    jsonFile = open('synapse_status.json','r')
    data = json.load(jsonFile)
    jsonFile.close()
    
    global dim_level
    global responseFlag
    # print(data)
    for lightData in data:
        
        # >=============< rpc call to set the target light node >=============<
        if(str(lightData['status']) != 'null'):
            if str(lightData['status']) == 'on':
                # set on the light
            
                print('setting on')
                while not responseFlag:                 
                    comm.rpc(addressMap[str(lightData['nodeaddress'])],'set_dim_level',100)
                    poll()
                responseFlag = False
            else:
                # set off the light
                print('setting off')
                while not responseFlag:                  
                    comm.rpc(addressMap[str(lightData['nodeaddress'])],'set_dim_level',0)
                    poll()
                responseFlag = False
        elif str(lightData['dim']) != 'null':
            # dim the lights
            print('dimming the lights')
            while not responseFlag:
                comm.rpc(addressMap[str(lightData['nodeaddress'])],'set_dim_level',int(lightData['dim']))
                poll()
            # return the status
            responseFlag = False
    # jsonFile.close()

# update the json file
def updateinitLights(response):  
    jsonFile = open('synapse_status.json','w')
    for lightData in data:
        # print(str(lightData))
        if str(lightData['nodeaddress']) == response['nodeaddress']:
            print('matched')
            lightData['status'] = response['status']
            lightData['dim']  = response['dim']
            break
    jsonFile.write(json.dumps(data))
    jsonFile.close()

# Get the dim level of the lights
def get_dim(level):
    global dim_level
    dim_level = level
    print("dim level ",dim_level)

def writePidFile():
    pid = str(os.getpid())
    currentFile = open('/var/run/synapse.pid', 'w')
    currentFile.write(pid)
    currentFile.close()

# Set up callback functions
def on_connect(client, userdata, flags, rc):
    # When we connect to the broker, subscribe to the following topic paths
 
    # Subscribe to all the node topic paths
    # for n in nodeaddress:
    #     client.subscribe("/lighting/"+n)
    client.subscribe("/lighting/nodes/#")
    
def poll():
    timeout = time.time() + 2
    while time.time() < timeout:
        comm.poll()


def rpcSuccess(obj):
    global responseFlag
    responseFlag = True
    
def on_message(client, userdata, message):
    global dim_level
    global responseFlag  
    # Message parsing 
    data = json.loads((message.payload).decode('utf8').replace("'",'"'))
    outputDataString = json.dumps(data,indent=4,sort_keys=True)
    outputDataJson = json.loads(outputDataString)
    
    # Get the required node address from the topic path  
    nodeaddress = str((message.topic).split('/')[2])
    print("nodeaddress: ",nodeaddress)
    print(type(nodeaddress))
    response = {}
    log = True
    # parse the message payload
    #TODO: Change rpc calling for all nodes for nodeaddress '#'
    if nodeaddress == '#':
        log = False
        if outputDataJson['action'] == 'set':
            for n in nodes:
                response[n] = {}
                comm.rpc(n,'setter',outputDataJson)
                # output = rpc(n,setter,outputDataJson)
                # response[n] = output
        elif outputDataJson['action'] == 'get':
            for n in nodes:
                response[n] = {}
                # output = { 'status' : 'on', 'dim' : '30'}
                comm.rpc(n,'setter',outputDataJson)
                # output = rpc(n,getter,outputDataJson)
                # response[n] = output
            mqtt.publish("lighting/get", json.dumps(response))
                     
        
    elif outputDataJson['action'] == 'get':
        print("In getter")
        #>-------------------< test purpose >--------------------<
        # response = {}
        # response['nodeaddress'] = nodeaddress
        # response['action'] = 'get'
        # response['status'] = 'on'
        # response['dim'] = '70'
        #>-------------------------------------------------------<
        
        # >=============< rpc call to get the target light node >=============<
        # address type '\x08\x1C\xC0'
        while not responseFlag:
            comm.rpc(addressMap[nodeaddress],"get_dim_level")
            poll()
        responseFlag = False
        response['dim'] = dim_level
        response['nodeaddress'] = nodeaddress
        response['action'] = 'get'
        mqtt.publish("lighting/get/"+nodeaddress, json.dumps(response))
        print("message published")
        
    elif outputDataJson['action'] == 'set':
        print("In setter")
        #>-------------------< test purpose >--------------------<
        # response = {}
        # response['nodeaddress'] = nodeaddress
        # response['action'] = 'set'
        # response['status'] = 'on'
        # response['dim'] = '70'
        #>-------------------------------------------------------<
        
        # >=============< rpc call to set the target light node >=============<
        if(outputDataJson['status'] != 'null'):
            if outputDataJson['status'] == 'on':
                # set on the light
            
                print('setting on')
                while not responseFlag:                 
                    comm.rpc(addressMap[nodeaddress],'set_dim_level',100)
                    poll()
                responseFlag = False
                response['dim'] = '100'
                # return the status
                response['status'] = 'on'
            else:
                # set off the light
                print('setting off')
                while not responseFlag:                  
                    comm.rpc(addressMap[nodeaddress],'set_dim_level',0)
                    poll()
                responseFlag = False
                response['dim'] = '0'
                response['status'] = 'off'
        elif outputDataJson['dim'] != 'null':
            # dim the lights
            print('dimming the lights')
            while not responseFlag:
                comm.rpc(addressMap[nodeaddress],'set_dim_level',int(outputDataJson['dim']))
                poll()
            # return the status
            responseFlag = False
            response['dim'] = outputDataJson['dim']
            # if dim_level == 0:
            #     response['status'] = 'off'
            # else:
            #     response['status'] = 'on'
            response['status'] = 'null'
        response['nodeaddress'] = nodeaddress
        response['action'] = 'set'
        updateinitLights(response)
        
    # >==============< Logging in clearblade system >=============<
    if log:    
        mqtt.publish("lighting/status", json.dumps(response))
    # >------------------------------------------------------------<
    
# Connect callbacks to client
mqtt.on_connect = on_connect
mqtt.on_message = on_message

writePidFile()
# Connect to the mqtt broker
mqtt.connect()
comm = snap.Snap(funcs={'get_dim':get_dim, 'rpcSuccess':rpcSuccess})
comm.open_serial(1,'/dev/snap0')
print("MQTT connected")
# Set initial Light State
setInitLights()
while(True):
    time.sleep(1)  # wait for messages
# mqtt.disconnect()
# print("mqtt disconnected")
