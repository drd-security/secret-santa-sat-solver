from pysat.formula import CNF
from pysat.solvers import Solver
from pandas import DataFrame, read_csv
from os import path
from itertools import permutations

###################################################################################################
#                                       Complexity:                                            #
###################################################################################################
''' 
Complexity: 
### Here establish the complexity of your encoding

***Here:***
  n is the number of participants,

1.**Number of variables***

    Each gift exchange is represented by a variable X_(i,j), where i is the giver and j is the receiver.
    Number of variables=n*n

2.**Number of Clauses:**
    - **At least one gift must be given by each person**: n clauses.
    - **At most one gift must be given by each person**: (n * (n - 1) * (n - 2)) / 2 clauses.
    - **At least one gift must be received by each person**: n clauses.
    - **At most one gift must be received by each person**: (n * (n - 1) * (n - 2)) / 2 clauses.
    - **No self-gifting**: n  clauses.(but the n clauses are duplicate clauses since they are already present in constraint 1 and 2)
    - **No mutual gifting**: (n*(n-1))/2 clauses .
    - **No gifting within the same family**: f clauses (where f is the number of family pairs).
    - **Avoiding cycles of length <= k**: Sum of binomial coefficients for each cycle length i (i >= 3) with a factorial term.
      Sum = sum(C(n, i) * (i-1)! for i in range(3, k+1))

    - **Total Number of Clauses (Exact Formula):**
      Total Clauses = 2n + n(n-1)(n-2) + n + (n*(n-1))/2 + f + sum(C(n, i) * (i-1)! for i in range(3, k+1))
      which resumes to ((2n^3 - 5n^2 +9n)/2) + f + sum(C(n, i) * (i-1)! for i in range(3, k+1))) 

3.**Big-O Complexity (as a function of n and k):**
    - O(n^3 + k * n^k)

    Where:
    - O(n^3) comes from the main constraints related to gift-giving.
    - O(k * n^k) comes from avoiding short cycles of length <= k.

'''

###################################################################################################
#                                      Helper functions                                           #
###################################################################################################
def remove_duplicates(cnf):
    seen_clauses = set()  # Set to track unique clauses
    unique_cnf : list[list[int]] = []  # List to store the final CNF without duplicates
    
    for clause in cnf:
        # Normalize the clause by sorting its literals
        normalized_clause = tuple(sorted(clause))
        
        # If this normalized clause hasn't been seen before, add it to the unique CNF
        if normalized_clause not in seen_clauses:
            unique_cnf.append(clause)
            seen_clauses.add(normalized_clause)
    
    return unique_cnf

def init_variable(participants: DataFrame):
   # Initialize variables
    variables = {}  # Map (giver, receiver) -> variable index

    # Assign a unique variable for each potential gift (giver -> receiver)
    variable_counter = 1
    for giver in participants.name:
      for receiver in participants.name:
        variables[(giver, receiver)] = variable_counter
        variable_counter += 1

    return variables

###################################################################################################
#                                      Main functions                                             #
###################################################################################################
'''
Encoding:
### Here briefly describe the encoding of the problem as a CNF formula
'''
                        
def encode_cnf(participants: DataFrame, max_forbidden_cycle: int = 2):
    """
    Encode the secret santa problem as a CNF formula
    Given a list of participants, returns a CNF formula that encodes that
    - each participant receives from and gives to exactly one other participant
    - no participant is assigned to themselves
    - if a participant A is assigned to participant B, then participant B is not assigned to
      participant A
    - if two participants are from the same family, they cannot be assigned to each other
    - if max_forbidden_cycle is given, cycles of length less than or equal to it are forbidden

    The cnf is represented as a list of lists of non-zero integers, whose sign indicates the
    propositional polarity of the variable.

    input:
      - participant: pandas dataframe with columns ["name", "family"] containing the list of
        participants
      - max_forbidden_cycle: maximum cycle length that should be avoided
    output:
      - cnf: a CNF formula as a list of lists of non-zero integers
    """
    cnf: list[list[int]] = []
    variables =init_variable(participants)

    # Constraint 1: Each person must give a gift to exactly one other person
    for giver in participants.name:
      # At least one gift must be given by this person
      cnf.append([variables[(giver, receiver)] for receiver in participants.name if giver != receiver])    
      # At most one gift given
      for receiver1 in participants.name:
          for receiver2 in participants.name:
            if receiver1 != receiver2 and receiver1 != giver and receiver2 != giver :
              cnf.append([-variables[(giver, receiver1)], -variables[(giver, receiver2)]])

    # Constraint 2: Each person must receive exactly one gift  
    for receiver in participants.name:
      #recieves atleast one gift 
      cnf.append([variables[(receiver, giver)] for giver in participants.name if receiver != giver])
      #recieves at most one gift 
      for giver1 in participants.name:
         for giver2 in participants.name:
          if giver1 != giver2 and giver1 != receiver and giver2 != receiver :
              cnf.append([-variables[(giver1,receiver)], -variables[(giver2,receiver)]])

    # Constraint 3: No self-gifting
    for giver in participants.name:
        for receiver in participants.name:
           if giver==receiver :
              cnf.append([-variables[(giver, receiver)]])
    
    #Constraint 4: No person can give a gift to someone of the same family 
    for i in range(len(participants.name)):
        for j in range(len(participants.name)):
            if i != j and participants.family[i] == participants.family[j]:
              cnf.append([-variables[(participants.name[i], participants.name[j])]])

    #Constraint 5:No person can give a gift to someone who gives them a gift
    for giver in participants.name:
      for receiver in participants.name:
          if giver != receiver:
              cnf.append([-variables[(giver, receiver)], -variables[(receiver, giver)]])

    # Constraint 6: Forbidden cycles of length ≤ max_forbidden_cycle
    for cycle_length in range(3, max_forbidden_cycle + 1):
        for cycle in permutations(participants.name, cycle_length):
            cnf.append([-variables[(cycle[i], cycle[(i + 1) % cycle_length])] for i in range(cycle_length)])

    # constraint 7: prevent trivial and duplicate clauses
    cnf1 = remove_duplicates(cnf)
      
    return cnf1


def decode_model(model: list, participants: DataFrame):
    """
    Given a model of the secret santa problem, and the list of participants, return the
    secret santa assignments as a dictionary

    input:
      - model: a model of the secret santa problem as a list of non-zero integers
      - participants: pandas dataframe with columns ["name", "family"] containing the list of
        participants
    output:
      - solution: a dictionary with keys of the form "name (family)" and values of the form
        "name (family)" representing the secret santa assignments. The key is the giver
        and the value is the receiver.
    """
    solution: dict[str, str] = {}
    variables =init_variable(participants)

    # Reverse the variables mapping
    reverse_variables = {v: (giver, receiver) for (giver, receiver), v in variables.items()}

    # Extract positive variables from the model
    positive_variables = [var for var in model if var > 0]

    # Map givers to receivers
    for var in positive_variables:
        if var in reverse_variables:
            giver, receiver = reverse_variables[var]
            giver_key = f"{giver} ({participants.loc[participants.name == giver, 'family'].iloc[0]})"
            receiver_key = f"{receiver} ({participants.loc[participants.name == receiver, 'family'].iloc[0]})"
            solution[giver_key] = receiver_key
    ### Here implement the decoding of the model to the secret santa assignments
    return solution


def provide_all_solutions(participants: DataFrame, max_forbidden_cycle: int = 2):
    """
    Given a list of participants, returns all possible secret santa assignments

    A solution is a dictionary with keys of the form "name (family)" and values of the form
    "name (family)" representing the secret santa assignments. The key is the giver and
    the value is the receiver.

    input:
      - participant: pandas dataframe with columns ["name", "family"] containing the list of
        participants
      - max_forbidden_cycle: maximum cycle length that should be avoided
    output:
      - solutions: a list of all possible (distinct) secret santa assignments
    """
    solutions: list[dict[str, str]] = []
    
    cnf = encode_cnf(participants, max_forbidden_cycle)
    with Solver(bootstrap_with=cnf) as solver:
        while solver.solve():
            model = solver.get_model()
            solution = decode_model(model, participants)
            solutions.append(solution)
            
            # Add blocking clause to prevent this solution from appearing again
            blocking_clause = [-var if var > 0 else -var for var in model ]
            solver.add_clause(blocking_clause)
    
    ### Here implement the generation of all possible solutions
    ### Hint, use incremental solving.
    return solutions
