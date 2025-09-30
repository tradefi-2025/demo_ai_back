import torch
import torch.nn.functional as F
import pandas as pd
from features import *
import os
import matplotlib.pyplot as plt

from datetime import datetime, timedelta
import refinitiv.data as rd


def replace_zeros_with_day_avg(prices: torch.Tensor):
    """
    Args:
        prices: Tensor of shape (N, T) containing intraday prices
    Returns:
        Tensor of same shape with 0s replaced by per-day non-zero average
    """
    # Mask of zeros
    
    zero_mask = prices == 0
    # Compute sum and count of non-zero elements per row
    non_zero_sum = torch.sum(prices * (~zero_mask), dim=1)  # shape (N,)
    non_zero_count = torch.sum(~zero_mask, dim=1)            # shape (N,)

    # Avoid division by zero
    day_avg = non_zero_sum / torch.clamp(non_zero_count, min=1)  # shape (N,)

    # Expand day_avg to match prices shape
    day_avg_expanded = day_avg.unsqueeze(1).expand_as(prices)

    # Replace 0s with day average
    prices_fixed = torch.where(zero_mask, day_avg_expanded, prices)

    return prices_fixed


def derivatives(data,dim):
    res=[]
    out=data
    for i in range(1,dim):
        out=out.diff(dim=-1)
        res.append(out[:,:-dim+i])
    res.append(data[:,:-dim])
    return torch.stack(res,dim=1).permute(0,2,1)


def fill_missing(df):
    valid_keys = [col for col in df.columns if not col.startswith("Unnamed")]
    for vk in valid_keys:
        cols = df.columns
        idx = cols.get_loc(vk)  # Get the index of the given column
        selected_columns = df.iloc[:, idx:idx+2]
        selected_columns.columns = ["Timestamp", "Close"]  # Rename columns
        selected_columns = selected_columns.iloc[1:]  # Remove the first row with column headers
        selected_columns = selected_columns.dropna()
        selected_columns["Timestamp"] = pd.to_datetime(selected_columns["Timestamp"])  # Convert to datetime
        selected_columns["Close"] = pd.to_numeric(selected_columns["Close"], errors='coerce')  # Convert prices to float
        full_range = pd.date_range(start=selected_columns["Timestamp"].min(), end=selected_columns["Timestamp"].max(), freq="T")
        selected_columns = selected_columns.set_index("Timestamp").reindex(full_range).reset_index()
        # Fill missing values with the average of neighboring values
        selected_columns["Close"] = selected_columns["Close"].interpolate(method='linear')
        selected_columns.to_csv(f"{vk.replace(' ','_')}.csv")




def apply_feature(data,feature,args):
    if feature=="Moving Average":
        return SMA(data,args['t_MA'])
    elif feature=="Exponential Moving Average":
        return EMA(data,args['t_EMA'])
    elif feature=="Moving Average Convergence Divergence":
        return MACD(data,args['t1'],args['t2'])
    elif feature=="Boll Bands":
        return BollBands(data,args['n'],args['k'])
    
def get_last_working_day(symbol="AAPL.O"):
    """Get the last available trading day using historical data."""
    today = datetime.today()
    # Fetch last 7 days of data
    data = rd.get_history(
        universe=[symbol],
        fields=["TRDPRC_1"],
        interval="1D",
        start=today - timedelta(days=7),
        end=today 
    )

    if data.empty:
        raise ValueError("No data returned. Check market availability or API credentials.")

    # Extract last available trading day
    # print(data)
    last_trading_day = data.index[-1].date()
    # print(last_trading_day)
    return last_trading_day

def get_closing_prices(stock_name, start_time, end_time, freq="1min", days=3, pad_with="ffill"):
    """
    Fetch closing prices for a given intraday range across the last N working days.
    Aligns all days to the same time index, so missing values are padded in place.

    Args:
        stock_name (str): Stock ticker (e.g., "AAPL" or "AAPL.O")
        start_time (str): "HH:MM"
        end_time (str): "HH:MM"
        freq (str): Frequency (default "1min")
        days (int): Number of past working days
        pad_with (str): How to pad missing values: "ffill", "bfill", "zero", "nan"

    Returns:
        torch.FloatTensor: Shape (days, sequence_len)
        pd.DatetimeIndex: The common timeline for all rows
    """
    if ".O" not in stock_name:
        stock_name = stock_name + ".O"

    rd.open_session(config_name="/home/kian/NO_NAME/DEMO/src/refinitiv-data.config.json")

    today = datetime.today().date()
    checked_days = 0
    offset = 0
    rows = []

    # Create the full reference timeline (e.g., 15:00 to 16:00 every minute)
    base_day = today
    start_dt = datetime.combine(base_day, datetime.strptime(start_time, "%H:%M").time())
    end_dt = datetime.combine(base_day, datetime.strptime(end_time, "%H:%M").time())
    full_index = pd.date_range(start=start_dt, end=end_dt, freq=freq)
    seq_len = len(full_index)

    while checked_days < days:
        day = today - timedelta(days=offset)
        offset += 1

        # Skip weekends
        if day.weekday() >= 5:
            continue

        try:
            start_day = datetime.combine(day, datetime.strptime(start_time, "%H:%M").time())
            end_day = datetime.combine(day, datetime.strptime(end_time, "%H:%M").time())
            print(start_day)
            stock_data = rd.get_history(
                stock_name,
                start=start_day,
                end=end_day,
                interval=freq,
                fields=["TRDPRC_1"]
            )

            if not stock_data.empty:
                prices = stock_data["TRDPRC_1"]
                prices.index = pd.to_datetime(prices.index)

                # Reindex to the full timeline (shifted to this day)
                ref_index = pd.date_range(start=start_day, end=end_day, freq=freq)
                aligned = prices.reindex(ref_index)

                # Pad missing values
                if pad_with == "ffill":
                    aligned = aligned.fillna(method="ffill").fillna(method="bfill")
                elif pad_with == "bfill":
                    aligned = aligned.fillna(method="bfill").fillna(method="ffill")
                elif pad_with == "zero":
                    aligned = aligned.fillna(0.0)
                else:  # "nan"
                    aligned = aligned

                rows.append(aligned.values)
                checked_days += 1

        except Exception as e:
            print(f"❌ Error fetching data for {stock_name} on {day}: {e}")
            continue

    rd.close_session()

    if not rows:
        print(f"⚠️ No data retrieved for {stock_name}")
        return None, None

    matrix = torch.FloatTensor(rows)  # shape: (days, seq_len)
    return matrix.flip(dims=[0])  # Return in chronological order
def backtest(stock_name, start_time, end_time, features=None, args=None, freq="1min"):
    """
    Backtest a stock's performance by fetching its closing prices and applying specified features.

    Parameters:
        stock_name (str): Stock ticker symbol (e.g., "AAPL.O").
        start_time (str): Start time in "HH:MM" format (e.g., "15:00").
        end_time (str): End time in "HH:MM" format (e.g., "17:00").
        features (list, optional): List of features to apply (default: None).
        args (dict, optional): Arguments for feature calculations (default: None).
        freq (str): Frequency of data ('1min', '5min', etc.).

    Returns:
        torch.Tensor: Processed tensor data with applied features.
    """

    data = torch.stack([get_closing_prices(stock_name, start_time, end_time, freq,i) for i in range(1,100)])
    if data is None:
        return None  # No data available
    data=replace_zeros_with_day_avg(data)
    if features:
        feature_tensors = []
        for f in features:
            feature_sequences = [apply_feature(seq, f, args) for seq in data]
            max_feature_len = max(len(fs) for fs in feature_sequences)  # Ensure consistent shape
            feature_tensor = torch.zeros((len(feature_sequences), max_feature_len))  # Padding
            for i, fs in enumerate(feature_sequences):
                feature_tensor[i, :len(fs)] = fs
            feature_tensors.append(feature_tensor.unsqueeze(2))  # Keep channel dimension

        feature_tensor = torch.cat(feature_tensors, dim=2)  # Stack features along the last axis
        # Concatenate Close price with extracted features
        final_tensor = torch.cat([feature_tensor, data.unsqueeze(2)], dim=-1)
    else:
        final_tensor = data.unsqueeze(2)  # Default to only 'Close' price

    return final_tensor


def today(stock_name, start_time, end_time,features=None,args=None,freq="1min",days=0):
    data=get_closing_prices(stock_name,start_time,end_time,freq,days=days).squeeze(1)

    if features:
        feature_tensors = []
        for f in features:
            feature_sequences = [apply_feature(seq, f, args) for seq in data]
            max_feature_len = max(len(fs) for fs in feature_sequences)  # Ensure consistent shape
            feature_tensor = torch.zeros((len(feature_sequences), max_feature_len))  # Padding
            for i, fs in enumerate(feature_sequences):
                feature_tensor[i, :len(fs)] = fs
            feature_tensors.append(feature_tensor.unsqueeze(2))  # Keep channel dimension

        feature_tensor = torch.cat(feature_tensors, dim=2)  # Stack features along the last axis
        # Concatenate Close price with extracted features
        final_tensor = torch.cat([feature_tensor, data.unsqueeze(2)], dim=-1)
    else:
        final_tensor = data.unsqueeze(2)  # Default to only 'Close' price

    return final_tensor


def load_train_test_data(folder_path,stock=None, pattern="_train.csv", start="09:00", end="10:00",trgt_start="17:00",trgt_end="18:00", freq="1min",days=1): 
    """
    Reads all stock CSVs in folder_path, filters times between start and end,
    aligns each day to the same timeline, and returns a combined DataFrame.

    Args:
        folder_path (str): Path where CSVs are stored
        pattern (str): File pattern to filter (default: '_train.csv')
        start (str): Start time (e.g., "09:00")
        end (str): End time (e.g., "10:00")
        freq (str): Frequency for alignment (default: "1min")

    Returns:
        pd.DataFrame: Combined and filtered DataFrame
    """
    if stock is not None:
        listdir=[f"{stock}{pattern}"]
    else:
        listdir=os.listdir(folder_path)

    src = []
    trgt=[]
    days_td=timedelta(days=days)
    for filename in listdir:
        if filename.endswith(pattern):
            ticker = filename.split("_")[0]
            filepath = os.path.join(folder_path, filename)

            df = pd.read_csv(filepath, parse_dates=[0], index_col=0)
            df = df.sort_index()
            df["Ticker"] = ticker

            # group by day
            all_dfs = []
            all_trgts = []
            for day, group in df.groupby(df.index.date):

                
               

                day_start = pd.to_datetime(f"{day} {start}")
                day_end = pd.to_datetime(f"{day} {end}")
                ref_index = pd.date_range(start=day_start, end=day_end, freq=freq)
                aligned = group.reindex(ref_index)
                target_start = pd.to_datetime(f"{day} {trgt_start}")
                target_end = pd.to_datetime(f"{day} {trgt_end}")

                
                trg_index = pd.date_range(start=target_start, end=target_end, freq=freq)

                # reindex and pad
                
                trg_aligned=group.reindex(trg_index)
                trg_aligned["Ticker"]=ticker

                
                trg_aligned=trg_aligned.ffill().bfill()

                if not trg_aligned.isna().any().any() and not aligned.isna().any().any():
                    all_dfs.append(aligned["TRDPRC_1"].ffill().bfill().values)
                    all_trgts.append(trg_aligned["TRDPRC_1"].values)

                    
            if len(all_dfs)<days:
                continue
            print(f"Loaded {len(all_dfs)} days for {ticker}")
            all_dfs = torch.FloatTensor(all_dfs).unfold(0,days,1).permute(0,2,1)
            all_trgts = torch.FloatTensor(all_trgts).unfold(0,days,1).permute(0,2,1)
            trgt.append(all_trgts[:,-1,:])
            src.append(all_dfs)
    if not src:
        print("⚠️ No files found.")
        return pd.DataFrame()

    
    return torch.cat(src,dim=0),torch.cat(trgt,dim=0)

def load_test(stock, frequency, period, features=None, args=None):
    """
    Load and preprocess stock data for a given frequency and period.
    
    Args:
        stock (str): Stock name.
        frequency (str): Frequency of data ('daily', 'hourly', 'minutes').
        period (dict): Dictionary with 'start' and 'end' keys.
        features (list, optional): List of features to extract (default: ['Close']).
        args (dict, optional): Arguments for feature calculations.

    Returns:
        torch.Tensor: Processed tensor data.
        int: Feature dimension.
        int: Sequence length.
    """

    start = pd.to_datetime(period["start"])
    end = pd.to_datetime(period["end"])

    # Define the file path
    stock_dir = os.path.join("Histories", "1min")
    stock_file = os.path.join(stock_dir, f"{stock}_US_Equity_backtest.csv")

    # Ensure the file exists
    if not os.path.exists(stock_file):
        raise FileNotFoundError(f"Stock data file not found: {stock_file}")

    # Load CSV file
    df = pd.read_csv(stock_file, parse_dates=["Timestamp"])
    df.rename(columns={"Timestamp": "index" , "TRDPRC_1": "Close"}, inplace=True)  # Rename column to 'index'
    sequences = []
    if frequency in ["1min", "5min","15min","1h"]:
        freq_map = {"1min": "1T", "5min": "5T", "15min": "15T", "1h": "1H"}
        period = freq_map[frequency]
        df["Date"] = df["index"].dt.date  # Extract date
        df["Time"] = df["index"].dt.strftime("%H:%M")  # Extract time
        # Process each day's sequence
        for date, group in df.groupby("Date"):

            filtered_group = group[(group["Time"] >= start.strftime("%H:%M")) & (group["Time"] <= end.strftime("%H:%M"))]
            if not filtered_group.empty:
                filtered_group.index=pd.to_datetime(filtered_group["index"])
                sequences.append(filtered_group["Close"].resample(period).mean().dropna().values)


    elif frequency in []:
        #TO DO
        pass
    # Convert sequences to tensor
    max_len = max(len(seq) for seq in sequences) if sequences else 0  # Find the longest sequence
    tensor_data = torch.zeros((len(sequences), max_len))  # Create a tensor with padding
    
    
    for i, seq in enumerate(sequences):
        tensor_data[i, :len(seq)] = torch.tensor(seq, dtype=torch.float32)  # Fill tensor with data

    tensor_data=replace_zeros_with_day_avg(tensor_data)
    # Apply features
    if features:
        feature_tensors = []
        for f in features:
            feature_sequences = [apply_feature(seq, f, args) for seq in tensor_data]
            max_feature_len = max(len(fs) for fs in feature_sequences)  # Ensure consistent shape
            feature_tensor = torch.zeros((len(feature_sequences), max_feature_len))  # Padding
            for i, fs in enumerate(feature_sequences):
                feature_tensor[i, :len(fs)] = fs
            feature_tensors.append(feature_tensor.unsqueeze(2))  # Keep channel dimension

        feature_tensor = torch.cat(feature_tensors, dim=2)  # Stack features along the last axis
        # Concatenate Close price with extracted features
        final_tensor = torch.cat([feature_tensor, tensor_data.unsqueeze(2)], dim=-1)
    else:
        final_tensor = tensor_data.unsqueeze(2)  # Default to only 'Close' price

    return final_tensor[1:-1],final_tensor.size(-1),final_tensor.size(-2)


def load_raw_data(stock):
    stock_dir = os.path.join("Histories", "1min")
    stock_file = os.path.join(stock_dir, f"{stock}_US_Equity.csv")
    # Ensure the file exists
    if not os.path.exists(stock_file):
        raise FileNotFoundError(f"Stock data file not found: {stock_file}")

    # Load CSV file
    df = pd.read_csv(stock_file, parse_dates=["Timestamp"])
    if("index" not in df.columns):
        df.rename(columns={"Timestamp": "index" , "TRDPRC_1": "Close"}, inplace=True)
    return torch.FloatTensor(df["Close"].values)

def load_data(stock, frequency, period, features=None, args=None):
    """
    Load and preprocess stock data for a given frequency and period.
    
    Args:
        stock (str): Stock name.
        frequency (str): Frequency of data ('daily', 'hourly', 'minutes').
        period (dict): Dictionary with 'start' and 'end' keys.
        features (list, optional): List of features to extract (default: ['Close']).
        args (dict, optional): Arguments for feature calculations.

    Returns:
        torch.Tensor: Processed tensor data.
        int: Feature dimension.
        int: Sequence length.
    """

    start = pd.to_datetime(period["start"])
    end = pd.to_datetime(period["end"])

    # Define the file path
    stock_dir = os.path.join("Histories", "1min")
    stock_file = os.path.join(stock_dir, f"{stock}_US_Equity.csv")

    # Ensure the file exists
    if not os.path.exists(stock_file):
        raise FileNotFoundError(f"Stock data file not found: {stock_file}")

    # Load CSV file
    df = pd.read_csv(stock_file, parse_dates=["Timestamp"])
    if("index" not in df.columns):
        df.rename(columns={"Timestamp": "index" , "TRDPRC_1": "Close"}, inplace=True) 
    df["index"] = pd.to_datetime(df["index"])  # Ensure 'index' is in datetime format
    sequences = []
    if frequency in ["1min", "5min","15min","1h","T"]:
        freq_map = {"1min": "min", "5min": "5T", "15min": "15T", "1h": "1H"}
        period = freq_map[frequency]
        df["Date"] = df["index"].dt.date  # Extract date
        df["Time"] = df["index"].dt.strftime("%H:%M")  # Extract time
        # Process each day's sequence
        for date, group in df.groupby("Date"):

            filtered_group = group[(group["Time"] >= start.strftime("%H:%M")) & (group["Time"] <= end.strftime("%H:%M"))]
            
            if not filtered_group.empty:
                filtered_group.index=pd.to_datetime(filtered_group["index"])
                sequences.append(filtered_group["Close"].resample(period).mean().dropna().values)


    elif frequency in []:
        #TO DO
        pass
    # Convert sequences to tensor
    max_len = max(len(seq) for seq in sequences) if sequences else 0  # Find the longest sequence
    for i in range(len(sequences)):
        seq=torch.FloatTensor(sequences[i])
        sequences[i]=F.interpolate(seq.unsqueeze(0).unsqueeze(0), size=max_len, mode='linear').squeeze(0).squeeze(0)  # Interpolate to max length
    tensor_data =  torch.stack(sequences)  # Stack sequences into a tensor

    # Apply features
    tensor_data=replace_zeros_with_day_avg(tensor_data)
    if features:
        # final_tensor=derivatives(tensor_data,5)
        feature_tensors = []
        for f in features:
            feature_sequences = [apply_feature(seq, f, args) for seq in tensor_data]
            max_feature_len = max(len(fs) for fs in feature_sequences)  # Ensure consistent shape
            feature_tensor = torch.zeros((len(feature_sequences), max_feature_len))  # Padding
            for i, fs in enumerate(feature_sequences):
                feature_tensor[i, :len(fs)] = fs
            feature_tensors.append(feature_tensor.unsqueeze(2))  # Keep channel dimension

        feature_tensor = torch.cat(feature_tensors, dim=2)  # Stack features along the last axis
        # Concatenate Close price with extracted features
        final_tensor = torch.cat([feature_tensor, tensor_data.unsqueeze(2)], dim=-1)
    else:
        final_tensor = tensor_data.unsqueeze(2)  # Default to only 'Close' price

    return final_tensor[1:-1],final_tensor.size(-1),final_tensor.size(-2)


def download_backtest_data(stock_name, start_time, end_time, frequency="1min",is_backtest=True):
    """
    Download historical stock data for backtesting.

    Parameters:
        stock_name (str): Stock ticker symbol (e.g., "AAPL.O").
        start_time (str): Start time in "HH:MM" format (e.g., "15:00").
        end_time (str): End time in "HH:MM" format (e.g., "17:00").
        frequency (str): Frequency of data ('1min', '5min', etc.).

    Returns:
        pd.DataFrame: DataFrame containing the stock's historical data.
    """
    if '.O' not in stock_name:
        stock_name=stock_name+".O"
    rd.open_session(config_name="/home/kian/NO_NAME/DEMO/src/refinitiv-data.config.json")

    try:
        start=start_time
        end=end_time

        # Fetch historical data
        stock_data = rd.get_history(
            stock_name,
            start=start,
            end=end,
            interval=frequency,
            fields=["TRDPRC_1"]
        )

        # Check if data is retrieved
        if stock_data.empty:
            print(f"⚠️ No data available for {stock_name} on {date}.")
            return None
        FOLDER_PATH = "/home/kian/NO_NAME/DEMO/Histories/1min"
        if is_backtest:
            FILE_PATH = os.path.join(FOLDER_PATH, f"{stock_name[:-2]}_US_Equity_backtest.csv")
        else:
            FILE_PATH = os.path.join(FOLDER_PATH, f"{stock_name[:-2]}_US_Equity.csv")
        stock_data.to_csv(FILE_PATH, index=True)
        print(stock_data)
        rd.close_session()
        return stock_data

    except Exception as e:
        print(f"❌ Error fetching data for {stock_name}: {e}")
        rd.close_session()
        return None
def chunk(tensor,k):
    m=tensor.size(0)
    tensor=tensor[:m-(m%k)]
    return tensor.view(-1,k)

def load_chunk(stock,chunckSize):
    stock_dir = os.path.join("Histories", "1min")
    stock_file = os.path.join(stock_dir, f"{stock}_US_Equity.csv")
    if not os.path.exists(stock_file):
        raise FileNotFoundError(f"Stock data file not found: {stock_file}")
    df = pd.read_csv(stock_file, parse_dates=["index"])
    df["Date"] = df["index"].dt.date  # Extract date
    df["Time"] = df["index"].dt.strftime("%H:%M")  # Extract time
    # Load CSV file
    data=list()
    for date, group in df.groupby("Date"):
        data.append(chunk(torch.FloatTensor(group['Close'].values),chunckSize))
    data=torch.cat(data,dim=0)
    return data

def load_concat_split_shuffle(folder_path, chunk_size, close_col='TRDPRC_1'):
    """
    Load closing prices from CSV files in folder_path, concatenate, split into chunks, shuffle chunks.
    
    Args:
        folder_path (str): Path to folder containing CSV files.
        chunk_size (int): Number of closing price points per chunk.
        close_col (str): Name of the closing price column in CSV files.
        
    Returns:
        torch.Tensor: Shuffled tensor of shape (num_chunks, chunk_size)
    """
    all_prices = []
    
    # Load closing prices from all CSV files in folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.csv'):
            file_path = os.path.join(folder_path, filename)
            df = pd.read_csv(file_path)
            if close_col in df.columns:
                prices = df[close_col].dropna().values
                all_prices.append(torch.tensor(prices, dtype=torch.float32))
            else:
                print(f"Warning: {filename} missing '{close_col}' column, skipping.")
    
    if not all_prices:
        raise ValueError("No closing price data found.")
    
    # Concatenate all closing prices into one long tensor
    long_tensor = torch.cat(all_prices)
    
    # Trim tensor to multiple of chunk_size
    n_chunks = len(long_tensor) // chunk_size
    trimmed_tensor = long_tensor[:n_chunks * chunk_size]
    
    # Split into chunks (shape: n_chunks x chunk_size)
    chunks = trimmed_tensor.view(n_chunks, chunk_size)
    
    # Shuffle the chunks
    shuffled_indices = torch.randperm(n_chunks)
    shuffled_chunks = chunks[shuffled_indices]
    
    return shuffled_chunks

def load_greenium_data(period,lag=5):
    dir = os.path.join("Histories","Greenium.csv")
    df=pd.read_csv(dir,parse_dates=["Date"])
    greenium=torch.FloatTensor(df["Spread"].values)
    trgt=greenium[period+lag-1:]-greenium[period-1:-lag]
    trgt=(trgt-trgt.mean())/(trgt.std()+1e-4)

    greenium=(greenium-greenium.mean())/(greenium.std()+1e-4)

    indices=torch.FloatTensor(df[df.columns.difference(["Date","Spread"])].values)
    print(df.columns.difference(["Date","Spread"]))

    indices=(indices-indices.mean(dim=0))/(indices.std(dim=0)+1e-4)

    src=greenium.unfold(0,period,1)[:-lag].unsqueeze(1)


    indices=indices.unfold(0,period,1).permute(1,0,2).unsqueeze(2)

    perm=torch.randperm(src.size(0))
    src=src[perm]
    indices=indices[:,perm]
    trgt=trgt[perm]
    return src[:-100],indices[:,:-100],trgt[:-100],src[-100:],indices[:,-100:],trgt[-100:]

def test():
    load_greenium_data(10)
if __name__=="__main__":
    test()