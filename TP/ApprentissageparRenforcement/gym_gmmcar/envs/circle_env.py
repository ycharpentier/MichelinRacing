# coding: utf-8

import numpy as np

import gym

# from rllab.spaces import Box

from gym_gmmcar.envs.base_env import VehicleEnv
from gym_gmmcar.misc.utils import normalize_angle


class CircleEnv(VehicleEnv):
    """
    Simulation environment for an RC car following a circular
    arc trajectory using relative coordinates.
    """

    def __init__(
            self,
            target_velocity=1.0,
            radius=1.0,
            dt=0.035,
            model_type='BrushTireModel',
            robot_type='RCCar',
            mu_s=1.37,
            mu_k=1.96
    ):
        """
        Initialize super class parameters, obstacles and radius.
        """
        super(CircleEnv, self).__init__(
            target_velocity=target_velocity,
            dt=dt,
            model_type=model_type,
            robot_type=robot_type,
            mu_s=mu_s,
            mu_k=mu_k
        )

        # Radius of trajectory to follow
        self.radius = radius

        # Reward function parameters
        self._lambda1 = 0.25
        self._lambda2 = 0.25

        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(4,))


    # @property
    # def observation_space(self):
    #     return Box(low=-np.inf, high=np.inf, shape=(4,))


    @property
    def get_initial_state(self):
        """
        Get initial state of car when simulation is reset.
        """
        # Compute domain randomized variables
        x = np.random.uniform(-0.25, 0.25) - self.radius
        yaw = np.random.uniform(-np.pi/3, np.pi/3) + np.deg2rad(270)
        x_dot = np.random.uniform(0, 2*self.target_velocity)
        y_dot = np.random.uniform(-0.6, 0.6)
        yaw_dot = np.random.uniform(-2.0, 2.0)

        state = np.zeros(6)
        state[0] = x
        state[2] = yaw
        state[3] = x_dot
        state[4] = y_dot
        state[5] = yaw_dot
        return state


    def get_reward(self, state, action):
        """
        Reward function definition.
        """
        observation = self.state_to_observation(state)
        r = self.radius
        x, y, _, x_dot, y_dot, _ = state
        dx, theta, _, _ = observation
        velocity = np.sqrt(x_dot**2 + y_dot**2)
        distance = dx

        reward = -np.abs(distance)
        reward -= self._lambda1 * (velocity - self.target_velocity)**2
        reward -= self._lambda2 * max(0, abs(theta) - np.pi/2)**2

        info = {}
        info['dist'] = distance
        info['vel'] = velocity
        return reward, info


    def state_to_observation(self, state):
        """
        Convert state [x, y, yaw, x_dot, y_dot, yaw_dot] to
        [dx, theta, ddx, dtheta]
        """
        r = self.radius
        x, y, yaw, x_dot, y_dot, yaw_dot = state

        dx = np.sqrt(x**2 + y**2) - r
        theta = normalize_angle(np.arctan2(-x, y) + np.pi - yaw)
        ddx = x/(x**2 + y**2)**0.5*x_dot + y/(x**2 + y**2)**0.5*y_dot
        dtheta = -y/(x**2 + y**2)*x_dot + x/(x**2 + y**2)*y_dot - yaw_dot

        # May want to rescale/normalize values to each other.
        return np.array([dx, theta, ddx, dtheta])

