from flask import Flask, render_template,jsonify,request,abort
import requests
import json
from flask import Response
from bson.json_util import dumps
import pika
import docker
import datetime
import math
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
import os


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
ismastermongo = lambda a: bool(a.startswith("master-mongo"))
isslave = lambda a: bool(a.startswith(path+"_slave"))
isslavemongo = lambda a: bool(a.startswith("slave-mongo"))
isworker = lambda a: bool(a.startswith(path+"_worker"))

client= docker.from_env()
client.containers.run(image='mongo:latest' , name='slave-mongo1',restart_policy = {'Name':'on-failure'},detach=True,network='project_default')
client.containers.run(image='workers:latest', name='slave1',command='sh -c "sleep 40 && python3 slave.py"',environment=["NODE_TYPE=SLAVE"],restart_policy={'Name':'on-failure'},links={'slave-mongo1':'slave'},network='project_default',detach=True)



class Scale(object):
    total = 0
    count = 0
    number = 1

    def check(self):
        print("################hello in trigger#################")
        a=list()
        b=list()
        c=list()
        a=client.containers.list(filters={'ancestor':'workers:latest'})
        b=client.containers.list(filters={'status':'running'})
        c=[val for val in a if val in b]
        containers_needed = math.ceil(self.count/20)
        containers_running = len(c)-2 #TODO: Write command to count current containers
        self.count = 0
        if(containers_needed>containers_running):
            for i in range(containers_needed-containers_running):
                self.number+=1
                container_name = "slave"+str(self.number)
                mongo_name = "slave-mongo"+str(self.number)
                #TODO: call container and mongo spawning commands
                #client.containers.run(image='workers:latest', name=container_name,command='sh -c "sleep 40 && python3 slave.py"',environment=["NODE_TYPE=SLAVE"],restart_policy={'Name':'on-failure'},network='project_default',links={mongo_name:'slave'},detach=True)
                #client.containers.run(image='mongo:latest',name=mongo_name,restart_policy = {'Name':'on-failure'},detach=True)

        elif(containers_needed<containers_running):
            #TODO: delete containers and theri respective mongo containers
            pass



class Callback(object):
    def __init__(self,body):
        self.body=body
    def response_callback(self, ch, method, properties, body):
        print("[x] received %r" %body)
        d = body.decode("utf-8")
        d = json.loads(d)
        self.body = d
        resp_channel.stop_consuming()


S = Scale()


@app.route('/api/v1/db/read',methods=["POST"])
def read():
    S.total+=1
    if(request.get_json()["method"] not in ["get_id_rides_count","get_all_rides","get_id_rides","get_user_rides"]):
        S.count+=1
    if(S.total==1):
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=S.check, trigger="interval", seconds=120)
        scheduler.start()  
        atexit.register(lambda: scheduler.shutdown())  


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
    client = docker.from_env()
    conts = client.containers.list(all)
    for i in conts:
        if ismaster(i.attrs['Config']['Image']):
            to_kill_master = i
        #print("##################",i.attrs['Names'])
        #if ismastermongo(i.attrs['Config']['Image']):
        #   to_kill_mongo = i
    to_kill_master.kill()
    client.containers.get('master-mongo').kill()
    return "{}"


@app.route('/api/v1/crash/slave',methods=["POST"])
def kill_highest_slave():
        client = docker.from_env()
    conts = client.containers.list(all)
    high = 0
    slavemongo = []
    to_kill_slave = ""
    for i in conts:
        if high < int(i.attrs['State']['Pid']) and isslave(i.attrs['Config']$
            to_kill_slave = i
            name_to_kill = i.attrs['Config']['Image']
        if isslavemongo(i.attrs['Config']['Image']) and int(i.attrs['State']$
            slavemongo.append([i,i.attrs['Config']['Image']])
    slave_no = name_to_kill.partition("slave")[2]
    slave_no = slave_no.partition('_')[0]
    print("###############################",slave_no)
    for i in slavemongo:
        if(i[1].endswith(slave_no)):
            to_kill_mongo = i[0]
    if to_kill_slave != "":
        to_kill_slave.kill()
        client.containers.get('slave-mongo'+slave_no).kill()
        #to_kill_mongo.kill()
        return "{}"
    else:
        return "['Nothing to kill']"


@app.route('/api/v1/worker/list',methods=["GET"])
def get_sorted_workers_pid():
    client = docker.from_env()
    conts = client.containers.list(all)
    pids = []
    for i in conts:
        if ismaster(i.attrs['Config']['Image']) or isslave(i.attrs['Config']['Image']):
             pids.append(int(i.attrs['State']['Pid']))
    response = sorted(pids)
    return(json.dumps(response))


if __name__ == '__main__':	
	app.debug=True
	app.run(host="0.0.0.0",use_reloader=False)
