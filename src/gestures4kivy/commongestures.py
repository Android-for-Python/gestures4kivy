########################################################################
#
# Common Gestures
#
# Detects the common gestures for primary event, secondary event, select,
# drag, scroll, pan, page, zoom, and rotate.
#
# These gestures can be added to Kivy widgets by subclassing a
# Kivy Widget and `CommonGestures`, and then including the methods for
# the required gestures.
#
# CommonGestures methods detect gestures, and do not define behaviors.
#
# Source https://github.com/Android-for-Python/Common-Gestures-Example
#
###########################################################################


from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.metrics import Metrics
from kivy.config import Config
from kivy.utils import platform
from functools import partial
from time import time
from math import sqrt, atan, degrees

# This must be global so that the state is shared between instances
# For example, a SwipeScreen instance must know about the previous one.
PREVIOUS_PAGE_START = 0


class CommonGestures(Widget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mobile = platform == 'android' or platform == 'ios'
        if not self.mobile:
            Window.bind(on_key_down=self._modifier_key_down)
            Window.bind(on_key_up=self._modifier_key_up)

        # Gesture state
        self._CTRL = False
        self._SHIFT = False
        self._ALT = False
        self._finger_distance = 0
        self._finger_angle = 0
        self._wheel_enabled = True
        self._previous_wheel_time = 0
        self._persistent_pos = [(0, 0), (0, 0)]
        self._new_gesture()

        # Tap Sensitivity
        self._DOUBLE_TAP_TIME = Config.getint('postproc',
                                              'double_tap_time') / 1000
        if self.mobile:
            self._DOUBLE_TAP_TIME = self._DOUBLE_TAP_TIME * 2

        self._DOUBLE_TAP_DISTANCE = Config.getint('postproc',
                                                  'double_tap_distance')
        self._LONG_MOVE_THRESHOLD = self._DOUBLE_TAP_DISTANCE / 2
        self._LONG_PRESS = 0.4                 # sec, convention

        # one finger motion sensitivity
        self._MOVE_VELOCITY_SAMPLE = 0.2       # sec
        self._SWIPE_TIME = 0.3                 # sec
        if self.mobile:
            self._SWIPE_VELOCITY = 5           # inches/sec, heuristic
        else:
            self._SWIPE_VELOCITY = 6           # inches/sec, heuristic

        # two finger motion and wheel sensitivity
        self._TWO_FINGER_SWIPE_START = 1/25     # 1/Hz
        self._TWO_FINGER_SWIPE_END = 1/2        # 1/Hz
        self._WHEEL_SENSITIVITY = 1.1           # heuristic

    '''
    #####################
    # Kivy Touch Events
    #####################
    1) In the case of a RelativeLayout, the touch.pos value is not persistent.
    Because the same Touch is called twice, once with Window relative and
    once with the RelativeLayout relative values.
    The on_touch_* callbacks have the required value because of collide_point
    but only within the scope of that touch callback.

    This is an issue for gestures with persistence, for example two touches.
    So if we have a RelativeLayout we can't rely on the value in touch.pos .
    So regardless of there being a RelativeLayout, we save each touch.pos
    in self._persistent_pos[] and use that when the current value is
    required.

    2) A ModalView will inhibit touch events to this underlying Widget.
    If this Widget saw an on_touch_down() and a ModalView inhibits the partner
    on_touch_up() then this state machine will not reset.
    For single touch events, not reset, the invalid state will be 'Long Pressed'
    because this has the longest timer and this timer was not reset.
    We recover on next on_touch down() with a test for this state.
    '''

    #   touch down
    ##################
    def on_touch_down(self, touch):
        if self.collide_point(touch.x, touch.y):
            if len(self._touches) == 1 and touch.id == self._touches[0].id:
                # Filter noise from Kivy, one touch.id touches down twice
                pass
            elif platform == 'ios' and 'mouse' in str(touch.id):
                # Filter more noise from Kivy, extra mouse events
                return super().on_touch_down(touch)
            else:
                if len(self._touches) == 1 and\
                   self._gesture_state in ['Long Pressed']:
                    # Case 2) Previous on_touch_up() was not seen, reset.
                    self._touches = []
                    self._gesture_state = 'None'
                    self._single_tap_schedule = None
                    self._long_press_schedule = None
                self._touches.append(touch)

            if touch.is_mouse_scrolling:
                self._gesture_state = 'Wheel'
                x, y = self._pos_to_widget(touch.x, touch.y)
                scale = self._WHEEL_SENSITIVITY
                delta_scale = scale - 1
                if touch.button in ['scrollup', 'scrollleft']:
                    scale = 1/scale
                    delta_scale = -delta_scale
                vertical = touch.button in ['scrollup', 'scrolldown']
                horizontal = touch.button in ['scrollleft', 'scrollright']

                # Event filter
                global PREVIOUS_PAGE_START
                delta_t = touch.time_start - PREVIOUS_PAGE_START
                PREVIOUS_PAGE_START = touch.time_start
                if delta_t > self._TWO_FINGER_SWIPE_END:
                    # end with slow scroll, or other event
                    self._wheel_enabled = True

                # Page event
                if self._wheel_enabled and\
                   delta_t < self._TWO_FINGER_SWIPE_START:
                    # start with fast scroll
                    self._wheel_enabled = False
                    if horizontal:
                        self.cg_swipe_horizontal(touch,
                                                 touch.button == 'scrollright')
                        self.cgb_horizontal_page(touch,
                                                 touch.button == 'scrollright')
                    else:
                        self.cg_swipe_vertical(touch,
                                               touch.button == 'scrollup')
                        self.cgb_vertical_page(touch,
                                               touch.button == 'scrollup')

                # Scroll events
                if vertical:
                    vertical_scroll = True
                    if self._CTRL:
                        vertical_scroll = False
                        self.cg_ctrl_wheel(touch, scale, x, y)
                        self.cgb_zoom(touch, None, x, y, scale)
                    if self._SHIFT:
                        vertical_scroll = False
                        self.cg_shift_wheel(touch, scale, x, y)
                        distance = x * delta_scale
                        period = touch.time_update - self._previous_wheel_time
                        velocity = 0
                        if period:
                            velocity = distance / (period * Metrics.dpi)
                        self.cgb_pan(touch, x, y, distance, velocity)
                    if self._ALT:
                        vertical_scroll = False
                        delta_angle = -5
                        if touch.button == 'scrollup':
                            delta_angle = - delta_angle
                        self.cgb_rotate(touch, None, x, y, delta_angle)
                    if vertical_scroll:
                        self.cg_wheel(touch, scale, x, y)
                        distance = y * delta_scale
                        period = touch.time_update - self._previous_wheel_time
                        velocity = 0
                        if period:
                            velocity = distance / (period * Metrics.dpi)
                        self.cgb_scroll(touch, x, y, distance, velocity)
                elif horizontal:
                    self.cg_shift_wheel(touch, scale, x, y)
                    distance = x * delta_scale
                    period = touch.time_update - self._previous_wheel_time
                    velocity = 0
                    if period:
                        velocity = distance / (period * Metrics.dpi)
                    self.cgb_pan(touch, x, y, distance, velocity)
                self._previous_wheel_time = touch.time_update

            elif len(self._touches) == 1:
                ox, oy = self._pos_to_widget(touch.ox, touch.oy)
                self._last_x = ox
                self._last_y = oy
                self._wheel_enabled = True
                if 'button' in touch.profile and touch.button == 'right':
                    # Two finger tap or right click
                    self._gesture_state = 'Right'
                else:
                    self._gesture_state = 'Left'
                    # schedule a posssible tap
                    if not self._single_tap_schedule:
                        self._single_tap_schedule =\
                            Clock.create_trigger(partial(self._single_tap_event,
                                                        touch,
                                                        touch.x, touch.y),
                                                self._DOUBLE_TAP_TIME)
                    # schedule a posssible long press
                    if not self._long_press_schedule:
                        self._long_press_schedule = Clock.create_trigger(
                            partial(self._long_press_event,
                                    touch, touch.x, touch.y,
                                    touch.ox, touch.oy),
                            self._LONG_PRESS)
                    # Hopefully schedules both from the same timestep 
                    if self._single_tap_schedule:
                        self._single_tap_schedule()
                    if self._long_press_schedule:
                        self._long_press_schedule()

                self._persistent_pos[0] = tuple(touch.pos)
            elif len(self._touches) == 2:
                self._wheel_enabled = True
                self._gesture_state = 'Right'  # scale, or rotate
                # If two fingers it cant be a long press, swipe or tap
                self._not_long_press()
                self._not_single_tap()
                self._persistent_pos[1] = tuple(touch.pos)
                x, y = self._scale_midpoint()
                self.cg_scale_start(self._touches[0], self._touches[1], x, y)
            elif len(self._touches) == 3:
                # Another bogus Kivy event
                # Occurs on desktop pinch/spread when touchpad reports
                # the touch points and not ctrl-scroll
                td = None
                for t in self._touches:
                    if 'mouse' in str(t.id):
                        td = t
                if td:
                    self._remove_gesture(td)
                    self._persistent_pos[0] = tuple(self._touches[0].pos)
                    self._persistent_pos[1] = tuple(self._touches[1].pos)

        return super().on_touch_down(touch)

    #   touch move
    #################
    def on_touch_move(self, touch):
        if touch in self._touches and self.collide_point(touch.x, touch.y):
            # Old Android screens give noisy touch events
            # which can kill a long press.
            if (not self.mobile and (touch.dx or touch.dy)) or\
               (self.mobile and not self._long_press_schedule and
                (touch.dx or touch.dy)) or\
               (self.mobile and (abs(touch.dx) > self._LONG_MOVE_THRESHOLD or
                                 abs(touch.dy) > self._LONG_MOVE_THRESHOLD)):
                # If moving it cant be a pending long press or tap
                self._not_long_press()
                self._not_single_tap()
                # State changes
                if self._gesture_state == 'Long Pressed':
                    self._gesture_state = 'Long Press Move'
                    x, y = self._pos_to_widget(touch.ox, touch.oy)
                    self._velocity_start(touch)
                    self.cg_long_press_move_start(touch, x, y)

                elif self._gesture_state == 'Left':
                    # Moving 'Left' is a drag, or a page
                    self._gesture_state = 'Disambiguate'
                    x, y = self._pos_to_widget(touch.ox, touch.oy)
                    self._velocity_start(touch)
                    self.cg_move_start(touch, x, y)

                if self._gesture_state == 'Disambiguate' and\
                   len(self._touches) == 1:
                    self._gesture_state = 'Move'
                    # schedule a posssible swipe
                    if not self._swipe_schedule:
                        self._swipe_schedule = Clock.schedule_once(
                            partial(self._possible_swipe, touch),
                            self._SWIPE_TIME)

                if self._gesture_state in ['Right', 'Scale']:
                    if len(self._touches) <= 2:
                        indx = self._touches.index(touch)
                        self._persistent_pos[indx] = tuple(touch.pos)
                    if len(self._touches) > 1:
                        self._gesture_state = 'Scale'  # and rotate
                        finger_distance = self._scale_distance()
                        f = self._scale_angle()
                        if f >= 0:
                            finger_angle = f
                        else:  # Div zero in angle calc
                            finger_angle = self._finger_angle
                        if self._finger_distance:
                            scale = finger_distance / self._finger_distance
                            x, y = self._scale_midpoint()
                            if abs(scale) != 1:
                                self.cg_scale(self._touches[0],
                                              self._touches[1],
                                              scale, x, y)
                                self.cgb_zoom(self._touches[0],
                                              self._touches[1],
                                              x, y, scale)
                            delta_angle = self._finger_angle - finger_angle
                            # wrap around
                            if delta_angle < -170:
                                delta_angle += 180
                            if delta_angle > 170:
                                delta_angle -= 180
                            if delta_angle:
                                self.cgb_rotate(self._touches[0],
                                                self._touches[1],
                                                x, y, delta_angle)
                        self._finger_distance = finger_distance
                        self._finger_angle = finger_angle

                else:
                    x, y = self._pos_to_widget(touch.x, touch.y)
                    delta_x = x - self._last_x
                    delta_y = y - self._last_y
                    if self._gesture_state == 'Move' and self.mobile:
                        v = self._velocity_now(touch)
                        self.cg_move_to(touch, x, y, v)
                        ox, oy = self._pos_to_widget(touch.ox, touch.oy)
                        if abs(x - ox) > abs(y - oy):
                            self.cgb_pan(touch, x, y, delta_x, v)
                        else:
                            self.cgb_scroll(touch, x, y, delta_y, v)
                    elif self._gesture_state == 'Long Press Move' or\
                         (self._gesture_state == 'Move' and not self.mobile):
                        self.cg_long_press_move_to(touch, x, y,
                                                   self._velocity_now(touch))
                        self.cgb_drag(touch, x, y, delta_x, delta_y)
                    self._last_x = x
                    self._last_y = y

        return super().on_touch_move(touch)

    #   touch up
    ###############
    def on_touch_up(self, touch):
        if touch in self._touches:

            self._not_long_press()
            x, y = self._pos_to_widget(touch.x, touch.y)

            if self._gesture_state == 'Left':
                if touch.is_double_tap:
                    self._not_single_tap()
                    self.cg_double_tap(touch, x, y)
                    self.cgb_select(touch, x, y, False)
                    self._new_gesture()
                else:
                    self._remove_gesture(touch)

            elif self._gesture_state == 'Right':
                self.cg_two_finger_tap(touch, x, y)
                self.cgb_secondary(touch, x, y)
                self._new_gesture()

            elif self._gesture_state == 'Scale':
                self.cg_scale_end(self._touches[0], self._touches[1])
                self._new_gesture()

            elif self._gesture_state == 'Long Press Move':
                self.cg_long_press_move_end(touch, x, y)
                self.cgb_long_press_end(touch, x, y)
                self._new_gesture()

            elif self._gesture_state == 'Move':
                self.cg_move_end(touch, x, y)
                self._new_gesture()

            elif self._gesture_state == 'Long Pressed':
                self.cg_long_press_end(touch, x, y)
                self.cgb_long_press_end(touch, x, y)
                self._new_gesture()

            elif self._gesture_state in ['Wheel', 'Disambiguate', 'Swipe']:
                self._new_gesture()

        return super().on_touch_up(touch)

    ############################################
    # gesture utilities
    ############################################

    #   long press clock
    ########################

    def _long_press_event(self, touch, x, y, ox, oy, dt):
        self._long_press_schedule = None
        distance_squared = (x - ox) ** 2 + (y - oy) ** 2
        if distance_squared < self._DOUBLE_TAP_DISTANCE ** 2:
            x, y = self._pos_to_widget(x, y)
            self.cg_long_press(touch, x, y)
            self.cgb_select(touch, x, y, True)
            self._gesture_state = 'Long Pressed'

    def _not_long_press(self):
        if self._long_press_schedule:
            Clock.unschedule(self._long_press_schedule)
            self._long_press_schedule = None

    #   single tap clock
    #######################
    def _single_tap_event(self, touch, x, y, dt):
        if self._gesture_state == 'Left':
            if not self._long_press_schedule:
                x, y = self._pos_to_widget(x, y)
                self.cg_tap(touch, x, y)
                self.cgb_primary(touch, x, y)
                self._new_gesture()

    def _not_single_tap(self):
        if self._single_tap_schedule:
            Clock.unschedule(self._single_tap_schedule)
            self._single_tap_schedule = None

    #   swipe clock
    #######################
    def _possible_swipe(self, touch, dt):
        self._swipe_schedule = None
        x, y = touch.pos
        ox, oy = touch.opos
        period = touch.time_update - touch.time_start
        distance = sqrt((x - ox) ** 2 + (y - oy) ** 2)
        if period:
            velocity = distance / (period * Metrics.dpi)
        else:
            velocity = 0

        if velocity > self._SWIPE_VELOCITY:
            # A Swipe pre-empts a Move, so reset the Move
            wox, woy = self._pos_to_widget(ox, oy)
            self.cg_move_to(touch, wox, woy, self._velocity)
            self.cg_move_end(touch, wox, woy)
            if self.touch_horizontal(touch):
                self.cg_swipe_horizontal(touch, x-ox > 0)
                self.cgb_horizontal_page(touch, x-ox > 0)
            else:
                self.cg_swipe_vertical(touch, y-oy > 0)
                self.cgb_vertical_page(touch, y-oy > 0)
            self._new_gesture()

    def _velocity_start(self, touch):
        self._velx, self._vely = touch.opos
        self._velt = touch.time_start

    def _velocity_now(self, touch):
        period = touch.time_update - self._velt
        x, y = touch.pos
        distance = sqrt((x - self._velx) ** 2 + (y - self._vely) ** 2)
        self._velt = touch.time_update
        self._velx, self._vely = touch.pos
        if period:
            return distance / (period * Metrics.dpi)
        else:
            return 0

    #  Touch direction
    ######################
    def touch_horizontal(self, touch):
        return abs(touch.x-touch.ox) > abs(touch.y-touch.oy)

    def touch_vertical(self, touch):
        return abs(touch.y-touch.oy) > abs(touch.x-touch.ox)

    #  Two finger touch
    ######################
    def _scale_distance(self):
        x0, y0 = self._persistent_pos[0]
        x1, y1 = self._persistent_pos[1]
        return sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)

    def _scale_angle(self):
        x0, y0 = self._persistent_pos[0]
        x1, y1 = self._persistent_pos[1]
        if y0 == y1:
            return -90  # NOP
        return 90 + degrees(atan((x0 - x1) / (y0 - y1)))

    def _scale_midpoint(self):
        x0, y0 = self._persistent_pos[0]
        x1, y1 = self._persistent_pos[1]
        midx = abs(x0 - x1) / 2 + min(x0, x1)
        midy = abs(y0 - y1) / 2 + min(y0, y1)
        # convert to widget
        x = midx - self.x
        y = midy - self.y
        return x, y

    #   Every result is in the self frame
    #########################################
    def _pos_to_widget(self, x, y):
        return (x - self.x, y - self.y)

    #   gesture utilities
    ########################
    def _remove_gesture(self, touch):
        if touch and len(self._touches):
            if touch in self._touches:
                self._touches.remove(touch)

    def _new_gesture(self):
        self._touches = []
        self._long_press_schedule = None
        self._single_tap_schedule = None
        self._velocity_schedule = None
        self._swipe_schedule = None
        self._gesture_state = 'None'
        self._finger_distance = 0
        self._velocity = 0

    # Modiier key detect
    def _modifier_key_down(self, a, b, c, d, modifiers):
        command_key = platform == 'macosx' and 'meta' in modifiers
        self._linux_caps_key = platform == 'linux' and 'capslock' in modifiers
        if 'ctrl' in modifiers or command_key:
            self._CTRL = True
        elif 'shift' in modifiers:
            self._SHIFT = True
        elif 'alt' in modifiers or self._linux_caps_key:
            self._ALT = True

    def _modifier_key_up(self,a, b, c):
        self._CTRL = False
        self._SHIFT = False
        self._ALT = self._linux_caps_key

    ############################################
    # User Events
    # define some subset in the derived class
    ############################################

    #
    # Common Gestures Behavioral API
    #
    # primary, secondary, select, drag, scroll, pan, page, zoom, rotate
    #
    # focus_x, focus_y are locations in widget coordinates, representing
    # the location of a cursor, finger, or mid point between two fingers.

    # Click, tap, or deep press events
    def cgb_primary(self, touch, focus_x, focus_y):
        pass

    def cgb_secondary(self, touch, focus_x, focus_y):
        pass

    def cgb_select(self, touch, focus_x, focus_y, long_press):
        # If long_press == True
        # Then on a mobile device set visual feedback.
        pass

    def cgb_long_press_end(self, touch, focus_x, focus_y):
        # Only called if cgb_select() long_press argument was True
        # On mobile device reset visual feedback.
        pass

    def cgb_drag(self, touch, focus_x, focus_y, delta_x, delta_y):
        pass

    # Scroll
    def cgb_scroll(self, touch, focus_x, focus_y, delta_y, velocity):
        # do not use in combination with cgb_vertical_page()
        pass

    def cgb_pan(self, touch, focus_x, focus_y, delta_x, velocity):
        # do not use in combination with cgb_horizontal_page()
        pass

    # Page
    def cgb_vertical_page(self, touch, bottom_to_top):
        # do not use in combination with cgb_scroll()
        pass

    def cgb_horizontal_page(self, touch, left_to_right):
        # do not use in combination with cgb_pan()
        pass

    # Zoom
    def cgb_zoom(self, touch0, touch1, focus_x, focus_y, delta_scale):
        # touch1 may be None
        pass

    # Rotate
    def cgb_rotate(self, touch0, touch1, focus_x, focus_y, delta_angle):
        # touch1 may be None
        pass

    #
    # Classic Common Gestures API
    # (will be depreciated)

    # Tap, Double Tap, and Long Press
    def cg_tap(self, touch, x, y):
        pass

    def cg_two_finger_tap(self, touch, x, y):
        # also a mouse right click, desktop only
        pass

    def cg_double_tap(self, touch, x, y):
        pass

    def cg_long_press(self, touch, x, y):
        pass

    def cg_long_press_end(self, touch, x, y):
        pass

    # Move
    def cg_move_start(self, touch, x, y):
        pass

    def cg_move_to(self, touch, x, y, velocity):
        # velocity is average of the last self._MOVE_VELOCITY_SAMPLE sec,
        # in inches/sec  :)
        pass

    def cg_move_end(self, touch, x, y):
        pass

    # Move preceded by a long press.
    # cg_long_press() called first, cg_long_press_end() is not called
    def cg_long_press_move_start(self, touch, x, y):
        pass

    def cg_long_press_move_to(self, touch, x, y, velocity):
        # velocity is average of the last self._MOVE_VELOCITY_SAMPLE,
        # in inches/sec  :)
        pass

    def cg_long_press_move_end(self, touch, x, y):
        pass

    # a fast move
    def cg_swipe_horizontal(self, touch, left_to_right):
        pass

    def cg_swipe_vertical(self, touch, bottom_to_top):
        pass

    # pinch/spread
    def cg_scale_start(self, touch0, touch1, x, y):
        pass

    def cg_scale(self, touch0, touch1, scale, x, y):
        pass

    def cg_scale_end(self, touch0, touch1):
        pass

    # Mouse Wheel, or Windows touch pad two finger vertical move

    # a common shortcut for scroll
    def cg_wheel(self, touch, scale, x, y):
        pass

    # a common shortcut for pinch/spread
    def cg_ctrl_wheel(self, touch, scale, x, y):
        pass

    # a common shortcut for horizontal scroll
    def cg_shift_wheel(self, touch, scale, x, y):
        pass

