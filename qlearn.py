import numpy as np
import random


class QTable:
  def __init__(self, n_actions=4, alpha=0.1, gamma=0.95, epsilon=1):
    # parameters
    self.alpha = alpha
    self.gamma = gamma
    
    self.epsilon = epsilon
    
    self.n_actions = n_actions
    
    self.q_table = {}
  
  def epsilon_greedy(self, state):
    r = np.random.uniform(0,1)
    
    if r < self.epsilon:
      return random.randint(0,self.n_actions-1)
    
    else:
      if state in self.q_table:
        if len(set(self.q_table[state])) == 1:
          return random.randint(0,self.n_actions-1)
        
        else:
          return self.q_table[state].index(max(self.q_table[state]))
      
      else:
        return 0
  
  def update_q(self, state, action, reward, next_state, next_action):
    if state in self.q_table:
      if next_state in self.q_table:
        self.q_table[state][action] += self.alpha * (reward + self.gamma * (self.q_table[next_state][next_action] - self.q_table[state][action]))
      
      else:
        self.q_table[next_state] = [0 for _ in range(self.n_actions)]
        
        self.q_table[state][action] += self.alpha * (reward + self.gamma * (self.q_table[next_state][next_action] - self.q_table[state][action]))
    
    else:
      self.q_table[state] = [0 for _ in range(self.n_actions)]
      
      if next_state in self.q_table:
        self.q_table[state][action] += self.alpha * (reward + self.gamma * self.q_table[next_state][next_action])
      
      else:
        self.q_table[next_state] = [0 for _ in range(self.n_actions)]
        
        self.q_table[state][action] += self.alpha * reward
  
  def eval_greedy(self, state):
    print(state)
    
    if state not in self.q_table:
      print("no state")
      return random.randint(0,self.n_actions-1), ""
    
    elif len(set(self.q_table[state])) == 1:
      print("random choice")
      return random.randint(0,self.n_actions-1), ""
    
    else:
      print("smart")
      return self.q_table[state].index(max(self.q_table[state])), [str(round(d,2)) for d in self.q_table[state]]
