import torch
import torch.nn as nn
import math
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import os
import torch
from torch.utils.data import Dataset
import matplotlib.pyplot as plt
import random
from tools import *
from generator import *



def labelise_algo1(prices: torch.Tensor,
                            tick_size=0.01,
                            target_ticks=20,
                            neutral_ticks=7,
                            lookahead_steps=15):
    """
    Label only BUY and NEUTRAL cases.

    prices: (B, T) tensor of prices
    Returns: (B, T) int8 tensor of labels
             0 = NONE
             1 = BUY
             2 = NEUTRAL
    """
    B, T = prices.shape
    labels = torch.zeros((B, T), dtype=torch.int8)

    target_move = target_ticks * tick_size
    neutral_move = neutral_ticks * tick_size


    for b in range(B):
        i=0
        while i<T:
            k=0
            entry_price=prices[b,i]
            no_sell=no_buy=False
            while True and (i+k <T):
                diff=prices[b,i+k]-entry_price
                if(diff>=target_move and not no_buy):
                    labels[b,i]=1
                    i+=k
                    break
                elif(diff<=-target_move and not no_sell):
                    labels[b,i]=2
                    i+=k
                    break
                elif(diff<=-neutral_move):
                    no_buy=True
                    if(no_sell):
                        i+=k
                        break
                elif(diff>=neutral_move):
                    no_sell=True
                    if(no_buy):
                        i+=k
                        break
                k+=1
            i+=1
            



    return labels



def generate_rolling_windows(data: torch.Tensor, window_size: int = 64):
    """
    Args:
        data: Tensor of shape (B, T, F)
        window_size: Number of past minutes to include (default: 64)
        
    Returns:
        Tensor of shape (B, T - window_size + 1, window_size, F)
    """
    B, F,T = data.shape
    if T < window_size:
        raise ValueError("Time dimension must be at least as long as the window size")
    
    # Use unfold to generate rolling windows
    # (B, T - window_size + 1, window_size, F)
    return data.unfold(dimension=-1, size=window_size, step=1).permute(0,2,1,3)

class RCNN(nn.Module):
    def __init__(self,kernel_size,in_channel,base_channel,d_latent,d_output):
        super(RCNN,self).__init__()
        self.kernel_size=kernel_size
        self.in_channel=in_channel
        self.base_channel=base_channel
        self.d_output=d_output
        self.d_latent=d_latent
        self.P=torch.zeros(256)
        self.sigmoid=nn.Sigmoid()
        self.sequencial=nn.Sequential(
            nn.Conv1d(in_channel, 64, kernel_size=7, stride=2, padding=3),  # L → L/2
            nn.LeakyReLU(),
            nn.Conv1d(64, 128, kernel_size=5, stride=2, padding=2),             # L/2 → L/4
            nn.LeakyReLU(),
            nn.Conv1d(128, 256, kernel_size=3, stride=2, padding=1)          # L/4 → L/8
            # nn.LeakyReLU(),
            # nn.AdaptiveAvgPool1d(1),  # global avg pool over sequence
            # nn.Flatten(),             # shape: (B, 256)
            # nn.Linear(256, 2*d_output)  # output latent vector
        )
        self.keep_current=nn.Sequential(
            nn.LeakyReLU(),
            nn.AdaptiveAvgPool1d(1),  # global avg pool over sequence
            nn.Flatten(),             # shape: (B, 256)
            nn.Linear(256, d_latent)  # output latent vector
        )
        self.remember=nn.Sequential(
            nn.LeakyReLU(),
            nn.Linear(d_latent,256)
        )
        self.keep_p=nn.Sequential(
            nn.Linear(256,d_latent)
        )
        

        self.gen=nn.ModuleList([
            IndicatorBlock(8, 256, 256, 256, is_first=True,kernel_size=3),
            IndicatorBlock(16, 256, 256, 256, is_first=False,kernel_size=3)
            ])
        self.output_segmentation = nn.Conv1d(256, 3, kernel_size=1)

    def reset(self):
        self.P=torch.zeros(256)
    def forward(self,X):
        x = F.interpolate(X, size=64, mode='linear', align_corners=False)
        current_encoding=self.sequencial(x)
        
        kc=self.keep_current(current_encoding)
        
        kp=self.keep_p(self.P)
        hist=self.remember(kp+kc)
        

        out=self.gen[0](hist,current_encoding)
        out=self.gen[1](hist,current_encoding)
        
        out=self.output_segmentation(out)
        self.P=hist.detach()
        return out
    



def generate(data,rcnn):

    patched_data=generate_rolling_windows(data)
    nb=(patched_data.size(1)//16)*16
    patched_data=patched_data[:,:nb]
    rcnn.reset()
    res=[]
    for i in range(0,patched_data.size(1),16):
        res.append(rcnn(patched_data[:,i]))

    return torch.cat(res,dim=-1).squeeze(1)
    
def train_estimator(indicators,sequence,target,filename=None):
    lbl=labelise_algo1(target.squeeze(1))
    print("labelized")
    
    dataset = ForecastingDataset(indicators, sequence,lbl)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True, num_workers=4)
    model= RCNN(8,indicators.size(1),64,512,0)
    if filename is not None:
        model.load_state_dict(torch.load(filename+'.nn'))
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-5, betas=(0.5, 0.999))
    criterion = nn.CrossEntropyLoss()
    mseLoss=nn.MSELoss()
    for epoch in range(20):
        total_loss = 0
        for ind, pose_batch, target_batch in dataloader:
            optimizer.zero_grad()
            gen=generate(ind,model)
            
            # tgt=target_batch[:,:,77:]
            
            tgt=target_batch[:,64:-13]

            # diff1=gen.diff(dim=2)
            
            # diff2=tgt.diff(dim=2)
            # loss=mseLoss(gen,tgt) + mseLoss(diff1,diff2)*0.1 + diff1.norm(dim=2).mean()*0.1 
            loss=criterion(gen,tgt.long())
            total_loss += loss.item()
            print(loss)
            loss.backward()
            optimizer.step()

        print(f"Epoch {epoch} - Loss: {total_loss:.4f}")

    return model

if __name__=='__main__':
    pass