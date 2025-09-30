import torch
import torch.nn.functional as F
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
import matplotlib.pyplot as plt
import numpy as np
from data_loader import *
from torch.utils.data import TensorDataset, DataLoader, Dataset
import torch.optim as optim

import torch.nn as nn
from generator import ProbabilisticLayer
from tools import *
import os

class ForecastingDataset(Dataset):
    def __init__(self, src,trgt,labels):
    
        self.src = src
        self.trgt= trgt
        self.labels=labels
    def __len__(self):
        return len(self.src)

    def __getitem__(self, idx):

            return self.src[idx],  self.trgt[idx], self.labels[idx]
    

class ForecastingDatasetLSTM(Dataset):
    def __init__(self, src,trgt,labels,seq_len=10):
    
        self.src = src
        self.trgt= trgt
        self.labels=labels
        self.seq_len=seq_len
    def __len__(self):

        return len(self.src)-self.seq_len

    def __getitem__(self, idx):
        return self.src[idx:idx+self.seq_len],  self.trgt[idx+self.seq_len], self.labels[idx+self.seq_len]

# ------------------------------
# Encoder: 1D CNN -> (mu, logvar)
# ------------------------------
class Encoder(nn.Module):
    """
    Encodes a time series (B, C, L) into a latent space (mu, logvar) of size latent_dim.
    """
    def __init__(self, in_channels: int = 1, latent_dim: int = 512):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv1d(in_channels, 32, kernel_size=7, padding=3),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm1d(32),

            nn.Conv1d(32, 64, kernel_size=5, stride=2, padding=2),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm1d(64),

            nn.Conv1d(64, 128, kernel_size=5, stride=2, padding=2),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm1d(128),

            nn.Conv1d(128, 256, kernel_size=3, stride=2, padding=1),
            nn.LeakyReLU(inplace=True),
            nn.BatchNorm1d(256),
        )
        # Collapse time dimension to length 1, then Linear -> latent
        self.pool = nn.AdaptiveAvgPool1d(1)
        self.fc_mu = nn.Linear(256, latent_dim)
        self.fc_logvar = nn.Linear(256, latent_dim)

    def forward(self, x: torch.Tensor):
        # x: (B, C, L)
        h = self.features(x)               # (B, 256, L')
        h = self.pool(h).squeeze(-1)       # (B, 256)
        mu = self.fc_mu(h)                 # (B, latent_dim)
        logvar = self.fc_logvar(h)         # (B, latent_dim)
        return mu, logvar


# ------------------------------
# Decoder: latent -> 1D series
# ------------------------------
class Decoder(nn.Module):
    """
    Decodes a latent vector (B, latent_dim) back to a time series (B, out_channels, seq_len).
    Uses a Linear to hit the exact target length, then a few Conv1d refinements.
    """
    def __init__(self, out_channels: int = 1, latent_dim: int = 512, seq_len: int = 256):
        super().__init__()
        self.seq_len = seq_len
        self.latent_dim = latent_dim
        self.hidden_channels = 128

        # Map latent directly to (hidden_channels, seq_len)
        self.fc = nn.Linear(latent_dim, self.hidden_channels * seq_len)

        # A small conv stack to refine the sequence
        self.refine = nn.Sequential(
            nn.Conv1d(self.hidden_channels, 64, kernel_size=5, padding=2),
            nn.LeakyReLU(inplace=True),
            nn.Conv1d(64, 64, kernel_size=5, padding=2),
            nn.LeakyReLU(inplace=True),
            nn.Conv1d(64, out_channels, kernel_size=3, padding=1)
        )

    def forward(self, z: torch.Tensor):
        # z: (B, latent_dim)
        B = z.size(0)
        x0 = self.fc(z)                                   # (B, hidden*L)
        x0 = x0.view(B, self.hidden_channels, self.seq_len)  # (B, hidden, L)
        x_hat = self.refine(x0)                           # (B, C_out, L)
        return x_hat


# ------------------------------
# VAE wrapper
# ------------------------------
class VAE(nn.Module):
    """
    VAE for 1D time series with CNN encoder and conv decoder.
    forward(x) -> x_hat, mu, logvar
    """
    def __init__(self, in_channels: int = 1, out_channels: int = 1,
                 seq_len: int = 256, latent_dim: int = 512):
        super().__init__()
        self.encoder = Encoder(in_channels=in_channels, latent_dim=latent_dim)
        self.decoder = Decoder(out_channels=out_channels,
                               latent_dim=latent_dim, seq_len=seq_len)

    @staticmethod
    def reparameterize(mu: torch.Tensor, logvar: torch.Tensor):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std

    def forward(self, x: torch.Tensor):
        # x: (B, C, L)
        mu, logvar = self.encoder(x)
        z = self.reparameterize(mu, logvar)
        x_hat = self.decoder(z)
        return x_hat, mu, logvar

class VAEbasedPatternDetector:
    def __init__(self, ref: torch.Tensor, file_name: str
                 ):
        """
        ref: reference pattern tensor of shape (seq_len,)
        file_name: path to saved VAE state_dict
        """
        
        
        seq_len = ref.size(0)
        
        # Load VAE and keep only encoder
        # vae = VAE(in_channels=1, out_channels=1, seq_len=seq_len)
        
        # vae.load_state_dict(torch.load(file_name))
        # self.encoder = vae.encoder
        self.encoder=Encoder()
        self.encoder.load_state_dict(torch.load(file_name))
        self.encoder.eval()
        
        # Encode reference pattern
        with torch.no_grad():
            ref_input = ref.unsqueeze(0).unsqueeze(0) # (1, 1, L)
            mu, logvar = self.encoder(ref_input)
            self.ref_latent = mu  # you ca


    def Encode(self,data):
        if(data.ndim==2):
            data=data.unsqueeze(1)

        mu, _=self.encoder(data)
        return mu
    
    def compute_dist(self,latents):
        return torch.stack([F.mse_loss(l,self.ref_latent) for l in latents])
    


class EncoderDecoderPredictor(nn.Module):
    def __init__(self,L,L_out,d_latent=512,in_channel=1,out_channel=1):
        super(EncoderDecoderPredictor,self).__init__()
        self.L=L
        self.d_latent=d_latent
        self.in_channel=in_channel
        self.out_channel=out_channel
        self.L_out=L_out
        self.mapper_mu=nn.Sequential(
            nn.Linear(d_latent,d_latent*2),
            nn.LeakyReLU(),
            nn.Linear(d_latent*2,d_latent*4),
            nn.LeakyReLU(),
            nn.Linear(d_latent*4,d_latent*2),
            nn.LeakyReLU(),
            nn.Linear(d_latent*2,d_latent)
        )

        self.mapper_logvar=nn.Sequential(
            nn.Linear(d_latent,d_latent*2),
            nn.LeakyReLU(),
            nn.Linear(d_latent*2,d_latent*4),
            nn.LeakyReLU(),
            nn.Linear(d_latent*4,d_latent*2),
            nn.LeakyReLU(),
            nn.Linear(d_latent*2,d_latent)
        )
        self.VAE_input=VAE(self.in_channel,1,L,self.d_latent)
        self.VAE_output=VAE(1,self.out_channel,L_out,self.d_latent)


    def forward(self,x,softmax=False):
        # x: (B, C, L)

        # x_hat_in, mu_in, logvar_in=self.VAE_input(x)
        # print(x.shape)

        # fig, axs = plt.subplots(1, 2, figsize=(12, 5))  # 1 row, 2 columns
        # axs[0].plot(x[0,0], label='trgt')
        # axs[1].plot(x_hat_in[0,0], label='preds')
        # plt.show()
        # raise
        
        mu, logvar = self.VAE_input.encoder(x)
        muT=self.mapper_mu(mu)
        logvarT=self.mapper_logvar(logvar)

        z = self.VAE_output.reparameterize(muT, logvarT)
        x_hat = self.VAE_output.decoder(z)
        if not softmax:
            return x_hat
        out=torch.softmax(x_hat,dim=1)
        return out.argmax(dim=1)
    
    def loss_vae(self,src,trgt,labels=None,crt="mse"):
        x_hat_in, mu_in, logvar_in=self.VAE_input(src)

        x_hat_out, mu_out, logvar_out=self.VAE_output(trgt)

        muT=self.mapper_mu(mu_in)
        logvarT=self.mapper_logvar(logvar_in)
        rep=self.VAE_output.reparameterize(muT,logvarT)
        pred=self.VAE_output.decoder(rep)


        loss1=vae_loss(src[:,-1,:].unsqueeze(1),x_hat_in,mu_in,logvar_in)[0]
        loss2=vae_loss(trgt if labels is None else labels,x_hat_out,mu_out,logvar_out,recon=crt)[0]
        loss3=vae_loss(trgt if labels is None else labels,pred,muT,logvarT,recon=crt)[0]

        return loss1+loss2+loss3

        
    def loss_pred(self,src,trgt):
        

        mu,logvar=self.VAE_input.encoder(src)
        muT=self.mapper_mu(mu)
        logvarT=self.mapper_logvar(logvar)
        mu_trgt,logvar_trgt=self.VAE_output.encoder(trgt)
        return F.mse_loss(mu_trgt,muT)+F.mse_loss(logvar_trgt,logvarT)
        # rep=self.VAE_output.reparameterize(muT,logvarT)
        # x_hat=self.VAE_output.decoder(rep)
        # loss=vae_loss(trgt,x_hat,muT,logvarT)
        # return loss[0]


class EncoderDecoderPredictorLSTM(nn.Module):
    def __init__(self, L, L_out, d_latent=512, in_channel=1, out_channel=1, hidden_size=512, num_layers=1):
        super(EncoderDecoderPredictorLSTM, self).__init__()
        self.L = L
        self.d_latent = d_latent
        self.in_channel = in_channel
        self.out_channel = out_channel
        self.L_out = L_out
        self.noise_mu=nn.Linear(d_latent,d_latent)
        self.noise_logvar=nn.Linear(d_latent,d_latent)
        # Mapper LSTM for mu and logvar
        self.mapper_mu = nn.LSTM(
            input_size=d_latent,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True
        )
        self.fc_mu = nn.Linear(hidden_size, d_latent)

        self.mapper_logvar = nn.LSTM(
            input_size=d_latent,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True
        )
        self.fc_logvar = nn.Linear(hidden_size, d_latent)

        # VAEs
        self.VAE_input = VAE(self.in_channel, 1, L, self.d_latent)
        self.VAE_output = VAE(1, self.out_channel, L_out, self.d_latent)

    def forward(self, x, softmax=False):
        # Encode input sequence
        
           # shape: (B, d_latent)

        # Add sequence dimension for LSTM -> (B, 1, d_latent)
       

        # Project back to latent space size
        if(x.ndim==4):
            ins=[self.VAE_input.encoder(s) for s in x]
            noise_mu=self.noise_mu(torch.randn(len(ins),self.d_latent))
            noise_logvar=self.noise_logvar(torch.randn(len(ins),self.d_latent))
            mu=torch.stack([s[0] for s in ins])
            logvar=torch.stack([s[1] for s in ins])
            mu_out,_ = self.mapper_mu(mu)
            
            logvar_out,_ = self.mapper_logvar(logvar)
            
            muT = self.fc_mu(mu_out[:, -1, :])+noise_mu       # (B, d_latent)
            logvarT = self.fc_logvar(logvar_out[:, -1, :])+noise_logvar
        else:
            mu, logvar = self.VAE_input.encoder(x)
            mu_out, _ = self.mapper_mu(mu)        # (B, 1, hidden_size)
            logvar_out, _ = self.mapper_logvar(logvar)
            muT = self.fc_mu(mu_out[-1, :])        # (B, d_latent)
            logvarT = self.fc_logvar(logvar_out[-1, :])

        # Reparametrize + decode
        z = self.VAE_output.reparameterize(muT, logvarT)

        x_hat = self.VAE_output.decoder(z.unsqueeze(1))

        if not softmax:
            return x_hat
        out = torch.softmax(x_hat, dim=1)
        return out.argmax(dim=1)

    def loss_vae(self, src, trgt, labels=None, crt="mse",regularize=True):
        noise_mu=self.noise_mu(torch.randn(src.size(0),self.d_latent))
        noise_logvar=self.noise_logvar(torch.randn(src.size(0),self.d_latent))
        ins=[self.VAE_input(s) for s in src]

        x_hat_in = torch.stack([x[0] for x in ins])
        mu_in = torch.stack([x[1] for x in ins])
        logvar_in = torch.stack([x[2] for x in ins])

        
        x_hat_out, mu_out, logvar_out = self.VAE_output(trgt)

        # LSTM mapper
        mu_mapped, _ = self.mapper_mu(mu_in)
        logvar_mapped, _ = self.mapper_logvar(logvar_in)
        
        muT = self.fc_mu(mu_mapped[:, -1, :])+noise_mu
        logvarT = self.fc_logvar(logvar_mapped[:, -1, :])+noise_logvar
        
        rep = self.VAE_output.reparameterize(muT, logvarT)
        pred = self.VAE_output.decoder(rep)
        # print(pred.shape,trgt.shape,src.shape,x_hat_in.shape,mu_in.shape,logvar_in.shape,mu_out.shape,logvar_out.shape,muT.shape,logvarT.shape,rep.shape)
        if not regularize:
            return vae_loss(trgt if labels is None else labels, pred, muT, logvarT, recon=crt)[0]
        
        loss1 = vae_loss(src[:,:, -1, :].unsqueeze(2), x_hat_in, mu_in, logvar_in)[0]
        loss2 = vae_loss(trgt if labels is None else labels, x_hat_out, mu_out, logvar_out, recon=crt)[0]
        loss3 = vae_loss(trgt if labels is None else labels, pred, muT, logvarT, recon=crt)[0]
        # loss3 = F.mse_loss(((pred[:,:,-1]-pred[:,:,0])/(pred[:,:,0]+1e-4)),((trgt[:,:,-1]-trgt[:,:,0])/(trgt[:,:,0]+1e-4)))
        
        return loss1 + loss2 + loss3

    def loss_pred(self, src, trgt):
        mu, logvar = self.VAE_input.encoder(src)

        # Map with LSTM
        mu_seq, logvar_seq = mu.unsqueeze(1), logvar.unsqueeze(1)
        mu_mapped, _ = self.mapper_mu(mu_seq)
        logvar_mapped, _ = self.mapper_logvar(logvar_seq)

        muT = self.fc_mu(mu_mapped[:, -1, :])
        logvarT = self.fc_logvar(logvar_mapped[:, -1, :])

        mu_trgt, logvar_trgt = self.VAE_output.encoder(trgt)
        return F.mse_loss(mu_trgt, muT) + F.mse_loss(logvar_trgt, logvarT)





class IDP (nn.Module):
    def __init__(self,L,L_out,nb_index=1,d_latent=512,in_channel=1,out_channel=1):
        super(IDP,self).__init__()
        self.L=L
        self.d_latent=d_latent
        self.in_channel=in_channel
        self.out_channel=out_channel
        self.L_out=L_out
        self.nb_index=nb_index
        self.VAE_indices=nn.ModuleList([VAE(self.in_channel,1,L,self.d_latent) for i in range(self.nb_index)])
        self.VAE_src=VAE(self.in_channel,1,L,d_latent)
        
        self.lambdas=nn.Parameter(torch.randn(d_latent,nb_index+1),requires_grad=True)
        self.fc_out=ProbabilisticLayer(d_latent,out_channel)
    def forward(self,src,indices):
        mu,sigma=self.VAE_src.encoder(src)
        
        l=self.VAE_src.reparameterize(mu,sigma)
        latents=[l.unsqueeze(1)]
        for vae,i in zip(self.VAE_indices,indices):
            mu,logvar=vae.encoder(i)
            l=vae.reparameterize(mu,logvar)
            latents.append(l.unsqueeze(1))
        latents=torch.cat(latents,dim=1)
        
        combine=self.lambdas@latents
        
        combine=combine.sum(dim=1)/self.lambdas.norm()

        return self.fc_out(combine)
    
    def loss(self,src,indices,trgt):
        
        src_hat, mu_src, logvar_src = self.VAE_src(src)
        loss_src = vae_loss(src[:, -1, :].unsqueeze(1), src_hat, mu_src, logvar_src)[0]
        loss_indices=0
        for vae,i in zip(self.VAE_indices,indices):
            i_hat, mu_i, logvar_i = vae(i)
            loss_indices+=vae_loss(i[:, -1, :].unsqueeze(1), i_hat, mu_i, logvar_i)[0]
        preds=self.forward(src,indices)
        loss_pred=F.mse_loss(preds,trgt)
        return loss_src+loss_indices+loss_pred
    
    def weights(self):

        return torch.softmax(self.lambdas.norm(dim=0),dim=0).detach().cpu().numpy()

def train_IDP(src,indices,trgt,filename=None):
    

    # src=torch.stack([gaussian_smooth_1d(s[:,-1,:]) for s in src]).unsqueeze(2)
    
    # src=gaussian_smooth_1d(src[:,-1,:]).unsqueeze(1)

    # trgt=gaussian_smooth_1d(trgt.squeeze(1)).unsqueeze(1)

    # src=(src-src.mean(dim=-1,keepdim=True))/(src.std(dim=-1,keepdim=True)+1e-4)
    # trgt=(trgt-trgt.mean(dim=-1,keepdim=True))/(trgt.std(dim=-1,keepdim=True)+1e-4)
    # indices=[(ind-ind.mean(dim=-1,keepdim=True))/(ind.std(dim=-1,keepdim=True)+1e-4) for ind in indices]

    # trgt=torch.log(trgt[:,-1,1:] / (trgt[:,-1,:-1]+1e-4)).unsqueeze(1)
    # labels=labelise(trgt.squeeze(1)).unsqueeze(1)
    
    model = IDP(src.size(-1),trgt.size(-1),nb_index=len(indices),in_channel=src.size(-2),out_channel=1)
    
    dataset = ForecastingDataset(src,trgt,indices)

    dataloader = DataLoader(dataset, batch_size=8, shuffle=True, num_workers=4)
    # if filename is not None:
    #     model.load_state_dict(torch.load(filename+'.nn'))

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4, betas=(0.5, 0.999))
    try:
        print("Pretraining the VAEs")
        for epoch in range(20):
            total_loss = 0
            for  src_batch, trgt_batch,indices_batch in dataloader:
                

                optimizer.zero_grad()


                loss = model.loss(src_batch,indices_batch.permute(1,0,2,3),trgt_batch)  # (B, 8, H, W)
                
                total_loss += loss.item()
                print(loss)
                loss.backward()
                optimizer.step()

            print(f"Epoch {epoch} - Loss: {total_loss:.4f}")

            
    except :
        pass
        

    return model


def train_EncoderDecoderPredictor(src,trgt,filename=None,LSTM=False):
    

    # src=torch.stack([gaussian_smooth_1d(s[:,-1,:]) for s in src]).unsqueeze(2)
    
    # src=gaussian_smooth_1d(src[:,-1,:]).unsqueeze(1)

    # trgt=gaussian_smooth_1d(trgt.squeeze(1)).unsqueeze(1)

    src=(src-src.mean(dim=-1,keepdim=True))/(src.std(dim=-1,keepdim=True)+1e-4)
    trgt=(trgt-trgt.mean(dim=-1,keepdim=True))/(trgt.std(dim=-1,keepdim=True)+1e-4)
    # trgt=torch.log(trgt[:,-1,1:] / (trgt[:,-1,:-1]+1e-4)).unsqueeze(1)
    labels=labelise(trgt.squeeze(1)).unsqueeze(1)
    if LSTM:
        # dataset = ForecastingDatasetLSTM(src,trgt, labels,seq_len=10)
        model = EncoderDecoderPredictorLSTM(src.size(-1),trgt.size(-1),in_channel=src.size(-2),out_channel=1)
    else:
        model = EncoderDecoderPredictor(src.size(-1),trgt.size(-1),in_channel=src.size(-2),out_channel=1)
    dataset = ForecastingDataset(src,trgt,trgt)

    dataloader = DataLoader(dataset, batch_size=8, shuffle=True, num_workers=4)
    # if filename is not None:
    #     model.load_state_dict(torch.load(filename+'.nn'))

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4, betas=(0.5, 0.999))
    try:
        print("Pretraining the VAEs")

        for epoch in range(1):
            total_loss = 0
            for  src_batch, trgt_batch, labels in dataloader:
                
                optimizer.zero_grad()


                loss = model.loss_vae(src_batch,trgt_batch,crt="mse",regularize=True)  # (B, 8, H, W)
                
                total_loss += loss.item()
                print(loss)
                loss.backward()
                optimizer.step()

            print(f"Epoch {epoch} - Loss: {total_loss:.4f}")

        # print("Training the predictor")
        # for p1,p2 in zip(model.VAE_input.parameters(),model.VAE_output.parameters()):
        #     p1.requires_grad=False
        #     p2.requires_grad=False

        # for epoch in range(200):
            
        #     total_loss = 0
        #     for  src_batch, trgt_batch in dataloader:

        #         optimizer.zero_grad()


        #         loss = model.loss_pred(src_batch,trgt_batch)  # (B, 8, H, W)
                
        #         total_loss += loss.item()
        #         print(loss)
        #         loss.backward()
        #         optimizer.step()

        #     print(f"Epoch {epoch} - Loss: {total_loss:.4f}")
    except Exception as e:
        print(e)
        

    return model


def find_pattern_VAEbased(prices,pattern_detector,eps=0.1):
    latents=pattern_detector.Encode(prices)
    distances=pattern_detector.compute_dist(latents)
    print(distances)
    matches = []
    for i, d in enumerate(distances):
        if d <= eps:
            start_idx = i * prices.size(1)  # assuming prices are already split into segments
            end_idx = start_idx + prices.size(1)
            matches.append((start_idx, end_idx))

    return matches
# ------------------------------
# Loss helper
# ------------------------------
def vae_loss(x: torch.Tensor,
             x_hat: torch.Tensor,
             mu: torch.Tensor,
             logvar: torch.Tensor,
             beta: float = 1.0,
             recon: str = "mse"):
    """
    ELBO-style loss = reconstruction + beta * KL
    recon: "mse" or "l1"
    """
    if recon == "mse":
        recon_loss = F.mse_loss(x_hat, x, reduction="mean")
    elif recon == "l1":
        recon_loss = F.l1_loss(x_hat, x, reduction="mean")
    elif recon == "CrossEntropy":
        recon_loss = nn.CrossEntropyLoss()(x_hat,x)
    else:
        raise ValueError("recon must be 'mse' or 'l1'")

    # KL divergence between N(mu, sigma) and N(0, I)
    kl = -0.5 * torch.mean(1 + logvar - mu.pow(2) - logvar.exp())

    return recon_loss + beta * kl, {"recon": recon_loss.item(), "kl": kl.item()}



def train_estimator(prices: torch.Tensor, filename: str = None,
                    epochs: int = 20, lr: float = 1e-3):
    """
    Trains a VAE on given price time series.

    prices: torch.Tensor of shape (num_samples, seq_len)
    filename: optional path to save trained model
    """
    # Ensure shape (B, C, L) for VAE: add channel dimension
    if prices.ndim == 2:
        prices = prices.unsqueeze(1)  # (B, 1, L)

    dataset = TensorDataset(prices)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True, num_workers=4)

    seq_len = prices.shape[2]
    vae = VAE(in_channels=1, out_channels=1, seq_len=seq_len,latent_dim=64)
    optimizer = optim.Adam(vae.parameters(), lr=lr)

    for epoch in range(epochs):
        vae.train()
        total_loss = 0

        for (batch,) in dataloader:
            batch = batch

            x_hat, mu, logvar = vae(batch)
            loss, loss_dict = vae_loss(batch, x_hat, mu, logvar, beta=1.0, recon="mse")

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            total_loss += loss.item() * batch.size(0)  # scale back to sum
            # print(total_loss)
        avg_loss = total_loss / len(dataset)
        print(f"Epoch [{epoch+1}/{epochs}] - Loss: {avg_loss:.6f} "
              f"(Recon: {loss_dict['recon']:.6f}, KL: {loss_dict['kl']:.6f})")

    if filename is not None:
        torch.save(vae.state_dict(), filename)
        print(f"Model saved to {filename}")

    return vae 



def select_reference_pattern(signal):
    """
    Displays an interactive plot of the time series and allows the user
    to click twice to select a start and end index for a reference pattern.

    Args:
        signal (array-like): 1D array or list representing the time series.

    Returns:
        (start_idx, end_idx): tuple of integers representing the selected indices.
    """
    signal = np.array(signal)
    selected_points = []
    fig, ax = plt.subplots()
    ax.plot(signal, label='Signal')
    ax.set_title("Click twice to select reference pattern")
    ax.legend()

    def onclick(event):
        if event.inaxes != ax:
            return
        if event.button == 1:  # Left mouse button
            selected_points.append(int(round(event.xdata)))
            if len(selected_points) == 2:
                start, end = sorted(selected_points)
                ax.axvspan(start, end, color='orange', alpha=0.3)
                fig.canvas.draw()
                print(f"Selected indices: {start} to {end}")
                plt.close(fig)  # Close the figure after selection

    fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()

    if len(selected_points) < 2:
        print("Selection cancelled or incomplete.")
        return None
    return tuple(sorted(selected_points))




def find_pattern(signal, ref, eps):
    """
    This function uses a sliding window to find parts of the `signal`
    that have a DTW distance lower than epsilon and returns the indices as a 
    list of tuples (start_index, end_index).

    Args:
        signal (Tensor): 1D torch tensor for the main signal.
        ref (Tensor): 1D torch tensor for the reference pattern.
        eps (float): Threshold for DTW distance.

    Returns:
        List[Tuple[int, int]]: List of (start, end) indices in the signal.
    """
    # Ensure tensors are 1D
    signal = signal.flatten()
    ref = ref.flatten()
    # ref= torch.log(ref[1:]/ref[:-1])
    ref=ref-ref.mean()
    ref=ref/ref.std()
    # Window length is the same as reference length
    win_len = len(ref)
    matches = []
    start=0
    while start < len(signal) - win_len + 1:
        segment = signal[start:start+win_len]
        # segment = torch.log(segment[1:]/segment[:-1])
        segment=segment-segment.mean()
        segment=segment/segment.std()


        # Convert to numpy for fastdtw
        seg_np = segment.detach().cpu().numpy()
        ref_np = ref.detach().cpu().numpy()

        # Compute DTW distance
        distance, _ = fastdtw(seg_np, ref_np, dist=euclidean)
        print(distance)
        # Check if it's under the threshold
        if distance <= eps:
            
            matches.append((start, start + win_len - 1))
            start+=win_len-1
        start+=1
    return matches



def find_similars(signal, eps):
    """
    Select a reference pattern interactively, then find and display
    all segments with similar patterns using DTW distance.
    """
    # Step 1: Select reference pattern
    selection = select_reference_pattern(signal)
    if selection is None:
        print("No selection made.")
        return
    start_idx, end_idx = selection
    # start_idx=50
    # end_idx=60
    ref = signal[start_idx:end_idx]
    window_size=end_idx-start_idx+1
    ref=(ref-ref.mean())/(ref.std()+1e-4)
    pattern_detector=VAEbasedPatternDetector(ref,"TEST_ENCODER_10")
    prices=signal.unfold(0,window_size,window_size)
    prices=(prices - prices.mean(dim=-1,keepdim=True))/(prices.std(dim=-1,keepdim=True)+1e-4)
    # Step 2: Find matching segments
    matches = find_pattern_VAEbased(prices,pattern_detector,eps)

    # Step 3: Display the signal with matches highlighted
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(signal, color='blue', label='Signal')

    # Highlight reference
    ax.axvspan(start_idx, end_idx, color='orange', alpha=0.4, label='Reference')

    # Highlight matches
    for s, e in matches:
        if not (s == start_idx and e == end_idx):  # skip the reference itself
            print(s,e)
            ax.axvspan(s, e, color='green', alpha=0.3)

    ax.set_title(f"Found {len(matches)} similar patterns (eps={eps})")
    ax.legend()
    plt.show()



def test_vae(prices: torch.Tensor, model_file: str, n_samples: int = 5):
    """
    Loads a trained VAE from `model_file`, reconstructs the first `n_samples` from `prices`,
    and plots original vs reconstructed signals.
    
    prices: torch.Tensor of shape (num_samples, seq_len)
    model_file: path to saved VAE state_dict
    """
    # Ensure shape (B, C, L)
    if prices.ndim == 2:
        prices = prices.unsqueeze(1)  # (B, 1, L)

    seq_len = prices.shape[2]

    # Initialize VAE
    vae = VAE(in_channels=1, out_channels=1, seq_len=seq_len)
    vae.load_state_dict(torch.load(model_file))
    vae.eval()

    # Select first n_samples
    test_batch = prices[:n_samples]

    with torch.no_grad():
        reconstructed, _, _ = vae(test_batch)

    reconstructed = reconstructed.cpu().squeeze(1)  # (B, L)
    original = test_batch.cpu().squeeze(1)          # (B, L)

    # Plot each sample
    for i in range(min(n_samples, original.size(0))):
        plt.figure(figsize=(10, 3))
        plt.plot(original[i].numpy(), label="Original", color="blue")
        plt.plot(reconstructed[i].numpy(), label="Reconstruction", color="red", linestyle="--")
        plt.title(f"Sample {i+1}")
        plt.legend()
        plt.show()


# Example usage:
if __name__ == "__main__":
    # np.random.seed(0)

    # signal  = load_raw_data("AMZN")[-360:]
    # find_similars(signal,0.1)
    # plt.plot(signal)

    # signal  = load_raw_data("AAPL")
    # data=signal.unfold(0,10,6)
    # data=(data-data.mean(dim=-1,keepdim=True))/(data.std(dim=-1,keepdim=True)+1e-4)
    # vae=train_estimator(data,filename="Test_VAE_10_64")
    # test_vae(data,"Test_VAE_10")

    # data=torch.randn(10,1,60)
    # idp=IDP(60,10,nb_index=3)
    # out=idp(data,[data,data,data])
    if(os.path.exists("GREENIUM_IDP.nn")):
        greenium_train,indices_train,trgt_train,greenium_test,indices_test,trgt_test=load_greenium_data(10)
        # trgt_test=(trgt_test-trgt_test.mean(dim=-1,keepdim=True))/(trgt_test.std(dim=-1,keepdim=True)+1e-4)

        model=IDP(greenium_train.size(-1),trgt_train.size(-1),nb_index=len(indices_train),in_channel=greenium_train.size(-2),out_channel=1)
        model.load_state_dict(torch.load("GREENIUM_IDP.nn"))
        preds=model(greenium_test,indices_test).detach()
        # preds=(preds-preds.mean(dim=-1,keepdim=True))/(preds.std(dim=-1,keepdim=True)+1e-4)
        # signs=preds[1:]-preds[:-1]
        # signs_trgt=trgt_test[1:]-trgt_test[:-1]
        # plt.plot(trgt_test,label="trgt")
        # plt.plot(preds,label="preds")
        # plt.legend()
        # plt.show()
        sign=torch.sign(preds.squeeze(1))
        sign_trgt=torch.sign(trgt_test)
        accuracy=(sign==sign_trgt).float().mean()
        print("Accuracy:",accuracy.item())
        plt.plot(trgt_test,label="trgt")
        plt.plot(preds,label="preds")
        plt.legend()
        plt.show()
        print(F.mse_loss(preds,trgt_test))

    else:
        greenium_train,indices_train,trgt_train,greenium_test,indices_test,trgt_test=load_greenium_data(10)
        model=train_IDP(greenium_train,indices_train,trgt_train,filename="GREENIUM_IDP")
        torch.save(model.state_dict(),"GREENIUM_IDP.nn")
        
    
