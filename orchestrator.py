from flask import Flask, render_template,jsonify,request,abort
import requests
import json
from flask import Response
from bson.json_util import dumps
import pika
import os
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

path = os.path.basename(os.getcwd())
ismaster = lambda a: bool(a.startswith(path+"_master"))
isslave = lambda a: bool(a.startswith(path+"_slave"))
isworker = lambda a: bool(a.startswith(path+"_worker"))

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


@app.route('/api/v1/crash/master',methods=["POST"])
def kill_master():
    workers = []
    client = docker.from_env()
    conts = client.containers.list(all)
    cont_pid = dict()
    output = []
    pids = []
    for i in conts:
         output.append([i,i.attrs['Config']['Image']])
         pids.append(int(i.attrs['State']['Pid']))
         # print(i.attrs['State']['Pid'],i.attrs['Config']['Image'])
    #output = [i.strip('\n') for i in os.popen('docker ps --format "{{.Names}}"').readlines()]
    final_pid = []
    for i in range(len(output)):
        if (ismaster(output[i][1]) or isslave(output[i][1]) or isworker(output[i][1])) and pids[i]!=0:
            workers.append(output[i])
            final_pid.append(pids[i])
    #pids = [int(os.popen('docker inspect --format="{{.State.Pid}}" '+i).read().strip('\n')) for i in workers]
    #pass
    print(final_pid,workers)
    to_kill = workers[final_pid.index(min(final_pid))][0]
    #flag = os.system("sudo docker kill "+to_kill)
    to_kill.kill()
    #if flag:
    return "{}"
    #pass


@app.route('/api/v1/crash/slave',methods=["POST"])
def kill_highest_slave():
    workers = []
    client = docker.from_env()
    conts = client.containers.list(all)
    cont_pid = dict()
    output = []
    pids = []
    for i in conts:
         output.append([i,i.attrs['Config']['Image']])
         pids.append(int(i.attrs['State']['Pid']))
         # print(i.attrs['State']['Pid'],i.attrs['Config']['Image'])
    #output = [i.strip('\n') for i in os.popen('docker ps --format "{{.Names}}"').readlines()]
    final_pid = []
    for i in range(len(output)):
        if (ismaster(output[i][1]) or isslave(output[i][1]) or isworker(output[i][1])) and pids[i]!=0:
            workers.append(output[i])
            final_pid.append(pids[i])
    #pids = [int(os.popen('docker inspect --format="{{.State.Pid}}" '+i).read().strip('\n')) for i in workers]
    #pass
    print(final_pid,workers)
    to_kill = workers[final_pid.index(max(final_pid))][0]
    #flag = os.system("sudo docker kill "+to_kill)
    to_kill.kill()
    #if flag:
    return "{}"
    #pass


@app.route('/api/v1/worker/list',methods=["GET"])
def get_sorted_workers_pid():
    workers = []
    client = docker.from_env()
    conts = client.containers.list(all)
    cont_pid = dict()
    output = []
    pids = []
    for i in conts:
         output.append(i.attrs['Config']['Image'])
         pids.append(int(i.attrs['State']['Pid']))
         # print(i.attrs['State']['Pid'],i.attrs['Config']['Image'])
    #output = [i.strip('\n') for i in os.popen('docker ps --format "{{.Names}}"').readlines()]
    final_pid = []
    for i in range(len(output)):
        if ismaster(output[i]) or isslave(output[i]) or isworker(output[i]):
            workers.append(output[i])
            final_pid.append(pids[i])
    #pids = [int(os.popen('docker inspect --format="{{.State.Pid}}" '+i).read().strip('\n')) for i in workers]
    response = sorted(final_pid)
    return(json.dumps(response))
    #pass





if __name__ == '__main__':	
	app.debug=True
	app.run(host='0.0.0.0')
