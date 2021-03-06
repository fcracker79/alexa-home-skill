import logging
import threading
import time

from chattyraspi.client import ThermostatMode
import queue
import RPi.GPIO as GPIO

_LOGGER = logging.getLogger('servomotor')

_MOTOR_PINS = (12, 16, 18, 22)
_CCW_STEP = (0x01, 0x02, 0x04, 0x08)
_CW_STEP = (0x08, 0x04, 0x02, 0x01)


class StepperThread(threading.Thread):
    def __init__(self, q: queue.Queue):
        super(StepperThread, self).__init__(name='StepperThread', daemon=True)
        self._q = q

    def run(self):
        while True:
            direction, degree = self._q.get()
            _remote_set_degree(direction, degree)


def _get_queue():
    if _get_queue.queue is None:
        _get_queue.queue = queue.Queue()
    return _get_queue.queue


_get_queue.queue = queue.Queue()


def init_camera():
    _LOGGER.info('GPIO.setmode(GPIO.BOARD)')
    # noinspection PyUnresolvedReferences
    GPIO.setmode(GPIO.BOARD)
    # use PHYSICAL GPIO Numbering
    for pin in _MOTOR_PINS:
        # noinspection PyUnresolvedReferences
        GPIO.setup(pin, GPIO.OUT)
    stepper_thread = StepperThread(_get_queue())
    stepper_thread.start()
    set_degree.current_degree = 0


def start_camera():
    set_degree(0)


def stop_camera():
    _LOGGER.info('GPIO.cleanup()')
    # noinspection PyUnresolvedReferences
    GPIO.cleanup()


def set_degree(degree: float):
    delta_degree, direction = degree - set_degree.current_degree, 1
    if delta_degree < 0:
        delta_degree, direction = -delta_degree, -1
    _get_queue().put((direction, delta_degree))
    set_degree.current_degree = degree


def _remote_set_degree(direction: int, degree: float):
    _move_steps(direction, 3, _map_angle(int(min(360.0, max(0.0, degree))), 0, 360, 0, 512))


def set_mode(mode: ThermostatMode):
    _LOGGER.info('TODO IMPLEMENT MODE for %s', mode)
    pass


def _map_angle(value: int, from_low: int, from_high: int, to_low: int, to_high: int) -> int:
    return (to_high - to_low) * (value - from_low) // (from_high - from_low) + to_low


def _move_one_period(direction: int, ms: int) -> None:
    _LOGGER.info('Move one period(direction=%s, ms=%s', direction, ms)
    for j in range(4):
        for i in range(4):
            if direction == 1:
                _LOGGER.info('GPIO.output(_MOTOR_PINS[i], GPIO.HIGH if _CCW_STEP[j] == (1 << i) else GPIO.LOW)')
                # noinspection PyUnresolvedReferences
                GPIO.output(_MOTOR_PINS[i], GPIO.HIGH if _CCW_STEP[j] == (1 << i) else GPIO.LOW)
            else:
                _LOGGER.info('GPIO.output(_MOTOR_PINS[i], GPIO.HIGH if _CW_STEP[j] == (1 << i) else GPIO.LOW)')
                # noinspection PyUnresolvedReferences
                GPIO.output(_MOTOR_PINS[i], GPIO.HIGH if _CW_STEP[j] == (1 << i) else GPIO.LOW)
        _LOGGER.info("Step cycle!")
        if ms < 3:
            ms = 3
        time.sleep(ms * 0.001)


def _move_steps(direction: int, ms: int, steps: int):
    for i in range(steps):
        _move_one_period(direction, ms)


def motor_stop():
    for i in range(4):
        _LOGGER.info('GPIO.output(_MOTOR_PINS[%s], GPIO.LOW)', i)
        # noinspection PyUnresolvedReferences
        GPIO.output(_MOTOR_PINS[i], GPIO.LOW)


set_degree.current_degree = 0