# coding: utf-8

import yaml

import numpy as np

import gym

# from rllab.envs.base import Env, Step
# from rllab.misc import logger
# from rllab.spaces import Box

from gym_gmmcar.envs.model.model import BrushTireModel, LinearTireModel
from gym_gmmcar.envs.renderer import _Renderer


class VehicleEnv(gym.Env):
    """
    Simulation environment for a FFAST RC car.
    """

    _MIN_VELOCITY = 0.0
    _MAX_VELOCITY = 10.0
    _MAX_STEER_ANGLE = np.pi / 6
    _HORIZON_LENGTH = 100

    metadata = {'render.modes': ['human']}

    def __init__(
            self,
            target_velocity=1.0,
            dt=0.035,
            model_type='BrushTireModel',
            robot_type='RCCar',
            mu_s=1.37,
            mu_k=1.96
    ):
        super().__init__()
        """
        Initialize environment parameters.
        """
        # Load estimated parameters for robot
        if robot_type == 'RCCar':
            stream = open(r'./gym_gmmcar/envs/model/model_params/rccar.yml','r')
            #stream = open(r'./envs/model/model_params/rccar.yml', 'r')
            self._params = yaml.load(stream, Loader=yaml.FullLoader)
        elif robot_type == 'MRZR':
            stream = open(r'./gym_gmmcar/envs/model/model_params/mrzr.yml','r')
            #stream = open(r'./envs/model/model_params/mrzr.yml', 'r')
            self._params = yaml.load(stream, Loader=yaml.FullLoader)
        else:
            raise ValueError('Unrecognized robot type')

        # Instantiate vehicle model for simulation
        self._state = None
        self._action = None
        self.target_velocity = target_velocity
        if model_type == 'BrushTireModel':
            self._model = BrushTireModel(self._params, mu_s, mu_k)
        elif model_type == 'LinearTireModel':
            self._model = LinearTireModel(self._params, mu_s, mu_k)
        else:
            raise ValueError('Invalid vehicle model type')

        self.action_space = gym.spaces.Box(
            low=np.array([VehicleEnv._MIN_VELOCITY, -VehicleEnv._MAX_STEER_ANGLE]),
            high=np.array([VehicleEnv._MAX_VELOCITY, VehicleEnv._MAX_STEER_ANGLE]))

        self.observation_space = gym.spaces.Box(low=-np.inf, high=np.inf, shape=(6,))

        # Time between each simulation iteration
        # Note: dt is measured to be 0.035, but we train with longer dt
        #       for more stability in commanded actions.
        self._dt = dt

        # Instantiates object handling simulation renderings
        self._renderer = None


    # @property
    # def observation_space(self):
    #     return Box(low=-np.inf, high=np.inf, shape=(6,))
    #
    #
    # @property
    # def action_space(self):
    #     low = np.array([VehicleEnv._MIN_VELOCITY,
    #         -VehicleEnv._MAX_STEER_ANGLE])
    #     high = np.array([VehicleEnv._MAX_VELOCITY,
    #         VehicleEnv._MAX_STEER_ANGLE])
    #     return Box(low=low, high=high)
    #
    #
    # @property
    # def horizon(self):
    #     return VehicleEnv._HORIZON_LENGTH


    def reset(self):
        """
        Reset environment back to original state.
        """
        self._action = None
        self._state = self.get_initial_state
        self._currentstep = 0
        observation = self.state_to_observation(self._state)

        # Reset renderer if available
        if self._renderer is not None:
            self._renderer.reset()

        return observation


    def step(self, action):
        """
        Move one iteration forward in simulation.
        """
        # Place limits on action based on mechanical constraints
        action_min = [VehicleEnv._MIN_VELOCITY, -VehicleEnv._MAX_STEER_ANGLE]
        action_max = [VehicleEnv._MAX_VELOCITY, VehicleEnv._MAX_STEER_ANGLE]
        action = np.clip(action, a_min=action_min, a_max=action_max)

        self._action = action
        nextstate = self._model.state_transition(self._state, action,
                self._dt)
        self._state = nextstate
        reward, info = self.get_reward(nextstate, action)
        observation = self.state_to_observation(nextstate)
        self._currentstep += 1
        # done = False
        done = self._currentstep == VehicleEnv._HORIZON_LENGTH
        return nextstate, reward, done, info
        # return Step(observation=observation, reward=reward, done=False,
        #         dist=info['dist'], vel=info['vel'], kappa=self._model.kappa)


    def render(self):
        """
        Render simulation environment.
        """
        if self._renderer == None:
            self._renderer = _Renderer(self._params,
                    self.__class__.__name__)
        self._renderer.update(self._state, self._action)


    def log_diagnostics(self, paths):
        """
        Log extra information per iteration based on collected paths.
        """
        dists = []
        vels = []
        kappas = []
        for path in paths:
            dists.append(path['env_infos']['dist'])
            vels.append(path['env_infos']['vel'])
            kappas.append(path['env_infos']['kappa'])
        dists = np.abs(dists)
        vels = np.abs(vels)
        kappas = np.abs(kappas)

        logger.record_tabular('AverageAbsDistance', np.mean(dists))
        logger.record_tabular('AverageAbsVelocity', np.mean(vels))
        logger.record_tabular('MaxAbsDistance', np.max(dists))
        logger.record_tabular('MaxAbsVelocity', np.max(vels))
        logger.record_tabular('AverageKappa', np.mean(kappas))
        logger.record_tabular('MaxKappa', np.max(kappas))


    @property
    def get_initial_state(self):
        """
        Get initial state of car when simulation is reset.
        """
        raise NotImplementedError


    def get_reward(self, state, action):
        """
        Reward function definition. Returns reward, a scalar, and info, a
        dictionary that must contain the keys 'dist' (closest distance to
        trajectory) and 'vel' (current velocity).
        """
        raise NotImplementedError


    def state_to_observation(self, state):
        """
        Prepare state to be read as input to neural network.
        """
        raise NotImplementedError

