import torch
from model import Model
import json
from data_loader import load_data,today,load_chunk,load_test,load_train_test_data
import pickle
# from generator import train_estimator,Generator1D
from RCNN import train_estimator,RCNN,generate
from cnn_vae import CNNVAE, train_vae
from technical_tools import train_EncoderDecoderPredictor, EncoderDecoderPredictor,EncoderDecoderPredictorLSTM
import matplotlib.pyplot as plt
from tools import *
import numpy as np

import torch

def directional_accuracy(y_true: torch.Tensor, y_pred: torch.Tensor) -> float:
    """
    Computes directional accuracy (hit rate) between actual and predicted values.
    
    y_true: (N,) actual values
    y_pred: (N,) predicted values
    """
    # Compute returns (differences)
    true_diff = torch.sign(y_true.diff(dim=-1))
    pred_diff = torch.sign(y_pred.diff(dim=-1))  # prediction vs last true

    # Boolean match
    hits = (true_diff == pred_diff).float()
    
    return hits.mean()

def spearman_corr(x: torch.Tensor, y: torch.Tensor) -> float:
    """
    Computes Spearman rank correlation between two 1D tensors.
    
    Args:
        x: (N,) tensor
        y: (N,) tensor
    
    Returns:
        Spearman correlation coefficient (float)
    """
    # Convert to ranks
    def rankdata(a: torch.Tensor) -> torch.Tensor:
        # sort indices
        sorted_idx = torch.argsort(a)
        ranks = torch.zeros_like(sorted_idx, dtype=torch.float)
        ranks[sorted_idx] = torch.arange(1, len(a) + 1, dtype=torch.float, device=a.device)
        return ranks

    rx = rankdata(x)
    ry = rankdata(y)

    # Pearson on ranks
    rx_mean = rx.mean()
    ry_mean = ry.mean()
    num = torch.sum((rx - rx_mean) * (ry - ry_mean))
    den = torch.sqrt(torch.sum((rx - rx_mean) ** 2) * torch.sum((ry - ry_mean) ** 2))
    return (num / den)

def kendall_tau(x: torch.Tensor, y: torch.Tensor) -> float:
    """
    Compute Kendall's tau correlation coefficient between two 1D tensors.
    
    Args:
        x: (N,) tensor
        y: (N,) tensor
    
    Returns:
        Kendall's tau coefficient (float)
    """
    n = x.size(0)
    assert n == y.size(0), "x and y must have same length"

    # Pairwise comparisons
    concordant, discordant = 0, 0
    for i in range(n - 1):
        for j in range(i + 1, n):
            dx = x[j] - x[i]
            dy = y[j] - y[i]
            prod = dx * dy
            if prod > 0:
                concordant += 1
            elif prod < 0:
                discordant += 1
            # ties (prod == 0) ignored

    tau = (concordant - discordant) / (0.5 * n * (n - 1))
    return torch.FloatTensor([tau])
class Robot:
    def __init__(self,name=None,stockname=None,inputFrequency=None,inputPeriod=None,outputFrequency=None,outputPeriod=None,features=None,args=None,train=True):
        if train:
            self.file=f"./robots/{name}"
            self.name=name
            self.stock=stockname
            self.inputFrequency=inputFrequency
            self.outputFrequency=outputFrequency
            self.inputPeriod=inputPeriod
            self.outputPeriod=outputPeriod
            self.features=features
            self.args=args
            # src,d_in,_=load_data(stockname,inputFrequency,inputPeriod,features,args)
            # src,d_in,_=load_data(stockname,inputFrequency,inputPeriod)
            # trgt,d_out,_=load_data(stockname,outputFrequency,outputPeriod)
            src,trgt=load_train_test_data("./Histories/test_train_datasets",stock=self.stock,pattern="_train.csv",start=inputPeriod['start'],end=inputPeriod['end'],trgt_start=outputPeriod['start'],trgt_end=outputPeriod['end'],days=10)
            # VAE_data=load_chunk(stockname,trgt.size(1)).unsqueeze(-1)
            if(src.size(0)!=trgt.size(0)):
                print("warning: src and trgt have different number of days, truncating to the smaller one")
                raise
                tmp=min(src.size(0),trgt.size(0))
                src=src[-tmp:]
                trgt=trgt[-tmp:]
            
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            # self.model=Model(len(self.features)+1,64,1,num_layers=2).to(device)
            # self.model.train(src,trgt,VAE_data,self.features,self.args)
            
            # src=src.permute(0,2,1)
            # trgt=trgt.permute(0,2,1)
            
            src=src.unsqueeze(2)
            trgt=trgt.unsqueeze(1)

            self.seq_len=trgt.size(-1)
            self.input_dim=src.size(-1)
            # self.model=train_vae(src[:,:-1],src[:,-1].unsqueeze(1),trgt)
            # self.model=train_estimator(src[:,:-1,:],src[:,-1,:].unsqueeze(1),trgt,self.file)
            # self.model=train_estimator(src[:,:,:],src[:,-1,:].unsqueeze(1),trgt,self.file)
            self.model=train_EncoderDecoderPredictor(src,trgt,self.file,LSTM=True)


    def to_rbt(self):
        jsn={
            'file':self.file,
            'stock':self.stock,
            'input frequency':self.inputFrequency,
            'output frequency': self.outputFrequency,
            'input period': self.inputPeriod,
            'output period': self.outputPeriod,
            'features': self.features,
            'args': self.args,
            'seq len': self.seq_len,
            'input dim' : self.input_dim

        }

        with open(self.file+".rbt","w") as file:
            file.write(json.dumps(jsn))
        self.save_model()            
        
    def read_rbt(self,name):
        with open(f"./robots/{name}.rbt","rb") as file:
            model=json.load(file)
        self.file=model['file']
        self.stock=model['stock']
        self.inputFrequency=model['input frequency']
        self.outputFrequency=model['output frequency']
        self.inputPeriod=model['input period']
        self.outputPeriod=model['output period']
        self.features=model['features']
        self.args=model['args']
        self.seq_len=model['seq len']
        
        self.input_dim=model['input dim']
        # self.model=Generator1D(361,64,2,181)
        # self.model=RCNN(8,len(self.features)+1,64,512,0)
        # self.model=Generator1D(61,64,2,61)
        # self.model=CNNVAE(input_dim=self.seq_len, latent_dim=64)
        self.model=EncoderDecoderPredictorLSTM(self.input_dim,self.seq_len,in_channel=1,out_channel=1)
        self.load_model()
    
    def save_model(self):
        """Save the model's state dict separately (PyTorch model)."""
        torch.save(self.model.state_dict(), self.file+'.nn')


    def load_model(self):
        """Load the model's state dict from a file (if separate from robot)."""
        self.model.load_state_dict(torch.load(self.file+'.nn'))
    def generate(self):
        data=today(self.stock,self.inputPeriod['start'],self.inputPeriod['end'],days=13).permute(0,2,1)[:-1]

        # data=gaussian_smooth_1d(data.squeeze(1)).unsqueeze(1)
        data=(data-data.mean(dim=-1,keepdim=True))/(data.std(dim=-1,keepdim=True)+1e-4)

        trgt=today(self.stock,self.outputPeriod['start'],self.outputPeriod['end'],days=3).permute(0,2,1)[0,:,:]
        trgt=(trgt-trgt.mean(dim=-1,keepdim=True))/(trgt.std(dim=-1,keepdim=True)+1e-4)
        # trgt=gaussian_smooth_1d(trgt.squeeze(1)).unsqueeze(1)
        # data=gaussian_smooth_1d(data.squeeze(1)).unsqueeze(1)
        
        # data=today(self.stock,self.outputPeriod['start'],self.outputPeriod['end'],self.features,self.args,self.inputFrequency).permute(0,2,1)

        with torch.no_grad():
            res= self.model(data)

        # print(labelise(trgt.squeeze(1)))
        # plt.plot(trgt[0,0])
        # plt.plot(res[0,0])
        # plt.show()
        # raise
        # # results=list()
        # # for i in range(30):
        # #     results.append(self.model(data))
        # # res=torch.stack(results).mean(dim=0)

        # return res
        
    def backtest(self):
        
        start=self.inputPeriod['start']
        end=self.inputPeriod['end']
        src,trgt = load_train_test_data("./Histories/test_train_datasets",stock=self.stock,pattern="_test.csv",start=start,end=end,trgt_start=self.outputPeriod['start'],trgt_end=self.outputPeriod['end'],days=10)
        l=F.mse_loss
        idgmPerf,gbmPerf = out_of_sample(src[:,-1,:].squeeze(1),trgt.squeeze(1),l)
        print(f"src shape : {src.shape}, trgt shape : {trgt.shape}")

        # src=torch.stack([gaussian_smooth_1d(s) for s in src])
        # trgt=gaussian_smooth_1d(trgt)

        src=(src-src.mean(dim=-1,keepdim=True))/(src.std(dim=-1,keepdim=True)+1e-4)
        trgt=(trgt-trgt.mean(dim=-1,keepdim=True))/(trgt.std(dim=-1,keepdim=True)+1e-4)
        # trgt=torch.log(trgt[:,1:]/(trgt[:,:-1]+1e-4))

        src=src.unsqueeze(2)
        trgt=trgt.unsqueeze(1)
        with torch.no_grad():
            preds=self.model(src)
        # argmaxes,argmins,bases=find_stationnary_points(src[:,-1,:].squeeze(1))
        # preds=(preds-preds.mean(dim=-1,keepdim=True))/(preds.std(dim=-1,keepdim=True)+1e-4)
        # preds=gaussian_smooth_1d(preds.squeeze(1)).unsqueeze(1)
        # trgt=(trgt-trgt.mean(dim=-1,keepdim=True))/(trgt.std(dim=-1,keepdim=True)+1e-4)
        # preds_sign=preds.sign()
        trgt_sign=trgt.sign()
        # acc=(preds_sign==trgt_sign).float().mean()
        preds_diff=preds.diff(dim=-1)
        trgt_diff=trgt.diff(dim=-1)
        acc=(preds_diff.sign()==trgt_diff.sign()).float().mean()
        print(f"sign accuracy : {acc}")
        print(F.mse_loss(preds,trgt))
        for i in range(20):
            plt.plot(trgt[i,0],label="true")
            # plt.scatter(argmaxes[i],trgt[i,0][argmaxes[i]],color='red')
            # plt.scatter(argmins[i],trgt[i,0][argmins[i]],color='green')
            plt.plot(preds[i,0],label="pred")


            plt.legend()
            plt.show()
        
        # data=load_test(self.stock,self.inputFrequency,self.inputPeriod)[0].permute(0,2,1)
        # trgt=load_test(self.stock,self.outputFrequency,self.outputPeriod)[0][1:].permute(0,2,1)
        l=torch.nn.L1Loss()
        

        # trgt=gaussian_smooth_1d(trgt.squeeze(1)).unsqueeze(1)
        # data=gaussian_smooth_1d(data.squeeze(1)).unsqueeze(1)
        # data=(data-data.mean(dim=-1,keepdim=True))/(data.std(dim=-1,keepdim=True)+1e-4)
        # trgt=(trgt-trgt.mean(dim=-1,keepdim=True))/(trgt.std(dim=-1,keepdim=True)+1e-4)
        # with torch.no_grad():
            
        #     preds=torch.stack([self.model(data[i-10:i]) for i in range(10,data.size(0)-1)]).squeeze(1)

        # # for i in range(3):
        # #     axis, fig = plt.subplots(2, 1)
        # #     fig[0].plot(preds[i,0],label="pred")
        # #     fig[1].plot(trgt[i,0],label="true")

        # #     plt.legend()
        # #     plt.show()

        perf=torch.stack([l(i.detach(),t) for i,t in zip(preds.squeeze(1),trgt.squeeze(1))]).mean()
        print(f"model's perf : {perf}")
        # perf=directional_accuracy(preds.squeeze(1),trgt.squeeze(1)).mean()

        print(f"model's perf : {perf}\nIDGBM's perf : {idgmPerf.mean()}\nGBM perf : {gbmPerf.mean()}")