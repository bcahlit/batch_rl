import numpy as np
import tensorflow as tf
import math
import gym
import time
from matplotlib import pyplot as plt
from utils import *

def env_step(env, current_state, action, FLAGS): # skip k frames
    frame_list = [current_state]
    rew = 0
    for i in range(FLAGS.skip_frame):
        next_state, r_t, done, info = env.step(action)
        rew += r_t
        frame_list.append(next_state)
        if done:
            break
    next_state = np.maximum.reduce(frame_list)
    rew = np.sign(rew) # clip reward
    return next_state, rew, done, info

def e_greedy_execute(num_actions, eps, greedy_action):
    action_probs = (1/num_actions)*eps*np.ones((num_actions,))
    action_probs[tuple(greedy_action)] += 1-eps
    a_t = np.random.choice(num_actions, 1, p = action_probs)[0]
    return a_t

 
def categorical_algorithm():
    return None

    




def show_process(FLAGS, episode_count ,rew_epi, global_avg_reward, loss_epi, eps, step_count, step_start, 
                 time1, reward_his, mean_reward, exp_memory, loss_his, sess, saver):
    
    if episode_count == 0:
        print('\nStart training '+ str(FLAGS.arch))
        
    if episode_count % FLAGS.print_every == 0:
        print('\nEpisode {0}: reward {1:2g}, avg_reward {2:2g} loss {3:2g}, epsilon {4:2g}, steps {5}, total steps {6}'\
              .format(episode_count+1 ,rew_epi, global_avg_reward, loss_epi, eps, step_count - step_start, step_count))
        
        time2 = time.time()
        print('time (minutes) :', int((time2-time1)/60))
        plt.plot(reward_his, label = 'reward')
        plt.plot(mean_reward, label = 'avg reward')
        plt.ylim(-30, 25)
        plt.title('Iteration frame: '+ str(step_count))
        plt.legend()
        plt.savefig('./results/it_frame_reward'+str(step_count))
        plt.clf()
                    
        plt.plot(loss_his, label = 'loss')
        plt.title('Iteration frame: '+ str(step_count))
        plt.legend()
        plt.savefig('./results/it_frame_loss'+str(step_count))
        plt.clf()
               
        if episode_count % 500 == 0 or step_count == FLAGS.max_frames:
            if step_count > 1000000:
                np.save('./results/replay_memory', exp_memory.memory_frame) 
                np.save('./results/replay_memory2', exp_memory.memory_a_r)   
                np.save('./results/loss_his', loss_his)
                np.save('./results/reward_his', reward_his)
                saver.save(sess, "./tmp/model", global_step=step_count)
                if step_count == FLAGS.max_frames-1:
                    print('Done')
                    #os.system('shutdown -s -t 60')    

def eval_agent(num_games, env, exp_memory, sess, num_actions, greedy_action, gd_idx, state, FLAGS, eps = 0.05):
    reward_his = []
    step_count = 3
    eps = eps
    for j in range(num_games):
        s_t = env.reset()   
        done = False
        if j == 0:
            for i in range(4):
                exp_memory.save_ex(s_t, None, None, None, None, step_count = j)
            while done == False:
                # compute forward pass to find greedy action and select action with epsilon greedy strategy
                stacked_s = exp_memory.stack_frame(b_idx = None, step_count = step_count, batch = False)
                greedy_action = sess.run([gd_idx], feed_dict = {state:stacked_s})
                a_t = e_greedy_execute(num_actions, eps, greedy_action)
                if step_count % 6 == 0: # random action on the 6th frame
                    a_t = np.random.randint(self.num_actions)
             
                next_state, r_t, done, info =  env_step(env, s_t, a_t, FLAGS) # step ahead  env.step(a_t)
                 
                # save (s_t, a_t, r_t, s_t+1) to memory
                exp_memory.save_ex(s_t, a_t, r_t, next_state, done, step_count = step_count) 
                s_t = next_state
                rew_epi += r_t
                step_count += 1
            reward_his.append(rew_epi)
    plt.plot(reward_his)
    print('Mean reward', np.mean(reward_his))
    print('Std reward', np.std(reward_his))
    return reward_his

def reload_session(saver, exp_memory):
    saver.restore(sess, "./tmp/model.ckpt")
    exp_memory.memory_frame = np.load('./results/replay_memory')       
    exp_memory.memory_a_r = np.load('./results/replay_memory2')
    loss_his = np.load('./results/loss_his')
    reward_his = np.load('./results/reward_his')
    step_count = len(loss_his)-1
    return exp_memory, loss_his, reward_his, step_count
 