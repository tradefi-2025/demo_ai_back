import torch
import torch.nn.functional as F
from data_loader import load_data
import matplotlib.pyplot as plt
import torch
import torch.nn.functional as F

from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

import torch
import torch.nn.functional as F
from line import Line
from pathlib import Path
import pandas as pd
import numpy as np




def gaussian_smooth_1d(x: torch.Tensor, kernel_size=31, sigma=4.0) -> torch.Tensor:
    """
    Apply 1D Gaussian smoothing with replicate padding.

    Args:
        x (torch.Tensor): Input of shape [batch_size, signal_length]
        kernel_size (int): Size of the Gaussian kernel (must be odd)
        sigma (float): Standard deviation of the Gaussian

    Returns:
        torch.Tensor: Smoothed signal, shape [batch_size, signal_length]
    """
    assert kernel_size % 2 == 1, "Kernel size must be odd"

    # Create Gaussian kernel
    half_k = kernel_size // 2
    t = torch.arange(-half_k, half_k + 1, dtype=x.dtype, device=x.device)
    kernel = torch.exp(-0.5 * (t / sigma)**2)
    kernel /= kernel.sum()
    kernel = kernel.view(1, 1, -1)  # shape: [out_channels, in_channels, kernel_size]

    # Reshape input: [B, L] -> [B, 1, L]
    x = x.unsqueeze(1)

    # Replicate padding: pad (left, right)
    x_padded = F.pad(x, (half_k, half_k), mode='replicate')

    # Convolve
    smoothed = F.conv1d(x_padded, kernel)

    return smoothed.squeeze(1)  # [B, L]

def central_difference_1d(x: torch.Tensor) -> torch.Tensor:
    """
    Apply central difference [-1/2, 0, 1/2] to a 1D batch of signals.

    Args:
        x (torch.Tensor): Input tensor of shape [batch_size, signal_length]

    Returns:
        torch.Tensor: Differentiated signal, same shape as input
    """
    # Define kernel
    kernel = torch.tensor([-0.5, 0.0, 0.5], dtype=x.dtype, device=x.device)
    kernel = kernel.view(1, 1, -1)  # shape [out_channels, in_channels, kernel_size]

    # Reshape input: [B, L] -> [B, 1, L]
    x = x.unsqueeze(1)

    # Replicate padding: pad 1 on each side
    x_padded = F.pad(x, (1, 1), mode='replicate')

    # Apply convolution
    dx = F.conv1d(x_padded, kernel)

    return dx.squeeze(1)  # shape: [B, L]


def find_min_max(data,deriv,lap,threshold_der,threshold_lap):
    peaks = []
    vals = []
    bases=[]
    for i in range(1, data.size(0)):
        thr=not(
            -threshold_der <= deriv[i] <= threshold_der and
            -threshold_lap <= lap[i] <= threshold_lap
        )
        # Peak: derivative changes from positive to negative
        if deriv[i - 1] >= 0 and deriv[i] < 0 :
            peaks.append(i)
        # Valley: derivative changes from negative to positive
        elif deriv[i - 1] <= 0 and deriv[i] > 0  :
            vals.append(i)
        elif( thr):
            bases.append(i)

    # Ensure beginning and end are included
    peaks = [0] + peaks
    vals = [0] + vals

    # Add global maximum and minimum if not included
    if peaks:
        arg_max = max(peaks, key=lambda i: data[i])
    else:
        arg_max = torch.argmax(data).item()
    if vals:
        arg_min = min(vals, key=lambda i: data[i])
    else:
        arg_min = torch.argmin(data).item()

    if arg_max not in peaks:
        peaks.append(arg_max)
    if arg_min not in vals:
        vals.append(arg_min)



    # Convert to tensor of (index, value)
    Ps = torch.LongTensor(peaks)
    Vs = torch.LongTensor(vals)
    Bs = torch.FloatTensor(bases)
    return Ps, Vs, Bs


def find_stationnary_points(data):
    """
    Detects characteristic points (peaks, valleys, and zero-crossing bases) 
    using smoothed derivatives.

    Args:
        data (torch.Tensor): 1D tensor of shape [L]
        kernel_size (int): Gaussian kernel size for smoothing
        sigma (float): Standard deviation for Gaussian kernel

    Returns:
        Ps (torch.Tensor): Peaks as [N, 2] tensor of (index, value)
        Vs (torch.Tensor): Valleys as [N, 2] tensor of (index, value)
        Bs (torch.Tensor): Bases (zero-crossings) as [N, 2]
    """


    # First and second derivatives
    smooth = gaussian_smooth_1d(data)
    deriv = central_difference_1d(smooth)
    lap = central_difference_1d(deriv)

    # Thresholds based on derivative statistics
    threshold_der = torch.abs(deriv.mean(dim=-1) - 0.5* deriv.std(dim=-1))
    threshold_lap = torch.abs(lap.mean(dim=-1) -  0.5*lap.std(dim=-1))
    res=[find_min_max(d,diff,l,th_der,th_lap) for d,diff,l,th_der,th_lap in  zip(data,deriv,lap,threshold_der,threshold_lap)]
    return [r[0] for r in res] , [r[1] for r in res], [r[2] for r in res]

def labelise(data):
    cls1,cls2,cls3 =find_stationnary_points(data)
    labels=torch.zeros_like(data)
    for l,c1,c2 in zip(labels,cls1,cls2):
        if(len(c1)):
            l[c1[1:]]=1
        if(len(c2)):
            l[c2[1:]]=2
    return labels.long()


def create_line_from_points(
    points, mu=0, std=1, push=0, V=1, weight_param=0, dt=1/390, nature='S'
):
    """
    Fit a line to a set of 2D points using least squares and return a `Line` object.

    Args:
        points (Tensor): Nx2 tensor of (x, y) points.
        mu (float): Mean drift parameter.
        std (float): Standard deviation.
        push (float): Initial push value.
        V (float): Velocity or sensitivity parameter.
        weight_param (float): Weight scaling.
        dt (float): Time delta.
        nature (str): Line type (e.g., 'S' or 'B').

    Returns:
        Line: Fitted line object.
    """
    if points.size(0) == 0:
        raise ValueError("Empty point set provided.")

    if points.size(0) == 1:
        return Line(a=0, b=points[0][1], mu=mu, std=std, push=push, V=V, dt=dt,
                    weight_param=weight_param, nature=nature)

    x = points[:, 0]
    y = points[:, 1]

    # Design matrix for linear regression
    X = torch.stack([x, torch.ones_like(x)], dim=1)

    # Solve least squares: a, b = (X^T X)^-1 X^T y
    coeffs = torch.linalg.pinv(X) @ y  # safer than .inverse()

    a, b = coeffs[0].item(), coeffs[1].item()
    return Line(a=a, b=b, mu=mu, std=std, push=push, V=V, dt=dt,
                weight_param=weight_param, nature=nature)


def find_sup_res(data):
    argmaxes,argmins,bases=find_stationnary_points(data)
    maxes=[torch.cat([am.unsqueeze(1),d[am.long()].unsqueeze(1)],dim=-1) for d,am in zip(data,argmaxes)]
    mins=[torch.cat([am.unsqueeze(1),d[am.long()].unsqueeze(1)],dim=-1) for d,am in zip(data,argmins)]
    Bases=[torch.cat([am.unsqueeze(1),d[am.long()].unsqueeze(1)],dim=-1) for d,am in zip(data,bases)]
    dt = torch.FloatTensor([1 / 390])
    RT = torch.log(data[:,1:] / data[:,:-1])
    Sigma = RT.std(dim=1,keepdim=True) / torch.sqrt(dt)
    MU = RT.mean(dim=1,keepdim=True) / dt + (Sigma**2) / 2

    threshold = data.mean(dim=1,keepdim=True) * abs(torch.exp(MU * dt - (Sigma**2) * dt / 2) + torch.sqrt(dt) * Sigma * 3 - 1)

    supports=[create_line_from_points(mns,mu,std,0,1,th if not torch.isnan(th) else torch.tensor(1.0),dt,'S') for mns,mu,std,th in zip (mins,MU,Sigma,threshold)]
    resistances=[create_line_from_points(mxs,mu,std,0,-1,th if not torch.isnan(th) else torch.tensor(1.0),dt,'R') for mxs,mu,std,th in zip (maxes,MU,Sigma,threshold)]
    bases=[create_line_from_points(mns,mu,std,0,0,th if not torch.isnan(th) else torch.tensor(1.0),dt,'B') for mns,mu,std,th in zip (maxes,MU,Sigma,threshold)]

    return supports,resistances

def IDGBM(
    S0: torch.Tensor,
    seq_len: int,
    mu: float,
    std: float,
    support: Line,
    resistance: Line,
    dt: float,
    t_0: int = 0
) -> torch.Tensor:
    """
    Generate a price trajectory using stochastic process influenced by support and resistance lines.

    Args:
        S0 (torch.Tensor): Initial price point as a tensor [t, price].
        seq_len (int): Number of time steps to simulate.
        mu (float): Base drift.
        std (float): Volatility (standard deviation).
        support (Line): Support line object.
        resistance (Line): Resistance line object.
        dt (float): Time delta.

    Returns:
        torch.Tensor: Price trajectory of shape [seq_len, 2] (time, price).
    """
    dt = torch.tensor([dt], dtype=torch.float32)
    std1 = (std ** 2) / 2
    random_shocks = torch.randn(seq_len)

    S_t = torch.FloatTensor([t_0,S0])
    trajectory = [S_t[1]]

    prev_sign = None

    for i in range(1, seq_len):
        # Influence weights
        w_res = resistance.w(S_t)
        w_supp = support.w(S_t)
        w_base = 0

        # Adjusted mus
        mu_res = resistance.mu(mu)
        mu_supp = support.mu(mu)
        mu_base = 0
        # Final drift
        total_weight = 1 + w_res + w_supp + w_base
        M = (mu + w_res * mu_res + w_supp * mu_supp + w_base * mu_base) / total_weight

        # Push update for base
        if w_base > 0:
            pass
        else:
            mu = M  # Update base mu for next step

        # Push logic based on drift direction change
        drift_sign = M.sign().item()
        if i == 1:
            prev_sign = drift_sign
        elif prev_sign == -1 and drift_sign == 1:
            support.update_push(S_t)
            prev_sign = 1
            min_val = S_t[1]
        elif prev_sign == 1 and drift_sign == -1:
            resistance.update_push(S_t)
            prev_sign = -1
            max_val = S_t[1]

        # Price update
        price = S_t[1] * torch.exp((M - std1) * dt + std * torch.sqrt(dt) * random_shocks[i])
        S_t_prev = S_t
        S_t = torch.tensor([S_t[0] + 1, price.item()])

        if torch.isnan(S_t[1]):
            raise RuntimeError(f"NaN price encountered at step {i}, drift: {M.item()}")

        trajectory.append(S_t[1])

    return torch.stack(trajectory)


def GBM(S0,seq_len,mu,std,dt,t_0=0):
    std1=(std**2)/2
    dt=torch.FloatTensor([dt])
    
    random_shocks=torch.randn(seq_len)
    S_t = torch.FloatTensor([t_0,S0])
    r=[S_t[1]]
    for i in range(1,seq_len):

        S_t=torch.FloatTensor([S_t[0]+1,S_t[1]*torch.exp((mu-std1)*dt + random_shocks[i]*torch.sqrt(dt)*std)])

        r.append(S_t[1])
    return torch.stack(r)



def augmentation(data,supp,res):
    dt = torch.FloatTensor([1 / 390])
    RT = torch.log(data[:,1:] / data[:,:-1])
    Sigma = RT.std(dim=1,keepdim=True) / torch.sqrt(dt)
    MU = RT.mean(dim=1,keepdim=True) / dt + (Sigma**2) / 2
    augmentaions=torch.stack([IDGBM(d[0],d.size(0),mu,std,s,r,dt) for d,mu,std,s,r in zip(data,MU,Sigma,supp,res)])
    return augmentaions


def out_of_sample(data,target,loss,t_0=0):
    """
    Check if the data is out of sample with respect to the support and resistance lines.
    """


    supp, res = find_sup_res(data)
    a=torch.FloatTensor([s.b for s in supp])
    b=torch.FloatTensor([r.b for r in res])
    c=target[:,0]
    
    x=c-(a+b)/2
    for i in range(len(supp)):
        supp[i].b=supp[i].b+x[i]
        res[i].b=res[i].b+x[i]
    

    dt = torch.FloatTensor([1 / 390])
    RT = torch.log(data[:,1:] / data[:,:-1])
    Sigma = RT.std(dim=1,keepdim=True) / torch.sqrt(dt)
    MU = RT.mean(dim=1,keepdim=True) / dt + (Sigma**2) / 2

    idgbm=torch.stack([IDGBM(t[0],t.size(0),mu,std,s,r,dt,t_0=t_0) for t,mu,std,s,r in zip(target,MU,Sigma,supp,res)])
    gbm=torch.stack([GBM(t[0],t.size(0),mu,std,dt,t_0=t_0) for t,mu,std in zip(target,MU,Sigma)])
    
    idgbm=(idgbm-idgbm.mean(dim=-1,keepdim=True))/(idgbm.std(dim=-1,keepdim=True)+1e-4)
    gbm=(gbm-gbm.mean(dim=-1,keepdim=True))/(gbm.std(dim=-1,keepdim=True)+1e-4)
    target=(target-target.mean(dim=-1,keepdim=True))/(target.std(dim=-1,keepdim=True)+1e-4)

    loss_idgbm = torch.stack([loss(i, t) for i, t in zip(idgbm, target)])
    loss_gbm =torch.stack([loss(i, t) for i, t in zip(gbm, target)])

    # loss_idgbm=torch.log(loss_idgbm+1)
    # loss_gbm=torch.log(loss_gbm+1)

    
    # print(f"IDGBM Loss: {loss_idgbm.mean().item()}")
    # print(f"GBM Loss: {loss_gbm.mean().item()}")
    # print(f"IDGBM Loss: {loss_idgbm.std().item()}")
    # print(f"GBM Loss: {loss_gbm.std().item()}")
    
    return loss_idgbm,loss_gbm


def robust_scale(tensor, dim=None, eps=1e-8):
    """
    Robust scale tensor along dimension dim:
    (x - median) / IQR
    
    Args:
      tensor (torch.Tensor): input tensor
      dim (int or None): dimension to reduce; None for entire tensor
      eps (float): small number to avoid division by zero
    
    Returns:
      torch.Tensor: scaled tensor
    """
    median = tensor.median(dim=dim, keepdim=True).values
    q1 = tensor.kthvalue(k=int(0.25 * tensor.size(dim)), dim=dim, keepdim=True).values
    q3 = tensor.kthvalue(k=int(0.75 * tensor.size(dim)), dim=dim, keepdim=True).values
    iqr = q3 - q1
    iqr = iqr.clamp(min=eps)  # avoid division by zero
    
    scaled = (tensor - median) / iqr
    return scaled



def pearson_corr(x: torch.Tensor, y: torch.Tensor) -> float:
    
    x = x.numpy()
    y = y.numpy()

    distance, path = fastdtw(x, y, dist=euclidean)
    
    return torch.FloatTensor([distance])



def pearsonr(x: torch.Tensor,
             y: torch.Tensor,
             dim: int = -1,
             eps: float = 1e-8,
             ddof: int = 0) -> torch.Tensor:
    """
    Pearson correlation between x and y along `dim`.

    Args:
        x, y: Tensors with the same shape (broadcasting not applied).
        dim: Dimension to reduce over.
        eps: Small constant to avoid division by zero.
        ddof: Degrees of freedom used in variance (0 = population, 1 = sample).
    Returns:
        Tensor of correlations with `dim` removed.
    """
    if x.shape != y.shape:
        raise ValueError("x and y must have the same shape")

    xm = x.mean(dim=dim, keepdim=True)
    ym = y.mean(dim=dim, keepdim=True)

    xc = x - xm
    yc = y - ym

    # covariance
    n = x.size(dim)
    cov = (xc * yc).sum(dim=dim) / max(1, (n - ddof))

    # standard deviations
    vx = (xc * xc).sum(dim=dim) / max(1, (n - ddof))
    vy = (yc * yc).sum(dim=dim) / max(1, (n - ddof))
    denom = (vx.clamp_min(0).sqrt() * vy.clamp_min(0).sqrt()).clamp_min(eps)

    r = cov / denom
    # clamp to valid range to avoid tiny numerical overshoot
    return r.clamp(-1.0, 1.0)


def run_experiment_for_ticker(ticker, loss,save_dir):
    # try:
        # Load 1-minute intraday data for each trading day from 9:30 to 16:00
        data = load_data(ticker, "1min", {"start": "9:30", "end": "16:00"})[0]

        if data.size(1) < 10:
            print(f"Skipping {ticker}: insufficient data")
            return None

        # Extract open and close 30-minute windows
        open_window = data[:, :30]  # 9:30 to 10:00 AM
        close_window = data[:, -30:]  # 3:30 to 4:00 PM

        open_window = open_window.view(open_window.size(0), -1)
        close_window = close_window.view(close_window.size(0), -1)

        # Evaluate forecasting models
        idgbm_corr, gbm_corr = out_of_sample(open_window, close_window, loss,t_0=0)

        results = {
            "ticker": ticker,
            "IDGBM_log_r": idgbm_corr.squeeze(1),
            "GBM_log_r": gbm_corr.squeeze(1),
        }
        print(idgbm_corr.mean())
        print(gbm_corr.mean())
        df = pd.DataFrame(results)
        df.to_csv(save_path)
        print(f"Completed: {ticker}")
        return results

    # except Exception as e:
    #     print(f"Error with {ticker}: {e}")
    #     return None

    

if __name__ == "__main__":
    tickers = [
        "NVDA", "MSFT", "AAPL", "AMZN", "GOOG",
        "META", "AVGO", "TSLA", "JPM"
    ]

    results = []
    

    for ticker in tickers:
        # for loss in ["F.mse_loss","torch.nn.L1Loss()","pearson_corr"]:
        for loss in ["pearson_corr"]:
            print(ticker,loss)
            save_path = Path(f"./intraday_model_comparison_{ticker}_{loss}.csv")
            result = run_experiment_for_ticker(ticker, eval(loss),save_path)
            
            


