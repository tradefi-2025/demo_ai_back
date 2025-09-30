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

class ForecastingDataset(Dataset):
    def __init__(self, segments, poses,target):
    
        self.segments = segments
        self.poses = poses
        self.target= target
    def __len__(self):
        return len(self.poses)

    def __getitem__(self, idx):
        return self.segments[idx], self.poses[idx], self.target[idx]


class Map(nn.Module):
    def __init__(self,d_input,d_hidden,d_output,nb_layers=6):
        super(Map,self).__init__()
        self.d_input=d_input
        self.d_output=d_output
        self.d_hidden=d_hidden
        self.embedding_in=nn.Linear(d_input,d_hidden)
        self.embedding_out=nn.Linear(d_hidden,d_output)
        self.hiddens=nn.ModuleList([nn.Linear(d_hidden,d_hidden) for i in range(nb_layers)])
        self.activation=nn.LeakyReLU()

    def forward(self,X):
        out=self.activation(self.embedding_in(X))
        for h in self.hiddens:
            out=self.activation(h(out))

        return self.embedding_out(out)


def adain_1d(content_feat, gamma, beta, eps=1e-5):
    """
    Adaptive Instance Normalization (AdaIN) for 1D data

    Args:
        content_feat: content features (B, C, L)
        gamma: scale parameters from affine(w) (B, C)
        beta: bias parameters from affine(w) (B, C)
    Returns:
        normalized and modulated features (B, C, L)
    """
    B, C, L = content_feat.shape

    # Instance norm over length dimension
    mean = content_feat.mean(dim=2, keepdim=True)
    std = content_feat.std(dim=2, keepdim=True) + eps
    normalized = (content_feat - mean) / std

    # Reshape gamma and beta to broadcast over L
    gamma = gamma.view(B, C, 1)
    beta = beta.view(B, C, 1)

    return gamma * normalized + beta
def is_positive_definite(A):
        try:
            _ = torch.linalg.cholesky(A)
            return True
        except RuntimeError:
            return False
class ProbabilisticLayer(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(ProbabilisticLayer, self).__init__()
        self.input_dim = output_dim  # Total dimension for the multivariate normal distribution
        self.output_dim = output_dim
        self.affine_transform=nn.Linear(input_dim, output_dim)

        
        self.mu= nn.Parameter(torch.randn(output_dim*2), requires_grad=True)
        raw= torch.randn((output_dim*2, output_dim*2))
        L=torch.tril(raw, diagonal=-1)
        diag=torch.diag(raw)
        diag_pos=F.relu(diag)+ 1e-3  # ensure strictly positive
        L.fill_diagonal_(0)
        L+= torch.diag(diag_pos)
        L/= torch.linalg.norm(L, dim=1, keepdim=True)  # Normalize rows to ensure stability
        self.L = nn.Parameter(L, requires_grad=True)  # Lower triangular matrix for Cholesky decomposition

    
    def forward(self, x):
        """
        x: Tensor of shape [batch_size, input_dim]
        Returns: MultivariateNormal distribution over y | x
        """
        
        D = self.input_dim + self.output_dim
        μ = self.mu

        # Reconstruct L with softplus diagonal to ensure positivity
        raw_L = self.L
        L = torch.tril(raw_L, diagonal=-1)  # strictly lower triangle
        diag = torch.diagonal(raw_L)
        diag_pos = F.softplus(diag) + 1e-3  # ensure strictly positive
        L += torch.diag(diag_pos)
        L =L/ torch.linalg.norm(L, dim=1, keepdim=True)  # Normalize rows to ensure stability
        # Compute full covariance
        Σ = L @ L.T
        
        # Partition mean
        μ_x = μ[:self.input_dim]
        μ_y = μ[self.input_dim:]

        # Partition covariance
        Σ_xx = Σ[:self.input_dim, :self.input_dim]
        Σ_xy = Σ[:self.input_dim, self.input_dim:]
        Σ_yx = Σ_xy.T
        Σ_yy = Σ[self.input_dim:, self.input_dim:]

        # Compute conditional mean and covariance
        Σ_xx_inv = torch.linalg.inv(Σ_xx)
        μ_y_given_x = μ_y + (self.affine_transform(x) - μ_x) @ Σ_xx_inv @ Σ_xy
        Σ_y_given_x = Σ_yy - Σ_yx @ Σ_xx_inv @ Σ_xy
        r=torch.randn((x.shape[0], self.output_dim), device=x.device)  # random noise for sampling
        y = μ_y_given_x + r @ torch.linalg.cholesky(Σ_y_given_x).T
        return y  

        
class AffineTransform(nn.Module):
    def __init__(self, latent_dim, num_channels):
        super().__init__()
        self.fc = nn.Linear(latent_dim, num_channels * 2)  # outputs gamma and beta

    def forward(self, w):
        style = self.fc(w)              # shape: [batch_size, 2C]
        gamma, beta = style.chunk(2, dim=1)  # split into two [batch_size, C]
        return gamma, beta



class IndicatorBlock(nn.Module): 
    def __init__(self, L, in_channels, out_channels, d_latent, batch_size=1, is_first=False,kernel_size=3):
        super(IndicatorBlock, self).__init__()
        self.is_first = is_first
        self.L = L
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.batch_size = batch_size
        self.probabilistic_layer1 = ProbabilisticLayer(d_latent, out_channels*2)
        self.probabilistic_layer2 = ProbabilisticLayer(d_latent, out_channels*2)
        if not is_first:
            self.conv1 = nn.Conv1d(in_channels=in_channels, out_channels=out_channels, kernel_size=kernel_size, padding=kernel_size//2)
            self.upsample = nn.Upsample(size=self.L, mode="linear", align_corners=True)
        else:
            self.const_in = None

        self.conv2 = nn.Conv1d(in_channels=out_channels, out_channels=out_channels, kernel_size=kernel_size, padding=kernel_size//2)
        self.B1 = nn.Parameter(torch.randn(out_channels))
        self.A1 = AffineTransform(d_latent, out_channels)
        self.B2 = nn.Parameter(torch.randn(out_channels))
        self.A2 = AffineTransform(d_latent, out_channels)

    def forward(self, latent, prev=None):
        noise = torch.randn((self.batch_size, 1, self.L), requires_grad=False)
        noise = self.B1.view(1, -1, 1) * noise
        if self.is_first:
            assert prev is not None
            first_noise = prev + noise
        else:
            assert prev is not None
            upsampled = self.upsample(prev)
            first_noise = self.conv1(upsampled) + noise

        # ys, yb = self.A1(latent)
        ys, yb = self.probabilistic_layer1(latent).chunk(2, dim=1)
        inject1 = adain_1d(first_noise, ys, yb)

        noise2 = torch.randn((self.batch_size, 1, self.L), requires_grad=False)
        noise2 = self.B2.view(1, -1, 1) * noise2
        second_noised = self.conv2(inject1) + noise2

        # ys2, yb2 = self.A2(latent)
        ys2, yb2 = self.probabilistic_layer2(latent).chunk(2, dim=1)
        out = adain_1d(second_noised, ys2, yb2)
        
        return out 

    def loss(self):
        return self.B1.abs().mean() + self.B2.abs().mean() + \
               self.A1.fc.weight.abs().mean() + self.A2.fc.weight.abs().mean() + \
                self.A1.fc.bias.abs().mean() + self.A2.fc.bias.abs().mean()
    
class SequenceEncoder1D(nn.Module): 
    def __init__(self, input_channels=1, base_channels=64):
        super(SequenceEncoder1D, self).__init__()
        self.distribution = ProbabilisticLayer(base_channels*8, base_channels*8)
        self.encoder = nn.Sequential(
            nn.Conv1d(input_channels, base_channels, kernel_size=7, stride=2, padding=3),   # L → L/2
            nn.LeakyReLU(),
            nn.Conv1d(base_channels, base_channels * 2, kernel_size=5, stride=2, padding=2), # L/2 → L/4
            nn.LeakyReLU(),
            nn.Conv1d(base_channels * 2, base_channels * 4, kernel_size=3, stride=1, padding=1), # L/4 → L/4
            nn.LeakyReLU(),
            nn.Conv1d(base_channels * 4, base_channels * 8, kernel_size=3, stride=1, padding=1), # L/4 → L/4
            nn.LeakyReLU(),
        )

        self.residual = nn.Sequential(
            nn.Conv1d(input_channels, base_channels * 8, kernel_size=1, stride=4),  # Match shape
        )

    def forward(self, x):
        # x: (B, C, L), assume L ≥ 64

        x = F.interpolate(x, size=32, mode='linear', align_corners=False)  # Optional: force input to fixed length
        out = self.encoder(x)
        res = self.residual(x)
        out=out + res

        return torch.stack([self.distribution(o.permute(1,0)) for o in out]).permute(0,2,1)  # (B, 2, C, L)
           



class SegmentEncoder1D(nn.Module):
    def __init__(self, input_channels=3, latent_dim=512):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv1d(input_channels, 64, kernel_size=7, stride=2, padding=3),  # L → L/2
            nn.LeakyReLU(),
            nn.Conv1d(64, 128, kernel_size=5, stride=2, padding=2),             # L/2 → L/4
            nn.LeakyReLU(),
            nn.Conv1d(128, 256, kernel_size=3, stride=2, padding=1),            # L/4 → L/8
            nn.LeakyReLU(),
            nn.AdaptiveAvgPool1d(1),  # global avg pool over sequence
            nn.Flatten(),             # shape: (B, 256)
            nn.Linear(256, latent_dim)  # output latent vector
        )

    def forward(self, x):
        # x: (B, C, L), e.g., (B, 3, 128)
        x = F.interpolate(x, size=64, mode='linear', align_corners=False)  # Optional: standardize input length
        return self.encoder(x)  # shape: (B, latent_dim)
    

def repulsion_loss_euclidean(latents):
    """
    latents: (B, C, L)
    Goal: encourage high L2 distance between flattened latent vectors
    """
    B = latents.size(0)
    latents = latents.view(B, -1)  # Flatten to (B, C*L)
    diffs = latents.unsqueeze(1) - latents.unsqueeze(0)  # (B, B, C*L)
    dists = torch.norm(diffs, dim=2)  # (B, B)
    mask = ~torch.eye(B, dtype=torch.bool, device=latents.device)
    loss=dists[mask].mean()    
    return -loss*(loss.detach()<124) # Negative: maximize distance

class Generator1D(nn.Module):
    def __init__(self, L, d_latent,nb_indicators=6,L_out=64):
        super(Generator1D, self).__init__()
        self.config = {
            'L': L,
            'd_latent': d_latent,
            'nb_indicators': nb_indicators,
            'L_out': L_out,
        }
        self.L = L
        self.nb_indicators = nb_indicators
        self.d_latent = d_latent
        self.seqEncoder = SequenceEncoder1D(input_channels=nb_indicators,base_channels=d_latent//8)  # must output (B, C, L/8) for consistency
        self.indEncoder = SegmentEncoder1D(input_channels=1,latent_dim=d_latent)
        self.latentMapper = Map(d_latent, d_latent * 2, d_latent)
        self.L_out = L_out
        nb_blocks = torch.log2(torch.tensor(L_out)).item()+1  # number of blocks to reach L_out
        kernel_sizes=[3,5,7]
        self.synthesis = nn.ModuleList([
            IndicatorBlock(2**i, d_latent, d_latent, d_latent, is_first=(i==3),kernel_size=kernel_sizes[min(i-3,2)])
            for i in range(3,int(nb_blocks) + 1)
        ])

        self.output_segmentation = nn.Conv1d(d_latent, 3, kernel_size=1)
        self.criterion = nn.CrossEntropyLoss()

    def forward(self, indicators, sequence):
        
        B = sequence.shape[0]

        # Encode pose

        prev = self.seqEncoder(indicators)  # (B, 512, L/64) or similar
        encodings=prev.clone()  # Keep a copy for loss calculation
        # Concatenate and map
        w = self.latentMapper(self.indEncoder(sequence))         # (B, d_latent)

        # Synthesis
        for s in self.synthesis:

            prev = s(w, prev)

        # Output segmentation logits (B, 8, L)
        pred = self.output_segmentation(prev)
        return F.interpolate(pred, size=self.L_out, mode='linear', align_corners=False),encodings,w  # Optional: standardize input length
    
    def loss(self):
        loss = 0
        for s in self.synthesis:
            loss += s.loss()
        return loss
    

def repulsion_loss_cosine(latents):
    """
    latents: tensor of shape (B, C, L)
    Goal: maximize dissimilarity across batch
    """
    B = latents.size(0)
    # Flatten channel and spatial/temporal dimensions
    latents = latents.view(B, -1)              # (B, C*L)
    latents = F.normalize(latents, dim=1)      # Normalize along feature dim
    sim_matrix = torch.matmul(latents, latents.T)  # (B, B) cosine similarities
    mask = ~torch.eye(B, dtype=torch.bool, device=latents.device)
    return (sim_matrix[mask].mean())  # Higher = more similar → penalize




def gaussian_smooth_bcl(x, kernel_size=5, sigma=1.0):
    """
    Apply 1D Gaussian smoothing to a tensor of shape (B, C, L).
    
    Args:
        x (Tensor): Input tensor of shape (B, C, L)
        kernel_size (int): Size of the Gaussian kernel (should be odd)
        sigma (float): Standard deviation of the Gaussian

    Returns:
        Tensor: Smoothed tensor of shape (B, C, L)
    """
    if kernel_size % 2 == 0:
        raise ValueError("kernel_size should be odd")

    # Create Gaussian kernel
    half_k = kernel_size // 2
    t = torch.arange(-half_k, half_k + 1, dtype=torch.float32, device=x.device)
    kernel = torch.exp(-0.5 * (t / sigma) ** 2)
    kernel = kernel / kernel.sum()

    # Shape for conv1d: (out_channels=C, in_channels=1, kernel_size)
    kernel = kernel.view(1, 1, -1)
    kernel = kernel.repeat(x.size(1), 1, 1)  # (C, 1, K)

    # Pad and apply conv1d per channel
    x = F.pad(x, (half_k, half_k), mode='reflect')
    smoothed = F.conv1d(x, weight=kernel, groups=x.size(1))

    return smoothed



def drift_labels(labels, max_shift=3):
    """
    Randomly shifts labels left or right by up to max_shift steps.
    Args:
        labels: (T,) or (B, T) tensor of per-time-step labels.
        max_shift: max number of steps to drift left or right.
    Returns:
        Tensor of same shape with shifted labels.
    """
    if labels.ndim == 1:
        labels = labels.unsqueeze(0)

    B, T = labels.shape
    shifted = torch.empty_like(labels)

    for b in range(B):
        shift = random.randint(-max_shift, max_shift)
        if shift < 0:
            shifted[b, :shift] = labels[b, -shift:]
            shifted[b, shift:] = labels[b, 0]
        elif shift > 0:
            shifted[b, shift:] = labels[b, :-shift]
            shifted[b, :shift] = labels[b, -1]
        else:
            shifted[b] = labels[b]

    return shifted.squeeze(0) if labels.shape[0] == 1 else shifted

def train_estimator(indicators,sequence,target,filename=None):
    
    labels=labelise(target.view(target.shape[0],-1)).long()
    
    dataset = ForecastingDataset(indicators, sequence,labels)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True, num_workers=4)
    model = Generator1D(sequence.size(2), d_latent=64,nb_indicators=indicators.size(1),L_out=target.size(2))
    if filename is not None:
        model.load_state_dict(torch.load(filename+'.nn'))

    print(f"Input shape: {indicators.shape}, Sequence shape: {sequence.shape}, Target shape: {target.shape}")
    # model=model.cuda()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4, betas=(0.5, 0.999))
    criterion = nn.CrossEntropyLoss()
    mseLoss=nn.MSELoss()
    total_loss = 3
    epoch=0
    for epoch in range(200):
        
        total_loss = 0
        i=1
        for segment_batch, pose_batch, target_batch in dataloader:
            # segment_batch = segment_batch.cuda()
            # pose_batch = pose_batch.cuda()
            # target_batch = target_batch.cuda()  # (B, H, W)
            # plt.plot(target_batch[2,0].detach())
            # plt.show()
            # raise

            optimizer.zero_grad()
            
            
            # supp,res=find_sup_res(target_batch.squeeze(1))
            if(torch.rand(1)<0.9):
                target_batch=drift_labels(target_batch,max_shift=2)
                # augm=augmentation(target_batch.squeeze(1),supp,res).unsqueeze(1)
            # else:
                # augm=target_batch

            # target_batch=labelise(augm)

            # segment_batch = gaussian_smooth_bcl(segment_batch)
            # target_batch = gaussian_smooth_bcl(target_batch)
            logits,latents,w = model(segment_batch, pose_batch)  # (B, 8, H, W)
            
            # target_batch = (target_batch.diff(dim=2)>0).long().squeeze(1)  # Convert to binary classification (up/down)
            # logits = logits - logits[:,:,0].unsqueeze(2) + target_batch[:,:,0].unsqueeze(2)  # Normalize logits to avoid numerical issues
            # diff_matrix_logits= torch.stack([logits[:,:,i].unsqueeze(1)- logits for i in range(logits.size(2))]).permute(1, 2, 0, 3)  # (B, L, 8, 8) 
            # diff_matrix_trgt= torch.stack([target_batch[:,:,i].unsqueeze(1)- target_batch for i in range(target_batch.size(2))]).permute(1, 2, 0, 3)  # (B, L, 8, 8) 
            # diff1= logits.diff(dim=2)
            # diff2= target_batch.diff(dim=2)
            # if i==3:
            #     plt.plot(logits[0,0].detach())
            #     plt.plot(target_batch[0,0].detach())
            #     plt.show()
            # i+=1
            # l1=criterion(logits, target_batch)
            # l2=mseLoss(diff1, diff2)
            # l3=criterion(diff_matrix_logits,diff_matrix_trgt)
            # l4=repulsion_loss_euclidean(latents)
            # l5=0.1*repulsion_loss_euclidean(w)
            # l6=0.001*model.loss()
            # l7=diff1.abs().mean()
            # print(f"Losses - L1: {l1.item():.4f}, L2: {l2.item():.4f}, L3: {l3.item():.4f}, L4: {l4.item():.4f}, L5: {l5.item():.4f}, L6: {l6.item():.4f}, L7: {l7.item():.4f}")
            # loss =    l1 + l2 + l7 + l3
            # loss= criterion(logits, target_batch)  # Cross-entropy loss
            loss=criterion(logits,target_batch)
            # loss=mseLoss(logits, augm)+0.1*l2+0.1*l7

            total_loss += loss.item()
            print(loss)
            loss.backward()
            optimizer.step()

        print(f"Epoch {epoch} - Loss: {total_loss:.4f}")

    return model



if __name__=="__main__":
    layer = ProbabilisticLayer(input_dim=64, output_dim=64)
    x = torch.randn(10, 64)  # batch of 10 inputs
    samples,y = layer(x)
    print(samples.shape)  # should be (10, 2), i.e., 10 samples of 2-dimensional output
    print(samples)