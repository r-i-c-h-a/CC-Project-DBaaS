import pika
import json
from pymongo import MongoClient
from datetime import datetime
from bson.json_util import dumps
from subprocess import check_output
import os
import sys
import subprocess

client = MongoClient("mongodb://worker-mongo:27017")

print(os.environ['NODE_TYPE'])

def write_callback(ch,method,properties,body):
    db = client.uber
    print("[x] received %r" %body)
    d_values = json.loads(body)
    collection = d_values["collection"]
    data = d_values["data"]
    method = d_values["method"]

    if(collection=="rides"):
        if(method=="post"):
            db.rides.insert(data)
        if(method=="join"):
            rideId = d_values["rideId"]
            db.rides.update({"rideId":rideId},{'$push':data})
        if(method=="delete"):
            db.rides.remove(data)
        if(method=="clear"):
            db.rides.remove({})

    if(collection=="users"):
        if(method=="put"):
            db.users.insert(data)
        if(method=="delete"):
            db.users.remove(data)
        if(method=="clear"):
            db.users.remove({})	
            
    channel_s.basic_publish(exchange='',routing_key='syncq',body=body)
    print("[x] published to syncq",body)



def read_callback(ch,method,properties,body):
	db = client.uber
	print("[x] received %r" %body)
	d_values = json.loads(body)
	collection = d_values["collection"]
	data = d_values["data"]
	method = d_values["method"]

	if(collection=="rides"):
		if(method=="get_all"):
			result=[] 
			cursor = list(db.rides.find(data,{"rideId":1,"created_by":1,"timestamp":1,"_id":0}))
			for i in cursor:
				timestamp = i['timestamp'].split(':')
				date = timestamp[0].split('-')
				time = timestamp[1].split('-')
				current_time = datetime.now()
				record_time = datetime(int(date[2]),int(date[1]),int(date[0]),int(time[2]),int(time[1]),int(time[0]))
				#print(record_time)
				# #print(current_time)
				if(record_time>=current_time):
					result.append(i)
			result = dumps(result)
		if(method=="get_ride"):
			result = dumps(db.rides.find(data,{"_id":0}))
		if(method=="get_rides_count"):
			result = str(db.rides.find().count()) 
		if(method=="get_user_rides"):
			result = dumps(db.rides.find(data))
		if(method=="get_id_rides"):
			result = dumps(db.rides.find(data))
		if(method=="get_id_rides_count"):
			result = str(db.rides.find(data).count())
		if(method=="get_all_rides"):
			result = dumps(db.rides.find())

	if(collection=="users"):
		if(method=="get_all"):
			result = dumps(db.users.find({},{"_id":0}))
            
	#print(result)
	resp_channel.basic_publish(exchange='',routing_key='responseq',body=result)



if(os.environ['NODE_TYPE']=="MASTER"):
    connection_s = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
    channel_s = connection_s.channel()
    channel_s.queue_declare(queue="syncq")

    connection_w = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
    channel_w = connection_w.channel()
    channel_w.queue_declare(queue="writeq")


    channel_w.basic_consume(queue="writeq", on_message_callback=write_callback, auto_ack=True)
    print("Waiting for write messages")
    channel_w.start_consuming()
else:
    resp_connection = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
    resp_channel = resp_connection.channel()
    resp_channel.queue_declare(queue="responseq") 

    connection_r = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
    channel_r = connection_r.channel()
    channel_r.queue_declare(queue="readq")


    channel_r.basic_consume(queue="readq", on_message_callback=read_callback, auto_ack=True)
    print("Waiting for read messages")

    subprocess.Popen([sys.executable, "sync_slave_worker.py"] ,close_fds=True,shell=False)  

    channel_r.start_consuming()
    
