import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from data_loader import apply_feature
import matplotlib.pyplot as plt
import copy
import math
from customVAE import VAE
def gaussian_1d(x, mu=0.0, sigma=1.0):
    """
    Compute the 1D Gaussian function.
    :param x: Input tensor of x-values.
    :param mu: Mean of the Gaussian.
    :param sigma: Standard deviation of the Gaussian.
    :return: Tensor of Gaussian values.
    """
    A = 1 / (sigma * torch.sqrt(torch.tensor(2 * math.pi)))
    exponent = -((x - mu)**2) / (2 * sigma**2)
    return A * torch.exp(exponent)

def apply_gauss_1D_index(data,n,weights,end):
    
    
    s=n-15
    e=n+15
    sd=max(s,0)
    ed=min(e,end)
    sw=-min(s,0)
    ew=min(end-e,0)-1
    return data[sd:ed] @ weights[sw:ew] /weights[sw:ew].sum()

def apply_gauss_1D(data):
    res=list()
    ind=torch.arange(-15,16)
    weights=gaussian_1d(ind)
    end=data.size(0)
    for i in range(data.size(0)):
        res.append(apply_gauss_1D_index(data, i,weights,end))
    return torch.FloatTensor(res)

def apply_features(data,features,args):
    if features:
        feature_tensors = []
        for f in features:
            feature_sequences = [apply_feature(seq, f, args) for seq in data.squeeze(-1)]
            max_feature_len = max(len(fs) for fs in feature_sequences)  # Ensure consistent shape
            feature_tensor = torch.zeros((len(feature_sequences), max_feature_len))  # Padding
            for i, fs in enumerate(feature_sequences):
                feature_tensor[i, :len(fs)] = fs
            feature_tensors.append(feature_tensor.unsqueeze(2))  # Keep channel dimension

        feature_tensor = torch.cat(feature_tensors, dim=2)  # Stack features along the last axis
        # Concatenate Close price with extracted features
        final_tensor = torch.cat([feature_tensor, data], dim=-1)
    else:
        final_tensor = data  # Default to only 'Close' price
    return final_tensor


class transformer(nn.Module):
    def __init__(self,d_model=512,nhead=8,n_layers=6,d_latent=256,AE=None):
        super(transformer,self).__init__()
        self.d_model=d_model
        self.nhead=nhead
        self.n_layers=n_layers
        self.latent_mu=nn.Linear(d_model,d_latent)
        self.latent_sigma=nn.Linear(d_model,d_latent)

        self.activation=nn.Tanh()
        self.encoder=nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model,nhead,batch_first=True,dropout=0.005),n_layers)
        if AE:
            self.decoder=AE.decoder
            self.decompose=AE.decompose
        else:
            self.decoder=nn.TransformerDecoder(nn.TransformerDecoderLayer(d_model,nhead,batch_first=True,dropout=0.005),n_layers)
            self.decompose=nn.Linear(d_latent,d_model)

    def encode(self,data):
        rep=self.encoder(data)
        mu=self.latent_mu(rep[:,-1])
        sigma=self.latent_sigma(rep[:,-1])
        sigma_norm=sigma/sigma.norm(dim=1).unsqueeze(1)
        mu_norm=mu/mu.norm(dim=1).unsqueeze(1)
        res=sigma_norm+mu_norm
        out=self.activation(res).unsqueeze(1)
        print(out)
        return out
    def decode(self,memory,prev):
        return self.activation(self.decoder(prev,memory)[:,-1])
    def forward(self,data,prev):
        return self.decode((self.decompose(self.encode(data))),prev)
    

class Classifier(nn.Module):
    def __init__(self,d_input):
        super(Classifier,self).__init__()
        self.d_input=d_input

class Model(nn.Module):
    def __init__(self, d_input, d_model, d_output, num_layers=2, batch=True):
        super(Model, self).__init__()
        self.batch = batch
        self.d_model = d_model
        self.d_output = d_output

        # Embedding layers
        self.embeddings = nn.Linear(d_input + 1, d_model)  # +1 for positional encoding
        self.embeddings_out = nn.Linear(d_output + 1, d_model)

        


        #self.AE = transformer(d_model,nhead=8,n_layers=num_layers,d_latent=d_model//2)
        self.AE=VAE(d_output,8,64,128,4,2)
        self.encoder = nn.TransformerEncoder(nn.TransformerEncoderLayer(d_model,8,batch_first=True,dropout=0.1),num_layers)
        self.latent_mu=nn.Linear(d_model,d_model//2)
        self.latent_sigma=nn.Linear(d_model,d_model//2)
        # Final output layer
        self.f_out = nn.Linear(d_model, d_output)
        self.batch_size=5
        self.criterion=nn.MSELoss()
        self.optimizer=optim.Adam(self.parameters(),lr=0.1)
        self.activation=nn.Tanh()

    def positionalEncoding(self, data):
        """ Manually computed positional encoding, concatenated to input """
        if self.batch:
            seq_len = data.size(1)
            batch_size = data.size(0)
            enc_cumsum = torch.arange(0, seq_len).cumsum(0)
            enc =enc_cumsum/ max(enc_cumsum[-1],1)
            
            enc = enc.repeat((batch_size, 1)).unsqueeze(-1)  # (batch_size, seq_len, 1)
            return torch.cat([data, enc.to(data.device)], dim=-1)
        else:
            seq_len = data.size(0)
            enc = torch.arange(0, seq_len).cumsum(0)
            
            enc /= enc.sum()
            enc = enc.unsqueeze(-1)  # (seq_len, 1)
            return torch.cat([data, enc.to(data.device)], dim=-1)

    def shift_target(self, tgt):
        """ Shifts target sequence to the right for Transformer decoding """
        batch_size, seq_len, d_output = tgt.shape
        shifted_tgt = torch.zeros((batch_size, seq_len, d_output), device=tgt.device)
        shifted_tgt[:, 1:, :] = tgt[:, :-1, :]  # Shift right
        return shifted_tgt

    def AutoEncode(self,src):
        """
        src: (batch, seq_len, d_input)
        tgt: (batch, seq_len, d_output) -> Needs to be shifted before passing
        

        # Apply positional encoding
        src_enc = self.AE.decompose(self.AE.encode(self.embeddings_out(self.positionalEncoding(src))))   # (batch, seq_len, d_model)

        seq_len=src.size(1)
        tgt_enc = torch.zeros(src.size(0),seq_len+1,src.size(2))
        for i in range(0,seq_len):
            tgt_enc[:,i+1]=self.f_out(self.AE.decode(src_enc,self.embeddings_out(self.positionalEncoding(tgt_enc[:,:i+1]).detach())))

        # Final output projection
        return tgt_enc[:,1:],src_enc"""
        return self.AE(self.positionalEncoding(src).squeeze(0),src.size(1),self.positionalEncoding)
    def compute_loss_AE(self,src):
        """
        predictions,src_enc = self.AutoEncode(src)
        #diff1=predictions.diff(dim=1)
        #diff2=src.diff(dim=1)
        #loss2=diff1.norm(dim=1).sum()
        loss = torch.stack([self.criterion(p, s) for p,s in zip(predictions,src)]).sum()
        #loss=self.criterion(predictions,src)
        return loss
        #return loss"""
        return self.AE.loss(self.positionalEncoding(src),self.positionalEncoding)
    
    def train_AE(self,data):
        scaledData=(data-data.mean(dim=1).unsqueeze(1))/(data.std(dim=1).unsqueeze(1)+1e-5)
        dataset = TensorDataset(scaledData)
        
        # Create DataLoader for batching
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        for batch_data in dataloader:
                # Compute the loss
                self.optimizer.zero_grad()
                loss = self.compute_loss_AE(batch_data[0])
                print(loss)
                loss.backward()
                del(loss)
                self.optimizer.step()

        self.optimizer.zero_grad()
        for param in self.AE.parameters():
            param.requires_grad_(False)
        for param in self.embeddings_out.parameters():
            param.requires_grad_(False)
        
        plt.figure(figsize=(6, 4))
        plt.plot(data[10])
        plt.show()
        plt.figure(figsize=(6, 4))
        plt.plot(self.AutoEncode(data[10].unsqueeze(0)).detach())
        plt.show()
        plt.figure(figsize=(6, 4))
        plt.plot(data[1])
        plt.show()
        plt.figure(figsize=(6, 4))
        plt.plot(self.AutoEncode(data[1].unsqueeze(0)).detach())
        plt.show()
    def f(self, src, seq_len):
        """
        src: (batch, seq_len, d_input)
        tgt: (batch, seq_len, d_output) -> Needs to be shifted before passing
        """
        # Apply positional encoding
        src_enc = self.embeddings(self.positionalEncoding(src))   # (batch, seq_len, d_model)
        mu=self.latent_mu(self.encoder(src_enc)).mean(dim=1)
        sigma=self.latent_sigma(self.encoder(src_enc)).mean(dim=1)
        res=self.activation(torch.randn(1,requires_grad=False)*sigma+mu)
        latent=self.AE.decompose(res.unsqueeze(1))
        tgt_enc = torch.zeros(src.size(0),seq_len+1,self.d_output)
        for i in range(0,seq_len):
            tgt_enc[:,i+1]=self.f_out(self.AE.decoder(latent,self.embeddings_out(self.positionalEncoding(tgt_enc[:,:i+1].detach()))))

        # Final output projection
        return tgt_enc[:,1:]

    def compute_loss(self, src, tgt,features=None,args=None):
        """ Compute loss given input and target sequences """
        
        mu=self.latent_mu(self.encoder(self.embeddings(self.positionalEncoding(src)))).mean(dim=1)
        sigma=self.latent_sigma(self.encoder(self.embeddings(self.positionalEncoding(src)))).mean(dim=1)
        predictions=torch.randn(1,requires_grad=False)*sigma+mu
        

        internal_rep_tgt=self.AE.encode(self.embeddings_out(self.positionalEncoding(tgt)))

        print(internal_rep_tgt)
        print("mean: ",predictions.mean(dim=0))
        
        loss = torch.stack([self.criterion(p, t) for p,t in zip(predictions,internal_rep_tgt)]).sum()
        #loss = self.criterion(internal_rep_pred, internal_rep_tgt)
        
        return loss
    
    def forward(self, src, seq_len):
        with torch.no_grad():
            src-=src.mean(dim=1).unsqueeze(1)
            src/=src.std(dim=1).unsqueeze(1)
            print(src)
            
            
            # Apply positional encoding
            
            
            # Apply final output projection
            return torch.stack([apply_gauss_1D(d.squeeze(1)) for d in self.f(src,seq_len)[:,1:]])
    

    def train(self, data, target,VAE_data,features=None,args=None):

        print("training the AE")
        self.train_AE(VAE_data)
        scaledData=(data-data.mean(dim=1).unsqueeze(1))/(data.std(dim=1).unsqueeze(1)+1e-5)
        scaledTrgt=(target-target.mean(dim=1).unsqueeze(1))/(target.std(dim=1).unsqueeze(1)+1e-5)
        # Combine data and target into a dataset
        dataset = TensorDataset(scaledData, scaledTrgt)
        
        # Create DataLoader for batching
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        print("training the AR")
        for i in range(1):
            # Training loop
            for batch_data, batch_target in dataloader:
                # Compute the loss
                self.optimizer.zero_grad()
                loss = self.compute_loss(batch_data, batch_target,features,args)
                print(loss)
                loss.backward()
                del(loss)
                self.optimizer.step()



def test():
    d=512
    seq_len=60
    nb_sample=100
    data=torch.randn(nb_sample,seq_len,d)
    tr=transformer()
    x=tr.encode(data)
    print(x.size())
    y=torch.randn(nb_sample,1,d)
    prev=torch.zeros(data.size(0),1,d)
    print(tr.decode(y,prev).size())
if __name__=="__main__":
    test()

    
