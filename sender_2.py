import pika

connection_2 = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel_2 = connection_2.channel()
channel_2.queue_declare(queue="hello2")
channel_2.basic_publish(exchange='',routing_key='hello2',body='i am hello2')

print("message published")

connection_2.close()