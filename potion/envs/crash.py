#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from potion.envs.lq import LQ
from gym import spaces
import numpy as np
import math
import time

class crash(LQ):
    def __init__(self):
        
        #max feat: 1
        #max rew: 2.5
        #max action: 4
        #action volume: 8
        
        self.ds = 3
        self.da = 1
        self.horizon = 20
        self.gamma = 0.95
        self.sigma_controller = 1. * np.ones(self.da)
        self.max_pos = np.array([1., 1., 1.])
        self.max_action = 4 * np.ones(self.da)
        self.sigma_noise = 0 * np.eye(self.ds)
        self.tau = 0.1
        self.mass = 0.2
        self.grav = 9.8
        
        self.A = np.array([[1., self.tau, 0],
                           [0., 1.,       -self.tau/(self.mass * self.grav)],
                           [0,  0,        1]])
        
        self.B = np.array([[0.],
                           [self.tau/self.mass],
                           [0]])
        
        self.Q = np.diag([0.7, 0.2, 0])
        self.R = 0.1 * np.eye(1) 

        #Gym attributes
        self.viewer = None
        self.action_space = spaces.Box(low=-self.max_action,
                                       high=self.max_action, 
                                       dtype=np.float32)
        self.observation_space = spaces.Box(low=-self.max_pos, 
                                            high=self.max_pos,
                                            dtype=np.float32)
        
        #Initialize state
        self.seed()
        self.reset()

    def reset(self, state=None):
        self.timestep = 0
        if state is None:
            self.state = np.array(self.np_random.uniform(low=self.max_pos/4,
                                                          high=self.max_pos))
        else:
            self.state = np.array(state)
        # self.state[1] = 0.

        return self.get_state()
    
    def step(self, action, render=False):
        u = np.clip(np.ravel(np.atleast_1d(action)), -self.max_action, self.max_action)
        noise = np.dot(self.sigma_noise, self.np_random.randn(self.ds))
        xn = np.clip(np.dot(self.A, self.state.T) + np.dot(self.B, u) + noise, -self.max_pos, self.max_pos)
        cost = np.dot(self.state,
                      np.dot(self.Q, self.state)) + \
            np.dot(u, np.dot(self.R, u))
        
        crash = xn[0] <= self.max_pos[0]/8
        if crash: cost = np.array([3.])

        self.state = xn.ravel()
        self.timestep += 1
        
        end = self.timestep >= self.horizon or crash
        
        return self.get_state(), -np.asscalar(cost), end, {'danger':int(crash)}
    
    def render(self, mode='human', close=False):
        if close:
            if self.viewer is not None:
                self.viewer.close()
                self.viewer = None
            return

        screen_width = 600
        world_width = math.ceil((self.max_pos[0] * 2) * 1.5)
        xscale = screen_width / world_width
        ballradius = 3
        
        world_height = math.ceil((self.max_pos[0] * 2) * 1.5)
        screen_height = math.ceil(xscale * world_height)
        yscale = screen_height / world_height

        if self.viewer is None:
            clearance = 0  # y-offset
            from gym.envs.classic_control import rendering
            self.viewer = rendering.Viewer(screen_width, screen_height)
            mass = rendering.make_circle(ballradius * 2)
            mass.set_color(.8, .3, .3)
            mass.add_attr(rendering.Transform(translation=(0, clearance)))
            self.masstrans = rendering.Transform()
            mass.add_attr(self.masstrans)
            self.viewer.add_geom(mass)
            if self.ds == 1:
                self.track = rendering.Line((0, 100), (screen_width, 100))
            else:
                self.track = rendering.Line((0, screen_height / 2), (screen_width, screen_height / 2))
            self.track.set_color(0.5, 0.5, 0.5)
            self.viewer.add_geom(self.track)
            zero_line = rendering.Line((screen_width / 2, 0),
                                       (screen_width / 2, screen_height))
            zero_line.set_color(0.5, 0.5, 0.5)
            self.viewer.add_geom(zero_line)

        x = self.state[0]
        y = 0.
        ballx = x * xscale + screen_width / 2.0
        bally = y * yscale + screen_height / 2.0
        self.masstrans.set_translation(ballx, bally)

        return self.viewer.render(return_rgb_array=mode == 'rgb_array')

if __name__ == '__main__':
    env = crash()
    theta_star = env.computeOptimalK()
    print('theta^* = ', theta_star)
    print('J^* = ', env.computeJ(theta_star,env.sigma_controller))
