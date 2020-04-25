import pika
import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")


connection_2 = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel_2 = connection_2.channel()
channel_2.queue_declare(queue="hello2")

def callback_2(ch,method,properties,body):
    #print("[x] received %r" %body)
    db = client.test
    db.logs.insert({"body":"hello22"})


channel_2.basic_consume(queue="hello2", on_message_callback=callback_2, auto_ack=True)
print("Waiting for messages from hello 2")
channel_2.start_consuming() 