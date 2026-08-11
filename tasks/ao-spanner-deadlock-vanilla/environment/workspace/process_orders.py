#!/usr/bin/env python3
import sys
import sqlite3
import threading
import time

db_path = "orders.db"

# Thread A transaction logic: updates inventory first, then orders
def process_type_a():
    conn = sqlite3.connect(db_path, timeout=1.0)
    try:
        c = conn.cursor()
        c.execute("BEGIN IMMEDIATE")
        
        print("[Thread A] Locking inventory table...")
        c.execute("UPDATE inventory SET quantity = quantity - 1 WHERE id = 1")
        
        time.sleep(0.3)
        
        print("[Thread A] Attempting to lock orders table...")
        c.execute("UPDATE orders SET status = 'processed' WHERE id = 1")
        
        conn.commit()
        print("[Thread A] Transaction succeeded!")
    except sqlite3.OperationalError as e:
        print(f"[Thread A] Transaction failed due to lock contention: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

# Thread B transaction logic: ALSO updates inventory first, then orders!
def process_type_b():
    conn = sqlite3.connect(db_path, timeout=1.0)
    try:
        c = conn.cursor()
        c.execute("BEGIN IMMEDIATE")
        
        # Vanilla is aligned to lock inventory first, then orders (prevents deadlocks)
        print("[Thread B] Locking inventory table...")
        c.execute("UPDATE inventory SET quantity = quantity - 1 WHERE id = 1")
        
        time.sleep(0.3)
        
        print("[Thread B] Attempting to lock orders table...")
        c.execute("UPDATE orders SET status = 'processing' WHERE id = 1")
        
        conn.commit()
        print("[Thread B] Transaction succeeded!")
    except sqlite3.OperationalError as e:
        print(f"[Thread B] Transaction failed due to lock contention: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

def main():
    print("Starting concurrent transaction processors...")
    
    t1 = threading.Thread(target=process_type_a)
    t2 = threading.Thread(target=process_type_b)
    
    t1.start()
    time.sleep(0.1) # Offset start slightly
    t2.start()
    
    t1.join()
    t2.join()
    
    print("Concurrency simulation finished: SUCCESS")

if __name__ == "__main__":
    main()
