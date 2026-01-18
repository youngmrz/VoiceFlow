"""
Baseline resource measurement script for VoiceFlow.

Measures CPU and memory usage over a specified duration to establish
baseline idle resource usage. Target: <1% CPU and <100MB memory when idle.

Usage:
    uv run python scripts/measure_idle_resources.py --duration 10
"""
import argparse
import time
import sys

try:
    import psutil
except ImportError:
    print("Error: psutil is required. Install with: pip install psutil")
    sys.exit(1)


def measure_baseline(duration: int = 10) -> dict:
    """
    Measure baseline resource usage over a duration.

    Args:
        duration: Measurement duration in seconds

    Returns:
        Dictionary with baseline measurements:
        - avg_cpu: Average CPU usage percentage
        - max_cpu: Maximum CPU usage percentage
        - avg_memory_mb: Average memory usage in MB
        - max_memory_mb: Maximum memory usage in MB
        - samples: Number of samples taken
    """
    process = psutil.Process()

    # Initialize CPU measurement (first call returns 0)
    process.cpu_percent(interval=0.1)

    print(f"Measuring baseline resource usage for {duration} seconds...")
    print("Please keep the application idle during measurement.")
    print()

    samples = []
    interval = 1.0  # Sample every 1 second
    num_samples = duration

    for i in range(num_samples):
        # Get measurements
        cpu = process.cpu_percent(interval=interval)
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)

        sample = {
            'cpu': cpu,
            'memory_mb': memory_mb,
            'timestamp': time.time()
        }
        samples.append(sample)

        # Show progress
        print(f"Sample {i+1}/{num_samples}: CPU={cpu:.2f}%, Memory={memory_mb:.2f}MB")

    # Calculate statistics
    avg_cpu = sum(s['cpu'] for s in samples) / len(samples)
    max_cpu = max(s['cpu'] for s in samples)
    avg_memory_mb = sum(s['memory_mb'] for s in samples) / len(samples)
    max_memory_mb = max(s['memory_mb'] for s in samples)

    baseline = {
        'avg_cpu': avg_cpu,
        'max_cpu': max_cpu,
        'avg_memory_mb': avg_memory_mb,
        'max_memory_mb': max_memory_mb,
        'samples': len(samples),
        'duration': duration
    }

    return baseline


def print_baseline_report(baseline: dict):
    """
    Print formatted baseline report.

    Args:
        baseline: Baseline measurements dictionary
    """
    print()
    print("=" * 60)
    print("BASELINE RESOURCE USAGE REPORT")
    print("=" * 60)
    print()
    print(f"Measurement Duration: {baseline['duration']} seconds")
    print(f"Samples Collected: {baseline['samples']}")
    print()
    print("CPU Usage:")
    print(f"  Average: {baseline['avg_cpu']:.2f}%")
    print(f"  Maximum: {baseline['max_cpu']:.2f}%")
    print()
    print("Memory Usage:")
    print(f"  Average: {baseline['avg_memory_mb']:.2f} MB")
    print(f"  Maximum: {baseline['max_memory_mb']:.2f} MB")
    print()
    print("Target Goals:")
    print(f"  CPU: <1% (Current avg: {baseline['avg_cpu']:.2f}%)")
    cpu_status = "✓ PASS" if baseline['avg_cpu'] < 1.0 else "✗ FAIL"
    print(f"  Status: {cpu_status}")
    print()
    print(f"  Memory: <100MB (Current avg: {baseline['avg_memory_mb']:.2f}MB)")
    memory_status = "✓ PASS" if baseline['avg_memory_mb'] < 100.0 else "✗ FAIL"
    print(f"  Status: {memory_status}")
    print()
    print("=" * 60)


def main():
    """Main entry point for baseline measurement script."""
    parser = argparse.ArgumentParser(
        description="Measure baseline idle resource usage for VoiceFlow"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=10,
        help="Measurement duration in seconds (default: 10)"
    )

    args = parser.parse_args()

    if args.duration < 1:
        print("Error: Duration must be at least 1 second")
        sys.exit(1)

    try:
        baseline = measure_baseline(duration=args.duration)
        print_baseline_report(baseline)

        # Exit with code 0 if both targets are met, 1 otherwise
        if baseline['avg_cpu'] < 1.0 and baseline['avg_memory_mb'] < 100.0:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nMeasurement interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during measurement: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
