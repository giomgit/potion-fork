#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from potion.envs.lq import LQ
from gym import spaces
import numpy as np
import math
import time

class mass(LQ):
    def __init__(self):
        self.ds = 2
        self.da = 1
        self.horizon = 10
        self.gamma = 0.9
        self.sigma_controller = 0.1 * np.ones(self.da)
        self.max_pos = np.array([1., 1.])
        self.max_action = 1.0 * np.ones(self.da)
        self.sigma_noise = 0 * np.eye(self.ds)
        self.tau = 0.1
        self.mass = 0.1
        self.attr = 0.
        
        self.A = np.array([[1., self.tau],
                           [0., 1.]])
        
        self.B = np.array([[0.         ],
                           [self.tau/self.mass]])
        
        self.Q = np.diag([0.8, 0.1])
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

    def reset(self, *, seed = None, options = None):

        self.timestep = 0
        if options is not None:
            if 'state' in options:
                self.state = np.array(options['state'])
        else:
            self.state = np.array(self.np_random.uniform(low=-self.max_pos,
                                                          high=self.max_pos))

        return self.get_state(), {}
    
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
    env = mass()
    theta_star = env.computeOptimalK()
    print('theta^* = ', theta_star)
    print('J^* = ', env.computeJ(theta_star,env.sigma_controller))
