#!/usr/bin/env python3
"""
CPU Scheduling Simulator for CampusConnect.

Algorithms:
- FCFS (First Come First Serve)
- SJF (Shortest Job First, non-preemptive)
- Round Robin (with configurable time quantum)

Input:
- A list of processes, each with:
  - arrival_time
  - burst_time
  - process_id (optional; if not provided, generated as P1, P2, ...)

Tie-breaking and ordering rules (stated here for README):
- General:
  - If two or more processes share the same arrival time, order them by
    their definition order in the input list (process ID / index) as the tiebreak.
- SJF:
  - If two processes have equal burst time, break the tie using:
    1) arrival time (earlier first),
    2) then process ID / definition order.
- Round Robin:
  - When a process is preempted at the end of its quantum, enqueue any
    processes that arrived during that quantum BEFORE re-enqueuing the
    just-preempted process at the back of the ready queue.

The simulator prints:
- Per-process waiting time and turnaround time.
- Average waiting time and average turnaround time.
"""

from dataclasses import dataclass
from typing import List, Optional
import sys


@dataclass
class Process:
    pid: str
    arrival_time: int
    burst_time: int


def parse_processes(processes: List[tuple]) -> List[Process]:
    """
    Convert a list of (arrival_time, burst_time, pid?) tuples into Process objects.
    If pid is not provided, generate as P1, P2, ...
    """
    result = []
    for i, item in enumerate(processes):
        if len(item) == 2:
            arrival, burst = item
            pid = f"P{i+1}"
        elif len(item) == 3:
            arrival, burst, pid = item
        else:
            raise ValueError("Each process must be (arrival, burst) or (arrival, burst, pid).")
        result.append(Process(pid=pid, arrival_time=arrival, burst_time=burst))
    return result


def fcfs_schedule(processes: List[Process]) -> List[dict]:
    """
    Simulate FCFS scheduling.
    Returns a list of dicts with per-process stats.
    """
    # Sort by arrival_time, then by definition order (pid)
    sorted_procs = sorted(processes, key=lambda p: (p.arrival_time, p.pid))

    current_time = 0
    stats = []

    for p in sorted_procs:
        if current_time < p.arrival_time:
            current_time = p.arrival_time

        start_time = current_time
        finish_time = start_time + p.burst_time

        turnaround_time = finish_time - p.arrival_time
        waiting_time = turnaround_time - p.burst_time

        stats.append({
            "pid": p.pid,
            "arrival": p.arrival_time,
            "burst": p.burst_time,
            "start": start_time,
            "finish": finish_time,
            "turnaround": turnaround_time,
            "waiting": waiting_time
        })

        current_time = finish_time

    return stats


def sjf_schedule(processes: List[Process]) -> List[dict]:
    """
    Simulate non-preemptive SJF scheduling.
    Tie-breaking:
      - If burst times are equal, break by arrival_time, then by pid.
    """
    # We'll simulate over time, picking the shortest job from available processes.
    # Sort initially by arrival_time, then by pid for tie-breaking at same arrival.
    remaining = list(processes)
    completed = []

    current_time = 0

    while remaining:
        # Find all processes that have arrived by current_time
        available = [p for p in remaining if p.arrival_time <= current_time]

        if not available:
            # Advance time to next arrival
            next_arrival = min(p.arrival_time for p in remaining)
            current_time = next_arrival
            continue

        # Choose the shortest job:
        # Sort by burst_time, then arrival_time, then pid
        available.sort(key=lambda p: (p.burst_time, p.arrival_time, p.pid))
        chosen = available[0]

        start_time = current_time
        finish_time = start_time + chosen.burst_time

        turnaround_time = finish_time - chosen.arrival_time
        waiting_time = turnaround_time - chosen.burst_time

        completed.append({
            "pid": chosen.pid,
            "arrival": chosen.arrival_time,
            "burst": chosen.burst_time,
            "start": start_time,
            "finish": finish_time,
            "turnaround": turnaround_time,
            "waiting": waiting_time
        })

        remaining.remove(chosen)
        current_time = finish_time

    return completed


def rr_schedule(processes: List[Process], quantum: int) -> List[dict]:
    """
    Simulate Round Robin scheduling with a given time quantum.

    Tie-breaking / ordering rules:
      - Ready queue is ordered by arrival time, then by pid.
      - When a process is preempted at the end of its quantum, enqueue any
        processes that arrived during that quantum BEFORE re-enqueuing the
        just-preempted process at the back.
    """
    # Sort initially by arrival_time, then by pid
    remaining = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    completed = []

    # Track remaining burst for each process
    remaining_burst = {p.pid: p.burst_time for p in remaining}
    arrival_map = {p.pid: p.arrival_time for p in remaining}
    burst_map = {p.pid: p.burst_time for p in remaining}

    ready_queue: List[str] = []

    current_time = 0

    # Initially, add all processes that arrive at time 0
    for p in remaining:
        if p.arrival_time == 0:
            ready_queue.append(p.pid)

    # To track start and finish times
    start_time_map: dict[str, int] = {}
    finish_time_map: dict[str, int] = {}

    last_arrival_time = max(p.arrival_time for p in remaining)

    while remaining_burst:
        # If ready queue is empty but there are still processes, advance time
        if not ready_queue:
            # Find next arrival
            next_arrivals = [p for p in remaining if remaining_burst[p.pid] > 0 and p.arrival_time > current_time]
            if not next_arrivals:
                break
            next_time = min(p.arrival_time for p in next_arrivals)
            current_time = next_time
            # Add all processes arriving at this time
            for p in remaining:
                if p.arrival_time == current_time and remaining_burst[p.pid] > 0:
                    ready_queue.append(p.pid)
            continue

        # Run the process at the front of the queue
        pid = ready_queue.pop(0)

        if remaining_burst[pid] == burst_map[pid]:
            # First time running this process -> record start time
            start_time_map[pid] = current_time

        # Determine how much to run
        run_time = min(quantum, remaining_burst[pid])
        end_time = current_time + run_time

        #这期间到达的新进程
        arrived_during_quantum = [
            p.pid for p in remaining
            if p.arrival_time > current_time and p.arrival_time <= end_time and remaining_burst[p.pid] > 0
        ]

        # Update remaining burst
        remaining_burst[pid] -= run_time
        current_time = end_time

        # If process completed
        if remaining_burst[pid] == 0:
            finish_time_map[pid] = current_time
            completed.append(pid)
        else:
            # Process is preempted:
            # Rule: enqueue any processes that arrived during this quantum BEFORE re-enqueuing this process.
            # First, add new arrivals (in arrival order, then pid)
            new_arrivals = sorted(
                [p for p in remaining if p.pid in arrived_during_quantum and remaining_burst[p.pid] > 0],
                key=lambda p: (p.arrival_time, p.pid)
            )
            for p in new_arrivals:
                ready_queue.append(p.pid)

            # Then re-enqueue the preempted process
            ready_queue.append(pid)

    # Compute stats
    stats = []
    for pid in completed:
        arrival = arrival_map[pid]
        burst = burst_map[pid]
        start = start_time_map[pid]
        finish = finish_time_map[pid]
        turnaround = finish - arrival
        waiting = turnaround - burst
        stats.append({
            "pid": pid,
            "arrival": arrival,
            "burst": burst,
            "start": start,
            "finish": finish,
            "turnaround": turnaround,
            "waiting": waiting
        })

    # Ensure stats are in PID order for consistent output
    stats.sort(key=lambda s: s["pid"])
    return stats


def print_stats(stats: List[dict], algorithm: str) -> None:
    """Print per-process and average waiting/turnaround times."""
    print(f"\n=== {algorithm} ===")
    print(f"PID\tArrival\tBurst\tStart\tFinish\tTurnaround\tWaiting")
    total_turnaround = 0
    total_waiting = 0

    for s in stats:
        print(f"{s['pid']}\t{s['arrival']}\t{s['burst']}\t{s['start']}\t{s['finish']}\t{s['turnaround']}\t{s['waiting']}")
        total_turnaround += s["turnaround"]
        total_waiting += s["waiting"]

    n = len(stats)
    avg_turnaround = total_turnaround / n
    avg_waiting = total_waiting / n

    print(f"\nAverage Turnaround Time: {avg_turnaround:.2f}")
    print(f"Average Waiting Time: {avg_waiting:.2f}")


def main() -> None:
    """
    Run the simulator on a dataset of at least 5 processes.

    Example dataset:
      P1: arrival=0, burst=5
      P2: arrival=1, burst=3
      P3: arrival=2, burst=8
      P4: arrival=3, burst=6
      P5: arrival=4, burst=2
    """

    # Define dataset (arrival, burst, pid)
    processes_input = [
        (0, 5, "P1"),
        (1, 3, "P2"),
        (2, 8, "P3"),
        (3, 6, "P4"),
        (4, 2, "P5"),
    ]

    processes = parse_processes(processes_input)

    # FCFS
    fcfs_stats = fcfs_schedule(processes)
    print_stats(fcfs_stats, "FCFS")

    # SJF
    sjf_stats = sjf_schedule(processes)
    print_stats(sjf_stats, "SJF (non-preemptive)")

    # Round Robin with configurable quantum
    # Default quantum = 2; can be overridden via command line
    quantum = 2
    if len(sys.argv) > 1:
        quantum = int(sys.argv[1])

    rr_stats = rr_schedule(processes, quantum)
    print_stats(rr_stats, f"Round Robin (quantum={quantum})")


if __name__ == "__main__":
    main()
