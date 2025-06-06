import torch
import random
import numpy as np
from collections import deque
from snake_game import SnakeGame, Direction, Point 
from model import Linear_QNetwork, QNetTrainer
from helper import plot

MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LEARNING_RATE = 0.001

class Agent:

    def __init__(self):
        self.number_of_games = 0
        self.epsilon = 0.39  # randomness (epsilon - greedy policy)
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.99
        self.gamma = 0.9 # discount rate
        self.memory = deque(maxlen = MAX_MEMORY)
        self.model = Linear_QNetwork(11, 256, 3)
        self.trainer = QNetTrainer(self.model, lr = LEARNING_RATE, gamma = self.gamma)

    def get_state(self, game):
        head = game.snake[0]
        point_l = Point(head.x - 20, head.y)
        point_r = Point(head.x + 20, head.y)
        point_u = Point(head.x, head.y - 20)
        point_d = Point(head.x, head.y + 20)

        dir_l = game.direction == Direction.LEFT
        dir_r = game.direction == Direction.RIGHT
        dir_u = game.direction == Direction.UP
        dir_d = game.direction == Direction.DOWN

        state = [
            # Danger straight
            (dir_r and game.is_collision(point_r)) or 
            (dir_u and game.is_collision(point_u)) or 
            (dir_d and game.is_collision(point_d)) or 
            (dir_l and game.is_collision(point_l)),
            
            # Danger Right
            (dir_r and game.is_collision(point_d)) or 
            (dir_u and game.is_collision(point_r)) or 
            (dir_d and game.is_collision(point_l)) or 
            (dir_l and game.is_collision(point_u)),
            
            # Danger Right
            (dir_r and game.is_collision(point_u)) or 
            (dir_u and game.is_collision(point_l)) or 
            (dir_d and game.is_collision(point_r)) or 
            (dir_l and game.is_collision(point_d)),
            
            # Move directions
            dir_l,
            dir_r,
            dir_u,
            dir_d,

            # Food Locations
            game.food.x < game.head.x, # Food left
            game.food.x > game.head.x, # Food right
            game.food.y < game.head.y, # Food down
            game.food.y > game.head.y # Food Up
        ]

        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory
        
        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self,state):
        # Random moves (Epsilon Greedy)
        print(self.epsilon)
        new_action = [0, 0, 0]
        if(random.uniform(0,1) <= self.epsilon):
            move = random.randint(0,2)
            new_action[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            new_action[move] = 1
        print(new_action)

        return new_action

    def change_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

def train():
    plot_scores = []
    plot_mean_scores = []
    total_score = 0
    record = 0
    agent = Agent()
    game = SnakeGame()

    while True:
        state_old = agent.get_state(game)
        move = agent.get_action(state_old)
        reward, done, score = game.play_step(move)
        state_new = agent.get_state(game)

        agent.train_short_memory(state_old, move, reward, state_new, done)
        agent.remember(state_old, move, reward, state_new, done)

        if done: 
            game.reset()
            agent.number_of_games += 1
            agent.change_epsilon()
            agent.train_long_memory()

            if score > record:
                record = score
                agent.model.save()

            print('Game', agent.number_of_games, 'Score', score, 'Record', record)

            plot_scores.append(score)
            total_score += score
            mean_score = total_score/agent.number_of_games
            plot_mean_scores.append(mean_score)
            plot(plot_scores, plot_mean_scores)

if __name__ == '__main__':
    train()

















