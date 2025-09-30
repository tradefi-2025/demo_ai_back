import multiprocessing
import sys
from worker import main as ma

def main():
    # Ensure command-line arguments are passed
    if len(sys.argv) < 2:
        print("Usage: python script.py <number_of_workers>")
        return
    
    try:
        nb_worker = int(sys.argv[1])
    except ValueError:
        print("Error: The number of workers must be an integer.")
        return

    # Create and start the processes
    global processes 
    processes = [multiprocessing.Process(target=ma,args=[_]) for _ in range(nb_worker)]
    try:
        for p in processes:
            p.start()
        
        print(f"{nb_worker} servers have been launched.")

        # Wait for all processes to complete
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        for p in processes:
            print("killing process",p)
            p.kill()

if __name__ == "__main__":
    main()
