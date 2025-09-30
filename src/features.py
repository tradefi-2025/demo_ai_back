
import torch

"""
this is a test for adding a new interface
"""
def Example2(var1):
    var2 = "TO DO"
    return var2







"""
this is an example of how to generate interfaces. The interface files should follow the same structure.

"""
def Example(var1 , var3):
    var2 = "TO DO"
    return var2











def EMA(data: torch.Tensor, t: int) -> torch.Tensor:
    """
    Compute the Exponential Moving Average (EMA).
    
    Parameters:
        data (torch.Tensor): 1D tensor of stock prices.
        period (int): Number of periods for EMA calculation.
        
    Returns:
        torch.Tensor: EMA values.
    """
    alpha = 2 / (t + 1)
    ema = torch.zeros_like(data)
    ema[0] = data[0]  # Initialize with the first data point

    for i in range(1, len(data)):
        ema[i] = (data[i] - ema[i - 1]) * alpha + ema[i - 1]
    
    return ema


def MACD(data: torch.Tensor, t1: int = 12, t2: int = 26) -> torch.Tensor:
    """
    Compute the MACD indicator.
    
    Parameters:
        data (torch.Tensor): 1D tensor of stock prices.
        t1 (int): Short-term EMA period.
        t2 (int): Long-term EMA period.
        
    Returns:
        torch.Tensor: MACD values.
    """
    ema_short = EMA(data, t1)
    ema_long = EMA(data, t2)
    macd = ema_short - ema_long
    return macd


def BollBands(data: torch.Tensor, n: int = 20, k: float = 2.0) -> tuple:
    """
    Compute Bollinger Bands.
    
    Parameters:
        data (torch.Tensor): 1D tensor of stock prices.
        n (int): Moving average period.
        k (float): Number of standard deviations.
        
    Returns:
        Tuple[torch.Tensor, torch.Tensor, torch.Tensor]: (middle_band, upper_band, lower_band)
    """
    sma = SMA(data, n)
    std = torch.zeros_like(data)
    
    for i in range(n - 1, len(data)):
        std[i] = torch.std(data[i - n + 1 : i + 1])

    upper_band = sma + k * std
    lower_band = sma - k * std

    return sma, upper_band, lower_band


def SMA(data: torch.Tensor, t: int) -> torch.Tensor:
    """
    Compute the Simple Moving Average (SMA).
    
    Parameters:
        data (torch.Tensor): 1D tensor of stock prices.
        t (int): SMA period.
        
    Returns:
        torch.Tensor: SMA values.
    """
    sma = torch.zeros_like(data)

    for i in range(t - 1, len(data)):
        sma[i] = torch.mean(data[i - t + 1 : i + 1])

    return sma











