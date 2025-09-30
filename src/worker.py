import multiprocessing.process
import threading as th
import pika
import json
from services import *
import multiprocessing

def request(req,message_dict,reply_to,correlation_id):
    if(req.lower()=='create'):
        print("Creating robot for",message_dict['username'])
        buildAndStore(json.dumps(message_dict))

        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        ch = connection.channel()

        try:
            ch.basic_publish(exchange='',
                                routing_key=reply_to,
                                properties=pika.BasicProperties(correlation_id=correlation_id),
                                body=json.dumps({"Type":'Create',"Status":"Done"}))
        except:
            ch.close()      # Closes the channel
            connection.close()
        
    elif(req.lower()=="Predict"):
        result=predict(message_dict)
        result=result.tolist()
        message = json.dumps({"values": result})
        ch.basic_publish(exchange='',
                            routing_key=reply_to,
                            properties=pika.BasicProperties(correlation_id=correlation_id),
                            body=message)
    
class Worker:
    def __init__(self,id):
        self.id=id
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        self.channel=channel
        self.connection=connection

        self.queue_name='rpc_queue'
        channel.queue_declare(queue=self.queue_name)
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(queue=self.queue_name,on_message_callback=self.handle_request,auto_ack=True)
        print(f"Server:{self.id} is running")
        self.channel.start_consuming()

    def handle_request(self,ch,method,props,body):
        message_dict = json.loads(body.decode('utf-8'))
        print(message_dict)
        p=th.Thread(target=request,args=(message_dict['req'],message_dict,props.reply_to,props.correlation_id,))
        p.start()

        


def main(args=None):
    worker=Worker(args)
    

if __name__=="__main__":
    main()