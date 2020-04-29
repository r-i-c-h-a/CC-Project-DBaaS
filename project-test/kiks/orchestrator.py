from flask import Flask, render_template,jsonify,request,abort
import requests
import json
from flask import Response
from bson.json_util import dumps
import pika
import docker
app = Flask(__name__)

connection_r = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
channel_r = connection_r.channel()
channel_r.queue_declare(queue="readq")

connection_w = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
channel_w = connection_w.channel()
channel_w.queue_declare(queue="writeq")

resp_connection = pika.BlockingConnection(pika.ConnectionParameters(host='rmq'))
resp_channel = resp_connection.channel()
resp_channel.queue_declare(queue="responseq")

#creating a master and slave container
client= docker.from_env()
#print("killing existing containers")
#a=list()
#a=client.containers.list({'status':'running'})
#print(a)
#for i in a:
#	i.kill()

print("spawning new container dynamically")

container1 = client.containers.run(image='workers:latest', name='a23',command='sh -c "sleep 40 && python3 worker.py"' ,environment=["NODE_TYPE=SLAVE"],restart_policy= {'Name':'on-failure'},network='kiks_default',links={'slaves-mongo':'slave'},detach=True)
container2 = client.containers.run(image='workers:latest' , name='a24',command='sh -c "sleep 40 && python3 worker.py"' ,environment=["NODE_TYPE=MASTER"],restart_policy = {'Name':'on-failure'},network='kiks_default' ,links={'maste-mongo':'master'},detach=True)
container3 = client.containers.run(image='mongo:latest' , name='slaves-mongo',restart_policy = {'Name':'on-failure'},detach=True)
container4 = client.containers.run(image='mongo:latest' , name='maste-mongo',restart_policy = {'Name':'on-failure'},detach=True)
container4 = client.containers.run(image='workers:latest', name='a25',command='sh -c "sleep 40 && python3 worker.py"',environment=["NODE_TYPE=SLAVE"],restart_policy={'Name':'on-failure'},network='kiks_default',detach=True)

a=list()
a=client.containers.list(filters={'ancestor':'workers:latest'})
b=client.containers.list(filters={'status':'running'})
c=[val for val in a if val in b]
print(c)

class Callback(object):
    def __init__(self,body):
        self.body=body
    def response_callback(self, ch, method, properties, body):
        print("[x] received %r" %body)
        d = body.decode("utf-8")
        d = json.loads(d)
        self.body = d
        resp_channel.stop_consuming()

@app.route('/api/v1/db/read',methods=["POST"])
def read():
    d_values = json.dumps(request.get_json())
    channel_r.basic_publish(exchange='',routing_key='readq',body=d_values)
    print("added to readq")
    #response = resp_channel.basic_get("responseq")[2]  #FIX ME!!
    C = Callback("null")
    resp_channel.basic_consume(queue="responseq", on_message_callback=C.response_callback, auto_ack=True)
    print("Waiting for response messages")
    resp_channel.start_consuming() 
    response = C.body
    #print("Response:",response)
    
    return(json.dumps(response))



@app.route('/api/v1/db/write',methods=["POST"])
def write():
    d_values = json.dumps(request.get_json())
    channel_w.basic_publish(exchange='',routing_key='writeq',body=d_values)
    print("added to writeq")
    return "{}"


@app.route('/api/v1/crash/master')
def kill_master():
    pass


@app.route('/api/v1/crash/slave')
def kill_highest_slave():
    pass


@app.route('/api/v1/worker/list')
def get_sorted_workers_pid():
    pass





if __name__ == '__main__':	
	app.debug=True
	app.run(host='0.0.0.0',use_reloader=False)
