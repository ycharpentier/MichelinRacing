# coding: utf-8

import numpy as np

import gym

# from rllab.envs.base import Step

from gym_gmmcar.envs.circle_env import CircleEnv


class FastCircleEnv(CircleEnv):
    """
    Simulation environment for an RC car following a circular
    arc trajectory using relative coordinates as fast as possible.
    """

    def __init__(
            self,
            target_velocity=1.0,
            radius=1.0,
            dt=0.035,
            model_type='BrushTireModel',
            robot_type='RCCar',
            mu_s=1.37,
            mu_k=1.96,
            algo='TRPO',
            eps=0.05
    ):
        """
        Initialize super class parameters, obstacles and radius.
        """
        super(FastCircleEnv, self).__init__(
            target_velocity=target_velocity,
            radius=radius,
            dt=dt,
            model_type=model_type,
            robot_type=robot_type,
            mu_s=mu_s,
            mu_k=mu_k
        )

        self.algo = algo
        self.eps = eps


    def get_reward(self, state, action):
        """
        Reward function definition.
        """
        r = self.radius
        x, y, _, x_dot, y_dot, _ = state
        velocity = np.sqrt(x_dot**2 + y_dot**2)
        distance = np.sqrt(x**2 + y**2) - r

        if self.algo == 'TRPO':
            reward = velocity**2
            if distance >= self.eps:
                reward -= 1000000
        elif self.algo == 'CPO':
            reward = velocity**2
        else:
            raise ValueError('Algorithm type unrecognized')

        info = {}
        info['dist'] = distance
        info['vel'] = velocity
        return reward, info

