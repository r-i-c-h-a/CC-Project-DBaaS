import pika
import json
import sys
import subprocess
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")



connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue="hello1")



def callback(ch,method,properties,body):
    #print("[x] received %r" %body)
    db = client.test   
    db.nlog.insert({"body":"hello11"})


channel.basic_consume(queue="hello1", on_message_callback=callback, auto_ack=True)
print("Waiting for messages from hello 1")

subprocess.Popen([sys.executable, "child.py"] ,close_fds=True,shell=False)

channel.start_consuming() 


