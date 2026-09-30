from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count
import time
import json
import matplotlib.pyplot as plt

PARQUET_PATH = "/home/cs179g/project/CS179G/clean_chicago_crime"
RESULTS_FILE = "experiment_results.json"

def run_experiment(num_workers, data_fraction, experiment_name):
    """
    Run analysis with specified number of workers and data fraction
    """
    print(f"\n{'='*60}")
    print(f"Experiment: {experiment_name}")
    print(f"Workers: {num_workers}, Data Fraction: {data_fraction}")
    print(f"{'='*60}\n")
    
    start_time = time.time()
    
    spark = SparkSession.builder \
        .appName(f"Experiment_{experiment_name}") \
        .config("spark.executor.instances", str(num_workers)) \
        .config("spark.executor.cores", "2") \
        .config("spark.executor.memory", "2g") \
        .getOrCreate()
    
        df = spark.read.parquet(PARQUET_PATH)
    
    if data_fraction < 1.0:
        df = df.sample(fraction=data_fraction, seed=42)
    
    df.cache()
    record_count = df.count() 
    
    print(f"Processing {record_count:,} records...")
    
    analysis_start = time.time()
    
    result1 = df.groupBy("primary_type").agg(count("*").alias("total"))
    result1.count()  
    
    result2 = df.filter(col("location_description").isNotNull()) \
        .groupBy("location_description", "primary_type") \
        .agg(count("*").alias("total"))
    result2.count()  
    
    analysis_time = time.time() - analysis_start
    total_time = time.time() - start_time
    
    spark.stop()
    
    result = {
        "experiment_name": experiment_name,
        "num_workers": num_workers,
        "data_fraction": data_fraction,
        "record_count": record_count,
        "analysis_time": analysis_time,
        "total_time": total_time
    }
    
    print(f"\nResults: Analysis time = {analysis_time:.2f}s, Total time = {total_time:.2f}s")
    
    return result


def save_results(results):
    """Save results to JSON file"""
    with open(RESULTS_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_FILE}")


def plot_results(results):
    """Generate execution time graphs"""
    
    print("\n=== DEBUG: Worker Experiments (100% data) ===")
    all_worker_experiments = [r for r in results if r['data_fraction'] == 1.0]
    print(f"Total experiments found: {len(all_worker_experiments)}")
    
    seen_workers = set()
    worker_experiments = []
    for r in sorted(all_worker_experiments, key=lambda x: x['num_workers']):
        if r['num_workers'] not in seen_workers:
            worker_experiments.append(r)
            seen_workers.add(r['num_workers'])
    
    if worker_experiments:
        worker_experiments = sorted(worker_experiments, key=lambda x: x['num_workers'])
        
        workers = [r['num_workers'] for r in worker_experiments]
        times = [r['analysis_time'] for r in worker_experiments]
        
        print(f"After removing duplicates: {len(worker_experiments)}")
        print("=== Order being plotted (workers) ===")
        for i, (w, t) in enumerate(zip(workers, times)):
            print(f"  Point {i}: Workers={w}, Time={t:.2f}s")
        
        plt.figure(figsize=(10, 6))
        plt.plot(workers, times, marker='o', linewidth=2, markersize=8)
        plt.xlabel('Number of Workers', fontsize=12)
        plt.ylabel('Execution Time (seconds)', fontsize=12)
        plt.title('Execution Time vs Number of Spark Workers (100% Data)', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.savefig('workers_vs_time.png', dpi=300, bbox_inches='tight')
        print("Saved: workers_vs_time.png")
        plt.close()
    
    worker_counts = sorted(set(r['num_workers'] for r in results))
    
    for num_workers in worker_counts:
        print(f"\n=== DEBUG: Data Size Experiments ({num_workers} workers) ===")
        all_data_experiments = [r for r in results if r['num_workers'] == num_workers]
        print(f"Total experiments found: {len(all_data_experiments)}")
        
        seen_fractions = set()
        data_experiments = []
        for r in sorted(all_data_experiments, key=lambda x: x['data_fraction']):
            if r['data_fraction'] not in seen_fractions:
                data_experiments.append(r)
                seen_fractions.add(r['data_fraction'])
        
        if len(data_experiments) > 1: 
            data_experiments = sorted(data_experiments, key=lambda x: x['data_fraction'])
            
            fractions = [r['data_fraction'] for r in data_experiments]
            times = [r['analysis_time'] for r in data_experiments]
            records = [r['record_count'] for r in data_experiments]
            
            print(f"After removing duplicates: {len(data_experiments)}")
            print(f"=== Order being plotted (data size, {num_workers} workers) ===")
            for i, (f, t, rec) in enumerate(zip(fractions, times, records)):
                print(f"  Point {i}: Fraction={f}, Time={t:.2f}s, Records={rec:,}")
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            ax1.plot(fractions, times, marker='s', linewidth=2, markersize=8, color='green')
            ax1.set_xlabel('Data Fraction', fontsize=12)
            ax1.set_ylabel('Execution Time (seconds)', fontsize=12)
            ax1.set_title(f'Execution Time vs Data Size ({num_workers} Workers)', fontsize=14)
            ax1.grid(True, alpha=0.3)
            
            sorted_indices = sorted(range(len(records)), key=lambda i: records[i])
            sorted_records = [records[i] for i in sorted_indices]
            sorted_times_by_records = [times[i] for i in sorted_indices]
            
            ax2.plot(sorted_records, sorted_times_by_records, marker='s', linewidth=2, markersize=8, color='orange')
            ax2.set_xlabel('Number of Records', fontsize=12)
            ax2.set_ylabel('Execution Time (seconds)', fontsize=12)
            ax2.set_title(f'Execution Time vs Record Count ({num_workers} Workers)', fontsize=14)
            ax2.grid(True, alpha=0.3)
            ax2.ticklabel_format(style='plain', axis='x')
            
            plt.tight_layout()
            filename = f'datasize_vs_time_{num_workers}workers.png'
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            print(f"Saved: {filename}")
            plt.close()
    
    print("\n=== Creating combined comparison graph ===")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    colors = ['blue', 'green', 'orange', 'red']
    markers = ['o', 's', '^', 'D']
    
    for idx, num_workers in enumerate(worker_counts):
        all_data_experiments = [r for r in results if r['num_workers'] == num_workers]
        
        seen_fractions = set()
        data_experiments = []
        for r in sorted(all_data_experiments, key=lambda x: x['data_fraction']):
            if r['data_fraction'] not in seen_fractions:
                data_experiments.append(r)
                seen_fractions.add(r['data_fraction'])
        
        if len(data_experiments) > 1:
            data_experiments = sorted(data_experiments, key=lambda x: x['data_fraction'])
            
            fractions = [r['data_fraction'] for r in data_experiments]
            times = [r['analysis_time'] for r in data_experiments]
            records = [r['record_count'] for r in data_experiments]
            
            ax1.plot(fractions, times, 
                    marker=markers[idx % len(markers)], 
                    linewidth=2, 
                    markersize=8,
                    color=colors[idx % len(colors)],
                    label=f'{num_workers} worker(s)')
            
            sorted_indices = sorted(range(len(records)), key=lambda i: records[i])
            sorted_records = [records[i] for i in sorted_indices]
            sorted_times_by_records = [times[i] for i in sorted_indices]
            
            ax2.plot(sorted_records, sorted_times_by_records,
                    marker=markers[idx % len(markers)],
                    linewidth=2,
                    markersize=8,
                    color=colors[idx % len(colors)],
                    label=f'{num_workers} worker(s)')
    
    ax1.set_xlabel('Data Fraction', fontsize=12)
    ax1.set_ylabel('Execution Time (seconds)', fontsize=12)
    ax1.set_title('Execution Time vs Data Size (All Worker Configurations)', fontsize=14)
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    ax2.set_xlabel('Number of Records', fontsize=12)
    ax2.set_ylabel('Execution Time (seconds)', fontsize=12)
    ax2.set_title('Execution Time vs Record Count (All Worker Configurations)', fontsize=14)
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    ax2.ticklabel_format(style='plain', axis='x')
    
    plt.tight_layout()
    plt.savefig('datasize_vs_time_comparison.png', dpi=300, bbox_inches='tight')
    print("Saved: datasize_vs_time_comparison.png")
    plt.close()
    
    print("\n=== Plotting Summary ===")
    print(f"Total graphs generated:")
    print(f"  - workers_vs_time.png")
    for num_workers in worker_counts:
        all_data = [r for r in results if r['num_workers'] == num_workers]
        if len(set(r['data_fraction'] for r in all_data)) > 1:
            print(f"  - datasize_vs_time_{num_workers}workers.png")
    print(f"  - datasize_vs_time_comparison.png")


def main():
    results = []
    
    print("\n" + "="*60)
    print("RUNNING ALL EXPERIMENTS")
    print("="*60)
    
    for num_workers in [1, 2, 4, 8]:
        print(f"\n--- Testing with {num_workers} workers ---")
        for data_fraction in [0.1, 0.25, 0.5, 0.75, 1.0]:
            result = run_experiment(
                num_workers=num_workers,
                data_fraction=data_fraction,
                experiment_name=f"workers_{num_workers}_data_{int(data_fraction*100)}"
            )
            results.append(result)
    
    save_results(results)
    plot_results(results)
    
    print("\n" + "="*60)
    print("All experiments completed!")
    print("="*60)


if __name__ == "__main__":
    main()