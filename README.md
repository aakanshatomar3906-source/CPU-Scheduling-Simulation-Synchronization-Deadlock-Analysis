# CPU-Scheduling-Simulation-Synchronization-Deadlock-Analysis

# CampusConnect CPU Scheduling Simulation, Synchronization & Deadlock Analysis

This repository contains:

- `scheduler.py` – CPU scheduling simulator for FCFS, SJF (non-preemptive), and Round Robin.
- `sync_demo.py` – Synchronization demo with:
  - Unsynchronized version using `threading.Barrier` to force a deterministic lost increment.
  - Synchronized version using a lock (binary semaphore) to ensure correct counting.
- `README.md` – This file, containing:
  - Tie-breaking and ordering rules.
  - Example dataset and results.
  - Priority scheduling with aging trace.
  - Deadlock analysis.

---

## Tie-Breaking and Ordering Rules (Scheduling Simulator)

These rules are applied consistently across all three algorithms:

- **General tie-breaking:**
  - If two or more processes share the same arrival time, order them by their definition order in the input list (process ID) as the tiebreak.

- **SJF (non-preemptive):**
  - If two processes have equal burst time, break the tie using:
    1) arrival time (earlier first),
    2) then process ID / definition order.

- **Round Robin:**
  - When a process is preempted at the end of its quantum, enqueue any processes that arrived during that quantum **before** re-enqueuing the just-preempted process at the back of the ready queue.

These deterministic rules ensure reproducible output for the same input.

---

## Example Dataset and Results

### Dataset (5 processes)

| PID | Arrival Time | Burst Time |
|-----|--------------|------------|
| P1  | 0            | 5          |
| P2  | 1            | 3          |
| P3  | 2            | 8          |
| P4  | 3            | 6          |
| P5  | 4            | 2          |

Run the simulator:

```bash
python3 scheduler.py
# or with custom quantum:
python3 scheduler.py 3
```

The output will show per-process and average waiting/turnaround times for:

- FCFS
- SJF (non-preemptive)
- Round Robin (with default quantum=2 or custom quantum)

---

## Priority Scheduling with Aging

### Assumptions and Convention

- **Priority convention:** Higher numeric priority value = higher scheduling priority.
- We use a **priority scheduling** model where the scheduler always picks the process with the highest numeric priority among those that have arrived.
- To demonstrate **starvation**, we assume that new high-priority processes continue arriving at fixed intervals for the duration of the simulated trace window. Without aging, a low-priority process would never be scheduled within that window.
- **Aging:** After a fixed wait interval, the priority of a waiting process is incremented (numerically raised) to gradually increase its chance of being scheduled.

### Dataset (5 processes)

We assign priorities as follows (higher number = higher priority):

| PID | Arrival Time | Burst Time | Initial Priority |
|-----|--------------|------------|------------------|
| P1  | 0            | 10         | 1                |
| P2  | 2            | 5          | 5                |
| P3  | 4            | 5          | 5                |
| P4  | 6            | 5          | 5                |
| P5  | 8            | 5          | 5                |

**Starvation scenario:**

- P1 is the only low-priority process (priority = 1).
- From time 2 onward, new high-priority processes (P2, P3, P4, P5) arrive at fixed intervals (every 2 time units).
- Without aging, the scheduler will always prefer the highest-priority arrived process (priority 5) over P1 (priority 1).
- As long as high-priority processes keep arriving and have remaining burst, P1 will be indefinitely delayed within the trace window — this is **starvation**.

### Aging Policy

- **Aging interval:** 2 time units.
- Every 2 time units that a process remains in the ready queue without being scheduled, its priority is increased by 1.

### Priority Values Over Time (Text Table)

We simulate a simplified trace window from time 0 to 14, showing P1’s priority and the set of arrived high-priority processes.

| Time | Processes in Ready Queue (arrived & not completed) | P1 Priority | Decision (which process runs) |
|------|----------------------------------------------------|-------------|------------------------------|
| 0    | P1                                                 | 1           | P1 runs (only one)           |
| 2    | P1 (partially run), P2                             | 1 → 2       | P2 runs (higher priority)    |
| 4    | P1, P2 (partially run), P3                         | 2 → 3       | P3 runs (higher priority)    |
| 6    | P1, P2, P3, P4                                     | 3 → 4       | P4 runs (higher priority)    |
| 8    | P1, P2, P3, P4, P5                                 | 4 → 5       | P5 runs (now equal to P1)    |
| 10   | P1, P2, P3, P4, P5                               | 5 → 5       | Tie: P1 runs (earlier arrival)|

**Explanation:**

- At time 0, only P1 is present, so it runs.
- From time 2 to 8, new high-priority processes (P2–P5) keep arriving, and P1’s priority is incremented every 2 time units (1→2→3→4→5).
- By time 8, P1’s priority reaches 5, equal to the others.
- At time 10, with equal priorities, the scheduler can break ties by arrival time, allowing P1 to run.
- Without aging, P1 would remain at priority 1 and be continuously preempted by arriving priority-5 processes, never getting to run within this window.

This trace demonstrates how **aging prevents starvation** by gradually raising the priority of the long-waiting low-priority process.

---

## Synchronization Demo

### Unsynchronized Version (with Barrier)

- Two threads increment a shared counter `iterations` times each (e.g., 100,000).
- Each thread:
  1. Reads the current counter value into a local variable.
  2. Waits at a `threading.Barrier(2)`.
  3. After both threads have read, writes back `local + 1`.
- Because both threads read the same stale value, they both compute the same new value, and exactly one increment is lost.
- The final counter will be `2 * iterations - 1` (or less, depending on timing), which is **incorrect**.

Run:

```bash
python3 sync_demo.py
```

Observe that the “Unsynchronized Version” prints an incorrect counter value.

### Synchronized Version (with Lock)

- The same two threads use a `threading.Lock` to protect the entire read-modify-write:
  ```python
  with counter_lock:
      local = counter
      counter = local + 1
  ```
- This makes the increment atomic; no two threads can interfere.
- The final counter is exactly `2 * iterations`, which is **correct**.

The “Synchronized Version” in the output will show the correct count.

---

## Deadlock Analysis

### Scenario: 3 Processes and 3 Resources

Consider CampusConnect’s backend with:

- Processes:
  - P1: reports generator
  - P2: enrollment updater
  - P3: cache manager
- Resources:
  - R1: database connection
  - R2: file lock (for nightly report file)
  - R3: cache lock

#### Resource Allocation and Requests

- P1:
  - Holds R1 (database connection).
  - Requests R2 (file lock).
- P2:
  - Holds R2 (file lock).
  - Requests R3 (cache lock).
- P3:
  - Holds R3 (cache lock).
  - Requests R1 (database connection).

#### Four Necessary Conditions for Deadlock

1. **Mutual Exclusion**  
   - Each resource (R1, R2, R3) can be held by only one process at a time; for example, only one process can hold the database connection R1.

2. **Hold-and-Wait**  
   - Each process holds at least one resource while waiting for another:  
     - P1 holds R1 and waits for R2.  
     - P2 holds R2 and waits for R3.  
     - P3 holds R3 and waits for R1.

3. **No Preemption**  
   - Resources cannot be forcibly taken away from a process; a process must release them voluntarily after completing its current operation.

4. **Circular Wait**  
   - There is a circular chain of processes waiting for resources held by each other:  
     - P1 → R2 (held by P2)  
     - P2 → R3 (held by P3)  
     - P3 → R1 (held by P1)  
   - This forms a cycle: P1 → P2 → P3 → P1.

#### Resource Allocation Graph (as Directed Edges)

Represented as a text list of directed edges:

- R1 → P1 (allocated)
- R2 → P2 (allocated)
- R3 → P3 (allocated)
- P1 → R2 (requested)
- P2 → R3 (requested)
- P3 → R1 (requested)

#### Edge to Remove to Break Circular Wait

Removing the edge **P3 → R1 (requested)** would break the circular wait:

- If P3 does not request R1, then P3 can complete its work using only R3 and release R3, allowing P2 to acquire R3, complete, and release R2, allowing P1 to acquire R2, complete, and release R1.
- The cycle P1 → P2 → P3 → P1 is broken.

#### Deadlock Prevention Strategy and Limitation

**Strategy:** Impose **resource ordering**.

- Define a global ordering of resources, e.g., R1 < R2 < R3.
- Require that processes only request resources in increasing order (e.g., a process holding R2 cannot request R1).
- In our scenario:
  - If P1 must request in order R1 → R2 → R3, it cannot hold R1 and then request R2 while P2 holds R2 and requests R3, etc., because the ordering would prevent certain request patterns that lead to cycles.

**Limitation:**

- Resource ordering can reduce flexibility and concurrency, as processes may need to request resources in a non-optimal order for their logic, potentially leading to longer waiting times or underutilization of resources.
- It may also be difficult to define a consistent ordering when new resources are added or when different subsystems have different natural ordering constraints.

---

## How to Run

```bash
# Scheduling simulator
python3 scheduler.py
# with custom Round Robin quantum
python3 scheduler.py 3

# Synchronization demo
python3 sync_demo.py
```

Both scripts print their results to the console.
