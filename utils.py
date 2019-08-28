import numpy as np
import tensorflow as tf
import gym
import matplotlib.pyplot as plt
import cv2
import os
import random

def set_seed(seed_number, env):
    os.environ['PYTHONHASHSEED']=str(seed_number)
    random.seed(seed_number)
    np.random.seed(seed_number)
    tf.set_random_seed(seed_number)
    env = gym.make(env)
    env.seed(seed_number)
    return env

def get_session(): # use with get_session() as sess: or sess = get_session()
    from tensorflow.compat.v1 import InteractiveSession
    tf.reset_default_graph()
    config = tf.ConfigProto()
    config.gpu_options.allow_growth = True
    session = InteractiveSession(config=config)
    return session
    
def preprocess(images): # input : raw image of shape (N, 210, 160, 3) from gym atari env
    images = np.array(images).reshape(1, 210, 160, 3)
    rgb2y = 0.299*images[:,:,:,0] + 0.583*images[:,:,:,1] + 0.114*images[:,:,:,2] # compute luminance from rgb
    resized_input = cv2.resize(rgb2y.reshape(210, 160), (84, 84)) # resize with bilinear interpolation (default)
    return resized_input # output of shape (84,84)

def linear_decay(step_count, start=1, end=0.1, frame=1000000):
    eps = start-(start-end)/(frame-1)*(step_count+1)
    if step_count > (frame-2):
        eps = end
    return eps

class ex_replay(object): # experience replay
    
    def __init__(self, memory_size, batch_size = 32):
        self.memory_size = memory_size
        self.memory_frame = np.zeros((memory_size, 84, 84)) 
        self.memory_a_r = np.zeros((memory_size, 3))
        self.batch_size = batch_size
        
    def save_ex(self, s_t, a_t, r_t, next_s_t, info, step_count): 
        """Input: s_t and next_s - each of shape (210, 160, 3) (raw observation from env), a_t and r_t
           Save unit frame of shape 84*84 instead of saving stacked frames"""
        if step_count == 0:
            self.memory_frame[step_count%self.memory_size, :, :] = preprocess(s_t)
        else:
            self.memory_frame[(step_count+1)%self.memory_size, :, :] = preprocess(next_s_t)
            self.memory_a_r[step_count%self.memory_size, 0], self.memory_a_r[step_count%self.memory_size, 1],  = a_t, r_t
            self.memory_a_r[step_count%self.memory_size, 2] = info
    
    def stack_frame(self, b_idx, step_count = None, batch = True):
        """Stack 4 most recent frames
           Input: index of batch sample, Ouput: of shape (N, 84, 84, 4)
           if batch = False, stack for a single data frame to compute forward pass of NN for selecting greedy action during exploration""" 
        if batch:
            out_frame = np.zeros((self.batch_size, 84, 84, 4))
            for idx, val in enumerate(b_idx):
                for j in range(4):
                    if val-3+j >= 0:
                        out_frame[idx,:,:,j] = self.memory_frame[val-3+j]
                    else:
                        out_frame[idx,:,:,j] = self.memory_frame[(self.memory_size) + (val-3+j)]
        else:
            out_frame = np.zeros((1, 84, 84, 4))
            val = step_count % self.memory_size
            for j in range(4):
                if val-3+j >= 0:
                    out_frame[0,:,:,j] = self.memory_frame[val-3+j]
                else:
                    out_frame[0,:,:,j] = self.memory_frame[(self.memory_size) + (val-3+j)]
                    
        return out_frame
   
    def sample_ex(self, step_count):
        "Sample experience from replay. Output exprience with batch_size"
        if step_count < self.memory_size:
            b_idx = np.random.choice(step_count, self.batch_size)
        else:
            b_idx = np.random.choice(self.memory_size, self.batch_size)
        s_t, next_s_t = self.stack_frame(b_idx), self.stack_frame(b_idx+1) # each of shape (N,84,84,4), which is input of NN
        a_t, r_t, info_t = self.memory_a_r[b_idx, 0], self.memory_a_r[b_idx, 1], self.memory_a_r[b_idx, 2]
        return s_t, a_t, r_t, next_s_t, info_t
