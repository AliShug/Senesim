from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from Box2D import *

from senesim.config import *

class TendonController(object):
    '''Simple controller tracks length limits.'''
    def __init__(self, elastic, label = 'Unnamed', max_force=5000, max_speed=50):
        self.elastic = elastic
        self.limit = 100
        self.target = 0
        self.position = 0
        self.rest = elastic.restLength
        self.label = label
        self.subscribers = []
        self.maxForce = max_force
        self.maxSpeed = max_speed

    def setLimit(self, limit):
        self.limit = limit

    def getLimit(self):
        return self.limit

    def setTarget(self, target):
        self.target = target
        for f in self.subscribers:
            f()

    def getTarget(self):
        return self.target

    def getPosition(self):
        '''Returns the actual feed position of the 'motor'.'''
        return self.position

    def reelOut(self, delta_t):
        '''Settles on a new position at the limit of the motor's force output'''
        # # First, increase our upper bound until the forces drop below the max
        # n = 0
        # tmp_pos = self.position * 2
        # print('starting, current pos {0:.2f}'.format(self.position))
        # while n < 20:
        #     self.elastic.setRestLength(self.rest + tmp_pos)
        #     internal_force = self.elastic.getInternalForce(delta_t)
        #     if internal_force < self.maxForce:
        #         break
        #     else:
        #         print('force {0:.2f}'.format(internal_force))
        #         tmp_pos *= 2
        #     n += 1
        #     print('pos {0:.2f}'.format(tmp_pos))
        # # tmp_pos is now our high bound, and tmp_pos/2 the low bound.
        # # Bisection search finds the point where the internal force ~=
        # # the maximum output force. (stops with epsilon < 0.001)

        # Use the maximum limit as a bound
        n = 0
        low = self.position
        high = self.limit
        while n < 20:
            mid = (low + high) / 2
            self.elastic.setRestLength(self.rest + mid)
            internal_force = self.elastic.getInternalForce(delta_t)
            if abs(internal_force - self.maxForce) < 0.001:
                break
            elif internal_force < self.maxForce:
                high = mid
            else:
                low = mid
            n += 1
        self.position = mid

    def update(self, delta_t):
        '''Reel in or out up to the maximum speed and force'''
        # If the force exceeds the maximum, we reel out until it doesn't.
        # Otherwise, we move towards the setpoint until we reach either the
        # maximum speed or the maximum force.
        # Basically, move towards goal by up to maxSpeed, then extend until the
        # forces are within range.

        if self.elastic.getInternalForce(delta_t) > self.maxForce:
            # Reel out on extreme forces - target position doesn't matter here
            self.reelOut(delta_t)
        else:
            # Cap movement to maximum speed, then find the
            step_speed = self.maxSpeed * delta_t
            if self.target < self.position - step_speed:
                capped_target = self.position - step_speed
            elif self.target > self.position + step_speed:
                capped_target = self.position + step_speed
            else:
                capped_target = self.target
            self.elastic.setRestLength(self.rest + capped_target)
            if self.elastic.getInternalForce(delta_t) < self.maxForce:
                self.position = capped_target
            else:
                # Reel out until the forces are within range
                self.reelOut(delta_t)

    def subscribeChange(self, function):
        self.subscribers.append(function)


class CoupledTendonController(object):
    '''Coupled controller unifies control of two tendons (variable length
    elastics), treating one as 'extensor' and the other as 'flexor'.'''
    def __init__(self, extensor_controller, flexor_controller):
        # Tendon controllers
        self.flexor = flexor_controller
        self.extensor = extensor_controller
        self.target = 0
        self.subscribers = []

    def setTarget(self, target):
        '''Target between -1 and 1'''
        if target > 1:
            target = 1
        elif target < -1:
            target = -1
        self.update()
        self.target = target
        for f in self.subscribers:
            f()

    def getTarget(self):
        return self.target

    def update(self):
        self.flexor.setTarget(self.flexor.limit * self.target)
        self.extensor.setTarget(self.extensor.limit * (-self.target))

    def subscribeChange(self, function):
        self.subscribers.append(function)
