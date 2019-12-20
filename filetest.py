import json

global data
global jsonFile

def setInitLights():
    global data
    jsonFile = open('synapse_status.json','r')
    data = json.load(jsonFile)
    # jsonFile.close()

    

def updateJsonFile():
    global data
    global jsonFile
    # jsonFile = open('synapse_status.json','r+')
    print(data)
    data[0]['status'] = 'off'
    jsonFile.seek(0)
    json.dump(data,jsonFile)
    jsonFile.truncate()
    # print(data[0]['status'])
    # data['status'] = 'off'

    # jsonFile = open('filetest.json','w')
    # jsonFile.write(json.dumps(data))
    # jsonFile.close()

setInitLights()
updateJsonFile()

