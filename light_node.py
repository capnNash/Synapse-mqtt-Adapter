# (c) Copyright 2014-2017, Synapse Wireless, Inc.
"""SN087 Demo Script
This script automatically sets the dimming level (0-10V output) on startup to 80%.
It is understood that generally humans have trouble distinguishing from 80-100%
At this point after the inital setting a remote command to set the dimming level is required.
"""

from atmega128rfa1_timers import *
from synapse.SM220 import GPIO_C5, GPIO_D1, GPIO_D3, GPIO_F1, GPIO_F2

# The PWM frequency has been carefully selected so that OCR
# 0-100 matches the 0-100% output for 0-10 volts. Any changes
# to the frequency must ensure the PWM duty cycle does not
# exceed 75.75%



# Constants
CPU_F = 16000000
PWM_FREQUENCY = 121212  # Hz (shouldn't need to change this)
ICR = CPU_F / PWM_FREQUENCY

DIM_RAMP_SPEED = 4
NO_COMMUNICATION_TIMEOUT = 15 * 60
DEFAULT_DIM_LEVEL = 80

# I/Os
LED_GREEN = GPIO_F1
LED_RED = GPIO_F2
LVLA = GPIO_D1
PWMA = GPIO_D3
BOOST_EN = GPIO_C5

# ADCs
ADC_CHN_33 = 2
ADC_CHN_12 = 0
ADC_CHN_DIM = 1

# Application NV parameters
NV_GROUP_ID = 128
WILDCARD_GROUP = 0xFFFF

# Global variables
dim_level = 0
group_id = 0
keep_alive_timer = NO_COMMUNICATION_TIMEOUT

# Self-test parameters
TEST_3V3_RAIL = 892
TEST_12V_RAIL = 865


@setHook(HOOK_STARTUP)
def on_startup():
    """Initialization."""
    global group_id

    # Configure LEDs
    setPinDir(LED_GREEN, True)
    writePin(LED_GREEN, False)
    setPinDir(LED_RED, True)
    writePin(LED_RED, True)

    # Configure power supply
    setPinDir(BOOST_EN, True)
    writePin(BOOST_EN, True)

    # Initialize dimmer
    setPinDir(PWMA, True)
    writePin(PWMA, True)
    setPinDir(LVLA, True)
    writePin(LVLA, False)

    init_dim_control()
    set_dim_level(DEFAULT_DIM_LEVEL)

    # Initialize application settings
    setting = loadNvParam(NV_GROUP_ID)
    if setting != None:
        group_id = setting


@setHook(HOOK_1S)
def timer_1s():
    """One second timer hook to keep track of communication."""
    global keep_alive_timer

    if keep_alive_timer > 0:
        keep_alive_timer -= 1
        if keep_alive_timer == 0:
            _dim_level(DEFAULT_DIM_LEVEL)
            led_red()


def init_dim_control():
    """Initializes the dimming control peripherals."""
    # Setup TMR1 for 16-bit PWM
    timer_init(TMR1, WGM_FASTPWM16_TOP_ICR, CLK_FOSC, ICR)
    set_tmr_output(TMR1, OCRxA, TMR_OUTP_CLR)


def set_dim_level(level):
    """Sets the dim level.
    :param int level: 0-100"""
    callback('rpcSuccess','get_dim_callback')
    reset_keep_alive()
    _dim_level(level)

def get_dim_callback():
    """Returns the dim level.
    :return int dim level: 0-100"""
    global dim_level
    return dim_level

def get_dim_level():
    """Returns the dim level.
    :return int dim level: 0-100"""
    callback('rpcSuccess','get_dim_callback')
    mcastRpc(1,3,'get_dim',dim_level)
    global dim_level
    return dim_level


def group_dim_level(group, level):
    """Sets the dim level for all lights in the group.
    :param int: group_id
    :param1 int level: 0-100"""
    global group_id

    if is_my_group(group):
        reset_keep_alive()
        _dim_level(level)


def _dim_level(level):
    """Sets the dim level.
    :param int level: 0-100"""
    global dim_level

    # Control the ramp up or down to specified dim level
    while level != dim_level:
        if dim_level < level:
            dim_level += 1
        else:
            dim_level -= 1

        # Control the ramp rate
        delay_ms(DIM_RAMP_SPEED)
        set_tmr_ocr(TMR1, OCRxA, dim_level)


def set_group(group):
    """Sets the group this light belongs to
    :param int: group_id"""
    global group_id

    group_id = group
    saveNvParam(NV_GROUP_ID, group_id)


def is_my_group(group):
    """Check to see if we belong to the group specified
    :param int: group_id
    :return bool this node is part of the group"""
    global group_id

    return group == WILDCARD_GROUP or group == group_id


def led_green():
    """Sets the on board led to green"""
    writePin(LED_RED, True)
    writePin(LED_GREEN, False)


def led_red():
    """Sets the on board led to red"""
    writePin(LED_RED, False)
    writePin(LED_GREEN, True)


def reset_keep_alive():
    """Resets the communication timeout counter"""
    global keep_alive_timer

    keep_alive_timer = NO_COMMUNICATION_TIMEOUT
    led_green()


def sts_get_dim_level():
    """Snap Thing Services helper function to get dimmer level"""
    return str(get_dim_level())


def measure_dim_output():
    """Measure output voltage level 0-100%
    :return int dim level output: 0-100"""
    dim_output = readAdc(ADC_CHN_DIM)
    return dim_output / 7 - dim_output / 240


def test_rail_output(target, actual, tolerance):
    """Measure voltage rail tolerance
    :param int target voltage ticks
    :param int measured voltage ticks
    :param int tolerance in percent
    :return bool passing status"""
    if actual < target - target / (100 / tolerance) or actual > target + target / (100 / tolerance):
        return False
    return True


def delay_ms(time_ms):
    """Blocking delay in milliseconds
    :param int: time in milliseconds"""
    for i in xrange(0, time_ms):
        pulsePin(-1, -1000, False)


def abs(value):
    """Return the absolute value of a given number
    :param int: value to convert to absolute
    :return int: absolute value"""
    if value < 0:
        return -value
    else:
        return value


      

def run_self_test():
    """Performs a quick self test of voltage rails and dimming output,
    :return bool passed self-test"""
    tolerance = 10
    voltage_3v3 = readAdc(ADC_CHN_33)
    if not test_rail_output(TEST_3V3_RAIL, voltage_3v3, tolerance):
        print "3.3V Fail"
        return False

    voltage_12v = readAdc(ADC_CHN_12)
    if not test_rail_output(TEST_12V_RAIL, voltage_12v, tolerance):
        print "12V Fail"
        return False

    # Test output in 10% increments from 0-100%
    for dim_output in xrange(0, 101, 10):
        set_dim_level(dim_output)
        delay_ms(20)
        if abs(dim_output - measure_dim_output()) > tolerance:
            print dim_output, '% DIM Fail'
            return False

    return True

