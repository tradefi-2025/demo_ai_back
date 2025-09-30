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
from generator import Generator1D, SequenceEncoder1D,ForecastingDataset

class CNNVAE(nn.Module):
    def __init__(self, input_dim, latent_dim):
        super(CNNVAE, self).__init__()
        self.input_dim = input_dim
        self.latent_dim = latent_dim 
        self.encoder  = SequenceEncoder1D(base_channels=8)
        self.sigmoid = nn.Sigmoid()
        self.fc_mu = nn.Linear(512, latent_dim)
        self.fc_logvar = nn.Linear(512, latent_dim)
        
        self.decoder_fc = nn.Linear(latent_dim, 512)
        
        self.decoder = nn.Sequential(
            nn.ConvTranspose1d(64, 64, kernel_size=3, stride=2, padding=1),
            nn.LeakyReLU(),
            nn.ConvTranspose1d(64, 64, kernel_size=3, stride=2, padding=1),
            nn.LeakyReLU(),
            nn.ConvTranspose1d(64, 64, kernel_size=3, stride=2, padding=1),
            nn.LeakyReLU()
        )
        self.last_cnn=nn.ConvTranspose1d(64, 1, kernel_size=3, stride=2, padding=1)
        

    def reparameterize(self, mu, logvar):
        std = torch.exp(0.5 * logvar)
        eps = torch.randn_like(std)
        return mu + eps * std
    
    def encode(self, x):
        enc = self.encoder(x)
        enc = enc.view(enc.size(0), -1)
        mu = self.fc_mu(enc)
        logvar = self.fc_logvar(enc)
        return mu, logvar
    
    def decode(self, z):
        x = self.decoder_fc(z)
        x = x.view(x.size(0), 64, -1)
        return self.decoder(x)
    
    def loss_function(self, recon_x, x, mu, logvar):
        BCE = nn.MSELoss()(recon_x, x)
        KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
        return BCE + KLD + recon_x.diff(dim=-1).abs().mean()  # Adding a small penalty for smoothness
    
    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return F.interpolate(self.last_cnn(self.decode(z)),size=self.input_dim,mode='linear', align_corners=False ), mu, logvar
    
def train_vae(indicators,sequence,target):

    
    model = CNNVAE(input_dim=target.size(2), latent_dim=64)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    dataset = ForecastingDataset(indicators, sequence,target)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True, num_workers=4)
    model.train()
    for epoch in range(100):  # Number of epochs can be adjusted
        for segment_batch, pose_batch, target_batch in dataloader:
            optimizer.zero_grad()
            target_batch= target_batch-target_batch[:,:,0].unsqueeze(-1)
            output, mu, logvar = model(target_batch)
            # output = output-output[:,:,0].unsqueeze(-1)

            loss = model.loss_function(output, target_batch, mu, logvar)
            
            loss.backward()
            print(f"Epoch {epoch}, Loss: {loss.item()}")
            optimizer.step()

    return model

if __name__ == "__main__":
    x=torch.randn(32, 1, 120)  # Batch size of 32, 1 channel, sequence length of 512
    model = CNNVAE(input_dim=120, latent_dim=64)
    output, mu, logvar = model(x)
    loss = model.loss_function(output, x, mu, logvar)
    print("Output shape:", output.shape)
    print("Mu shape:", mu.shape)
    print("Logvar shape:", logvar.shape)

    print("Loss:", loss.item())

