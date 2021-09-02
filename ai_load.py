from setup_load import *

COLUMNWIDTH,OPENING_SIZE = 50, 300

import random
from random import randint as rng
import numpy as np
from collections import deque
from keras.models import Sequential
from keras.layers import Dense
from tensorflow.keras.optimizers import Adam
import os
import shelve

SHUTDOWN = None

class Env():
    def __init__(self):
        self.bird=Bird()
        self.column1 = Column(SCREENWIDTH,COLUMNWIDTH,OPENING_SIZE)
        self.column2 = Column(SCREENWIDTH*3//2 + COLUMNWIDTH//2, COLUMNWIDTH,OPENING_SIZE)
        self.reward = 0
        self.count=0
        self.done=False

    def reset(self):
        self.__init__()
        return self.get_state()

    def get_state(self):
        state = tuple()
        state += self.bird.get_position()[:2]
        state += (self.bird.vel,)

        pos1 = self.column1.get_position()[:2]
        pos2 = self.column2.get_position()[:2]
        state += pos1+pos2
        state = list(state)
        return state

        
    def bird_movement(self):
        if self.bird.action == 1: # jump
            self.bird.move(True)
        else: # not jumping
            self.bird.move()

        if self.column1.score(self.bird) or self.column2.score(self.bird):
            self.reward += 1
            self.count += 1

        if self.column1.collide(self.bird) or self.column2.collide(self.bird):
            self.bird.kill()

        if self.bird.y+self.bird.h > SCREENWIDTH:
            self.bird.kill()

        if not self.bird.alive: #bird is dead, give negative reward
            self.reward = -100
            
        else: #bird is alive
            self.reward += 0.1

    def runframe(self, action1):
        self.done = False
        self.bird.action = action1
        self.column1.move()
        self.column2.move()
        self.bird_movement()
        state = self.get_state()

        if not self.bird.alive:
            self.done=True
        
        if self.count>60:
            self.done=True

        return state, self.reward, self.done

    def render(self):
        global SHUTDOWN
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                SHUTDOWN = True
        window.fill((255,255,255))
        for item in [self.bird, self.column1, self.column2]:
            item.draw(window)
        pygame.display.update()




env = Env()
state_size = 7 #env.observation_space.shape[0]
action_size = 2 #env.action_space.n
batch_size=64
n_episodes = 1000
output_dir = 'data/'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

class DQNAgent:
    def __init__(self,state_size,action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=100000)
        self.gamma = 0.95 #decrease by 0.95 each time
        self.epsilon = 1.0 #exploitation=0 vs exploration=1
        self.epsilon_decay = 0.995 #less and less each time
        self.epsilon_min = 0.001 #0.1% exploration
        self.learning_rate = 0.001
        self.model = self._build_model()

    def _build_model(self):
        model=Sequential()
        model.add(Dense(24,input_dim = self.state_size, activation = 'relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse',optimizer=Adam(learning_rate=self.learning_rate))
    
        return model
    
    def remember(self,state,action,reward,next_state,done):
        self.memory.append((state,action,reward,next_state,done))
        
    def act(self,state):
        if np.random.rand()<=self.epsilon:
            return int(np.random.rand() < 0.055)
            #return random.randrange(self.action_size)
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])
        
    def replay(self,batch_size):
        minibatch=random.sample(self.memory,batch_size)
        for state,action,reward,next_state,done in minibatch:
            target=reward
            if not done:
                target = reward + self.gamma * np.amax(self.model.predict(next_state)[0])
            target_f = self.model.predict(state)
            target_f[0][action]=target
            self.model.fit(state,target_f,epochs=1,verbose=0)
            
        if self.epsilon>self.epsilon_min:
            self.epsilon*=self.epsilon_decay

    def save(self,name):
        self.model.save_weights(name)

    def load(self,name):
        self.model.load_weights(name) 

    def load_all(self, episode_num):
        self.load_reset('{}agent_{:05d}.hdf5'.format(output_dir,episode_num))
        self.load_memory(episode_num)

    def load_reset(self, filename):
        self.load(filename)
        self.epsilon = 0.0

    def load_memory(self, episode_num):
        with shelve.open(f'{output_dir}memory.pickle') as file:
            self.memory = file.get(f'{episode_num}') or self.memory
            


agent = DQNAgent(state_size,action_size)

agent.load_reset('data/agent_02700.hdf5')

episode = 0
count   = 0
        

if __name__ == '__main__':
    while True:
        if SHUTDOWN:
            break
        episode+=1
        # Learning Loop
        state=env.reset() 
        state=np.reshape(state,[1, state_size])
        for t in range(5000):
            if window is not None:
                env.render()
                if SHUTDOWN: 
                    break
            action = agent.act(state)
            next_state, reward, done = env.runframe(action)
            next_state=np.reshape(next_state,[1, state_size])
            agent.remember(state,action,reward,next_state,done)
            state=next_state
            if done:
                if episode%10 ==1 or env.count>5:
                    print('episode: {}/{},\ttime: {},\tscore: {},\tepsilon: {:.2}'.format( episode,n_episodes,t,env.count,agent.epsilon))
                break
        
    

if RENDERING:
    pygame.quit()





