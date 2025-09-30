import torch
import json
from data_loader import load_data
from robot import Robot
import sys
import matplotlib.pyplot as plt

def Create(js):
    JSON=json.loads(js)
    username=JSON['username']
    stock=JSON["targeted market"]
    input=JSON['input']
    features=input['features']
    args=input['args']
    input_time_protocol=input['time protocol']
    input_frequency=input_time_protocol['frequency']
    input_period=input_time_protocol['period']
    output=JSON['output']
    output_time_protocol=output['time protocol']
    output_frequency=output_time_protocol['frequency']
    output_period=output_time_protocol['period']

    
    return Robot(username,stock,input_frequency,input_period,output_frequency,output_period,features,args)


def buildAndStore(JSON):
    robot=Create(JSON)
    robot.to_rbt()
    return 1




    
def predict(JSON):
    username=JSON['username']
    robot=Robot(train=False)
    robot.read_rbt(username)
    return robot.generate()

def back(JSON):
    username=JSON['username']
    robot=Robot(train=False)
    robot.read_rbt(username)
    return robot.backtest()
def test(username,stock,n):
    js=json.dumps({'username':username,
                   'targeted market': stock,
                   'input':
                   {
                       'features':["Moving Average","Moving Average Convergence Divergence"],
                       'args': {'t_MA':5,'t1':5,'t2':10,'t_EMA':5,},
                       'time protocol':
                        {
                            'frequency':'1min',
                            'period':
                            {
                                'start':'9:00',
                                'end':'10:00'
                            }

                        }
                   },
                   'output':
                   {
                       'time protocol':
                        {
                            'frequency':'1min',
                            'period':
                            {
                                'start':'17:00',
                                'end':'18:00'
                            }

                        }
                       
                   }
                   }
                  )
    if(n):
        print(buildAndStore(js))
        return
    
    # x=predict(json.loads(js))
    # print(x)
    # plt.plot(x[0][0])
    # plt.show()
    back(json.loads(js))
if __name__=="__main__":
    test(sys.argv[1],sys.argv[2],int(sys.argv[3]))