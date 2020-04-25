import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()
channel.queue_declare(queue="hello1")
channel.basic_publish(exchange='',routing_key='hello1',body='i am hello1')

print("message published")

connection.close()