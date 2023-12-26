import wandb
import numpy as np
import random
import math
from copy import deepcopy
import pickle

from game_map import levels
from qlearn import QTable


class Level:
  def __init__(self, level, current_level):
    self.tiles = level["tiles"]
    
    self.tiles_set = set()
    
    for z, layer in enumerate(self.tiles):
      for y, row in enumerate(layer):
        for x, tile in enumerate(row):
          if tile:
            if tile == 2:
              self.goal_pos = (x,y,z)
            self.tiles_set.add((x,y,z))
    
    self.objects = deepcopy(level["objects"])
    
    self.checkpoint = "checkpoint" in level["objects"]
    self.checkpointed = False
    
    self.player = self.objects["player"]["pos"]
    
    self.steps = 0
    
    self.level = current_level
  
  @property
  def state(self):
    return tuple([tuple(
      [round(coord) for coord in obj["pos"]]
    ) for obj in self.objects.values()] + [self.steps, self.level])
  
  @property
  def player_state(self):
    if (round(self.player[0]), round(self.player[1]), 0) in self.tiles_set:
      if (round(self.player[0]), round(self.player[1]), 0) == self.goal_pos:
        if self.checkpoint:
          if self.checkpointed:
            return "win"
          else:
            return None
        else:
          return "win"
      else:
        return None
    elif "checkpoint" in self.objects:
      if [round(self.player[0]), round(self.player[1]), 0] == self.objects["checkpoint"]["pos"]:
        if self.checkpointed:
          return None
        else:
          self.checkpointed = True
          return "checkpoint"
      else:
        return "lose"
    else:
      return "lose"


class Game:
  def __init__(self):
    self.tile_data = {
      1:"assets/tiles/stone.png",
      2:"assets/tiles/goal.png"
    }
    
    self.object_data = {
      "robot-1":"assets/robot/1.png",
      "robot-2":"assets/robot/2.png",
      "robot-3":"assets/robot/3.png",
      "robot-4":"assets/robot/4.png",
      "checkpoint-1":"assets/tiles/checkpoint.png",
      "checkpoint-2":"assets/tiles/checkpoint-done.png"
    }
    
    self.levels = levels
    
    self.max_level = len(self.levels)
    
    self.current_level = 1
    
    self.level = Level(self.levels[self.current_level], self.current_level)
    
    self.level_complete = False
    
    self.end = False
    
    self.action = None
    
    self.q_table = QTable()
  
  def train(self, logging=False):
    # parameters
    alpha = 0.2 # learning rate
    gamma = 0.9 # discount factor
    
    # training parameters
    n_episodes = 12000 # number of episodes to train for
    n_max_steps = 70 # max number of steps per episode
    
    epsilon = 0.05 # whether to make a random choice or choose best action
    
    if logging:
      # setup wandb
      wandb.init(project="Hackathon", entity="icemastereric")
      
      wandb.config = {
        "learning_rate": alpha,
        "discount_factor": gamma,
        "episodes": n_episodes,
        "steps":n_max_steps,
        "epsilon": epsilon
      }
    
    for episode in range(n_episodes):
      current_level = 1
      
      level = Level(self.levels[current_level], current_level)
      
      traveled = [] # keep track of places where agent has traveled and discourage infinite loops
      
      state = level.state
      
      win = False
      
      end = False
      
      self.q_table.epsilon = epsilon
      
      action = self.q_table.epsilon_greedy(state)
      
      total_reward = 0
      
      for step in range(n_max_steps):
        if win == True:
          win = False
          
          current_level += 1
          
          traveled.clear()
          
          if current_level <= self.max_level:
            level = Level(self.levels[current_level], current_level)
          else:
            break
        else:
          if action == 0:
            level.player[0] += 1
          elif action == 1:
            level.player[0] -= 1
          elif action == 2:
            level.player[1] += 1
          elif action == 3:
            level.player[1] -= 1
          
          level.steps += 1
        
        next_state = level.state
        
        player_state = level.player_state
        
        if player_state == "win":
          reward = 100
          win = True
        
        elif player_state == "lose":
          reward = -30
          end = True
        
        elif player_state == "checkpoint":
          reward = 100
        
        else:
          reward = -1
        
        if level.player in traveled:
          if not level.checkpoint:
            reward -= 10
          else:
            reward -= 3
        
        total_reward += reward
        
        traveled.append(level.player.copy())
        
        next_action = self.q_table.epsilon_greedy(next_state)
        
        self.q_table.update_q(state, action, reward, next_state, next_action)
        
        state = next_state
        action = next_action
        
        if end == True:
          break
      
      if logging:
        wandb.log({
          "level":current_level,
          "steps":level.steps,
          "reward":total_reward,
          "q_table_size":len(self.q_table.q_table)
        })
    
    with open(f"models/model-{random.randint(100,999)}.pkl","wb") as f:
      pickle.dump(self.q_table,f)
  
  def load_model(self, path):
    with open(path, "rb") as f:
      self.q_table = pickle.load(f)
  
  def step(self):
    player_state = self.level.player_state
    
    if player_state == "win":
      self.level_complete = True
      
      self.action = None
      
      self.current_level += 1
      
      if self.current_level <= self.max_level:
        self.level = Level(self.levels[self.current_level], self.current_level)
      
      else:
        self.end = True
      
      return
    
    elif player_state == "lose":
      self.end = True
      
      return
    
    self.action, data = self.q_table.eval_greedy(self.level.state)
    
    self.level.steps += 1
    
    if self.action == 0:
      self.level.objects["player"]["sprite"] = "robot-1"
    elif self.action == 1:
      self.level.objects["player"]["sprite"] = "robot-4"
    elif self.action == 2:
      self.level.objects["player"]["sprite"] = "robot-2"
    elif self.action == 3:
      self.level.objects["player"]["sprite"] = "robot-3"
    
    if self.level.checkpointed:
      self.level.objects["checkpoint"]["sprite"] = "checkpoint-2"
    
    return data
  
  def update(self, fps):
    if self.action == 0:
      self.level.player[0] += 1/fps
    elif self.action == 1:
      self.level.player[0] -= 1/fps
    elif self.action == 2:
      self.level.player[1] += 1/fps
    elif self.action == 3:
      self.level.player[1] -= 1/fps