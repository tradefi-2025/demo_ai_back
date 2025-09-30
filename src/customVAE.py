
import torch
import torch.nn as nn
import torch.nn.init as init
import torch.nn.functional as F

import math

def Attention(Q,K,V,sqrt):
    return( F.softmax(Q.T@K/sqrt,dim=-1) @V.T).T

class AttHead(nn.Module):
    def __init__(self,d1,d2):
        super(AttHead,self).__init__()
        self.params=nn.Parameter(torch.randn(d1,d2),requires_grad=True)
    def forward(self,X):
        return X@self.params
    
class SelfAttention(nn.Module):
    def __init__(self, d_model, nhead):
        super(SelfAttention, self).__init__()
        self.d_model = d_model
        self.nhead = nhead
        self.d_k = d_model // nhead  # Dimension per head
        self.sqrt=math.sqrt(self.d_k)
        
        
        self.sequence=nn.ModuleList([nn.ModuleList([nn.Linear(self.d_model, self.d_k) ,nn.Linear(self.d_model, self.d_k),nn.Linear(self.d_model, self.d_k) ]) for i in range(nhead)])
        
        
        
        # Output linear transformation
        self.fc_out = nn.Linear(d_model, d_model)
        
    def forward(self, Q,K,V):
        out=self.fc_out(torch.cat([Attention(l[0](Q),l[1](K),l[2](V),self.sqrt) for l in self.sequence] , dim=1))
        
        return out


def layer_norm(data):
    mean=data.mean(dim=1).unsqueeze(1)
    var=data.std(dim=1).unsqueeze(1)
    return (data-mean)/var

class TransformerBlock(nn.Module):
    def __init__(self,d_model,dff, nhead):
        super(TransformerBlock, self).__init__()
        self.MHAtention=SelfAttention(d_model, nhead)
        self.ff = nn.Sequential(
            nn.Linear(d_model, dff),
            nn.ReLU(),
            nn.Linear(dff, d_model)
        )
        
        self.norm1=layer_norm
        self.norm2=layer_norm
        # self.dropout=nn.Dropout(0.1)
        
    def forward(self,Q,K,V):
        attention_out=self.MHAtention(Q,K,V)
        norm1=self.norm1(V+attention_out)
        ff_out=self.ff(norm1)
        norm2=self.norm2(norm1+ff_out)
        return norm2
    
    

    
# Encoder class for the transformer, embedding input and applying multiple transformer blocks
class Encoder(nn.Module):
    def __init__(self,d_input,d_model=512,dff=2048,nhead=8,N=6):
        super(Encoder,self).__init__()
        self.embedder=nn.Parameter(torch.randn(d_input,d_model),requires_grad=True)
        self.layers=nn.ModuleList([TransformerBlock(d_model, dff, nhead) for _ in range(N)])
        self.device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    def forward(self,x):
        embeddings=x@ self.embedder
        res=self.layers[0](embeddings,embeddings,embeddings)
        for l in self.layers[1:]:
            res=l(res,res,res)
        return res
    
    def _initialize_weights(self):
        # Initialize the embedding layer weights using Xavier initialization
        init.xavier_uniform_(self.embedder.weight)
        if self.embedder.bias is not None:
            init.zeros_(self.embedder.bias)
            


class Decoder(nn.Module):
    def __init__(self,d_input,d_model=512,dff=2048,nhead=8,N=6):
        super(Decoder,self).__init__()
        self.embedder=nn.Linear(d_input,d_model)
        self.out_emb=nn.ModuleList([SelfAttention(d_model, nhead) for _ in range(N)])
        self.decomp=nn.ModuleList([TransformerBlock(d_model, dff, nhead) for _ in range(N)])
        self.device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.norm=layer_norm
        # self.dropout=nn.Dropout(0.1)
    def forward(self,Lat,Prev):
        embeddings= self.embedder(Prev)
        out=self.norm(embeddings+self.out_emb[0](embeddings,embeddings,embeddings))
        out=self.decomp[0](Lat,Lat,out)
        for d,o in zip(self.decomp[1:],self.out_emb[1:]):
            out=self.norm(out+o(out,out,out))
            out=d(Lat,Lat,out)
        return out
    
    def _initialize_weights(self):
        # Initialize the embedding layer weights using Xavier initialization
        init.xavier_uniform_(self.embedder.weight)
        if self.embedder.bias is not None:
            init.zeros_(self.embedder.bias)
            


class VAE(nn.Module):
    def __init__(self,d_input,d_latent=8,d_model=512,dff=2048,nhead=8,N=6):
        super(VAE,self).__init__()
        self.Encoder=Encoder(d_input+1,d_model,dff,nhead,N)
        self.mu=nn.Linear(d_model, d_latent)
        self.sigma=nn.Linear(d_model, d_latent)
        self.decomp=nn.Linear(d_latent, d_model)
        self.Decoder=Decoder(d_input+1,d_model,dff,nhead,N)
        self.d_input=d_input
        # self.lstm=Bi_LSTM_Regressor(d_model,1,4,60)
        self.fc_out=nn.Linear(d_model,d_input)
        # self.fc_out=nn.Linear(d_model,1)
        self.MU=list()
        self.SIG=list()
        self.Loss=nn.MSELoss()
        
        # self.Encoder=Bi_enc(2,128,16,60)
        # self.Decoder=Bi_dec(16,128,1,60)
        
        # self.d_input=d_input
        
        self.MU=list()
        self.SIG=list()
        self.Loss=nn.MSELoss()
        self.activation=nn.Tanh()

    def f(self,dec,Prev):
        out=self.Decoder(self.decomp(dec),Prev)
        return self.fc_out(self.activation(out.mean(dim=0)))
    
    def forward(self,X,seq_len,Add_time_dim):
        L=self.activation(self.Encoder(X).mean(dim=0)).unsqueeze(0)
        mu=self.mu(L)
        self.MU.append(mu)
        sigma=self.sigma(L)
        self.SIG.append(sigma)
        dec=(torch.randn(1,requires_grad=False)*sigma)+mu
        # dec=(torch.randn(1,requires_grad=False)*sigma)+mu
        # out=self.Decoder(self.decomp(dec))
        
        # L=self.Encoder(X)
        
        # out=self.Decoder(L)
        
        # self.MU.append(L.mean(dim=0))
        p=self.f(dec,torch.zeros(1,X.size(1)))
        for i in range(seq_len):
            p=torch.cat([p,self.f(dec,Add_time_dim(p.unsqueeze(1).unsqueeze(0)).squeeze(0).detach())])
        # return self.lstm(out).squeeze(1)
        return p[1:]
        # return out

    def loss(self,X,Add_time_dim):
        
        
        # X_in=scaledX[:,:scaledX.size(1)//2]
        # X_out=scaledX[:,scaledX.size(1)//2:]
        seq_len=X.size(1)
        self.MU=list()
        self.SIG=list()
        Xhat=torch.stack([self(x,seq_len,Add_time_dim) for x in X])
        rec=torch.stack([self.Loss(xh,sx) for xh,sx in zip(Xhat,X[:,:,0])]).sum()
        # self.MU=list()
        # self.SIG=list()
        # Xhat=torch.stack([self(x,seq_len) for x in scaledX_t])
        # # mu=torch.stack(self.MU)
        # # sigma=torch.stack(self.SIG)
        # KL=0
        # # KL= -0.1*torch.sum((1 + sigma - mu.pow(2) - sigma.exp()),dim=1).sum()
        # # rec=(Xhat-scaledX).norm(dim=1).max()
        # rec=0
        # # smthLoss=((Xhat[:,1:]-Xhat.detach()[:,:-1])-(scaledX.diff(dim=1))).max()
        # # tmS=torch.stack([self.Loss(xh,sx) for xh,sx in zip(Xhat.diff(dim=1),scaledX.diff(dim=1))]).max()
        # # smthLoss=Xhat.diff(dim=1).max()
        # # meanHat=Xhat.mean(dim=1).unsqueeze(1)
        # # mean=scaledX.mean(dim=1).unsqueeze(1)
        # # diffHat=Xhat-meanHat
        # # diff=scaledX-mean
        # rec=torch.stack([self.Loss(xh,sx) for xh,sx in zip(Xhat,scaledX)]).sum()
        # # rec2=torch.stack([self.Loss(dh,df) for dh,df in zip(diffHat,diff)]).max()
        # # smthLoss=smthLoss.norm(dim=1).max()
        # self.MU=list()
        # self.SIG=list()
        # # rec=0.1*loss_time_series(scaledX, Xhat)
        # # return rec+KL+0.9*smthLoss+cont+rec2*0.9+0.9*tmS
    
        return rec