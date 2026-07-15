#!/usr/bin/env python3
"""
Synchronization Demo for CampusConnect:

- Unsynchronized version with a Barrier between read and write,
  causing a deterministic lost increment.
- Synchronized version using a binary semaphore (Lock) to make
  the read-modify-write atomic, producing the correct count.
"""

import threading


# Shared counter
counter = 0
counter_lock = threading.Lock()

# For unsynchronized version: barrier between read and write
barrier = threading.Barrier(2)


def unsynchronized_increment(thread_id: int, iterations: int) -> None:
    """
    Unsynchronized increment with a Barrier between read and write.
    Both threads:
      1. Read counter into a local variable.
      2. Wait at the barrier.
      3. After both have read, write back local + 1.

    Because both threads read the same stale value, exactly one
    increment is lost deterministically.
    """
    local = counter
    # Wait for the other thread to also read
    barrier.wait()

    # Now both threads write based on the same stale 'local'
    new_value = local + 1
    # Non-atomic write (no lock)
    counter = new_value


def synchronized_increment(thread_id: int, iterations: int) -> None:
    """
    Synchronized increment using a Lock (binary semaphore).
    The entire read-modify-write is inside the critical section,
    making it atomic.
    """
    for _ in range(iterations):
        with counter_lock:
            local = counter
            counter = local + 1


def run_unsynchronized(iterations: int = 100000) -> None:
    """
    Run the unsynchronized version with two threads.
    Shows that the final counter is incorrect (less than 2*iterations).
    """
    global counter
    counter = 0
    barrier = threading.Barrier(2)

    t1 = threading.Thread(target=unsynchronized_increment, args=(1, iterations))
    t2 = threading.Thread(target=unsynchronized_increment, args=(2, iterations))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    expected = 2 * iterations
    print("\n=== Unsynchronized Version (with Barrier) ===")
    print(f"Expected counter: {expected}")
    print(f"Actual counter:   {counter}")
    if counter == expected:
        print("Result: CORRECT (unexpected; barrier may not have forced collision).")
    else:
        print("Result: INCORRECT (lost increment due to race condition).")


def run_synchronized(iterations: int = 100000) -> None:
    """
    Run the synchronized version with two threads using a Lock.
    Shows that the final counter is correct (equal to 2*iterations).
    """
    global counter
    counter = 0

    t1 = threading.Thread(target=synchronized_increment, args=(1, iterations))
    t2 = threading.Thread(target=synchronized_increment, args=(2, iterations))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    expected = 2 * iterations
    print("\n=== Synchronized Version (with Lock) ===")
    print(f"Expected counter: {expected}")
    print(f"Actual counter:   {counter}")
    if counter == expected:
        print("Result: CORRECT (atomic read-modify-write).")
    else:
        print("Result: INCORRECT (unexpected).")


if __name__ == "__main__":
    iterations = 100000
    run_unsynchronized(iterations)
    run_synchronized(iterations)
