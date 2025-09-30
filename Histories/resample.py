import os
import pandas as pd
import sys
def resample_to_5min(directory,n,dest):
    """
    Goes through all CSV files in the given directory, resamples 1-minute frequency stock data to 5-minute frequency,
    and saves the new files with "_5min" appended to the filename.
    """
    for filename in os.listdir(directory):
        if filename.endswith(".csv"):  # Process only CSV files
            filepath = os.path.join(directory, filename)
            
            # Load data
            df = pd.read_csv(filepath, parse_dates=['Time'], index_col='Time')
            
            # Ensure the data is sorted by time
            df = df.sort_index()
            
            # Resample to 5-minute frequency using mean aggregation
            df_resampled = df.resample(f'{n}T').mean()
            
            # Save the new resampled file
            new_filename = filename.replace(".csv", f"_{n}min.csv")
            df_resampled.to_csv(os.path.join(dest, new_filename))
            print(f"Processed: {filename} -> {new_filename}")

# Example usage

def main():
    directory = sys.argv[1]  # Change this to your actual directory path
    resample_to_5min(directory,sys.argv[2],sys.argv[3])
if __name__=='__main__':
    main()