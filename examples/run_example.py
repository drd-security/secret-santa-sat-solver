from pathlib import Path
import sys
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from secret_santa import provide_all_solutions

participants = pd.read_csv(Path(__file__).with_name("participants.csv"))
solutions = provide_all_solutions(participants, max_forbidden_cycle=3)
print(f"Found {len(solutions)} solution(s).")
for i, solution in enumerate(solutions[:5], 1):
    print(f"\nSolution {i}")
    for giver, receiver in solution.items():
        print(f"  {giver} -> {receiver}")
