Gestures for Kivy
=================

*Detect common touch gestures in Kivy apps*

## Install

For a desktop OS:
```
pip3 install gestures4kivy
```

For Android:

Add `gestures4kivy` to `buildozer.spec` requirements.

Import using:
```
from gestures4kivy import CommonGestures
```

This is required at the top of the app's main.py to disable a Kivy feature:
```
if platform not in ['android', 'ios]:
    Config.set('input', 'mouse', 'mouse, disable_multitouch')
```

## Behavior

The class `CommonGestures` detects the common gestures for `scale`, `move`, `swipe`, `long press move`, `long press`, `tap`, and `double tap`. A `long press move` is initiated with a `long press`. On the desktop the class also detects `mouse wheel` and the touchpad equivalent `two finger move`. 

Originally designed for use on Android, the gestures can be used on any Kivy supported platform and input device.

In addition, for platforms with a mouse scroll wheel the usual conventions are detected: `scroll wheel` can be used for vertical scroll, `shift-scroll wheel` can be used for horizontal scroll, and `ctrl-scroll wheel` can be used for zoom. Also on touch pads, vertical or horizontal two finger movement emulates a mouse scroll wheel. In addition a mouse right click, or pad two finger tap is detected.

Each gesture results in a callback, which will contain the required action. These gestures can be **added** to Kivy widgets by subclassing a Kivy Widget and `CommonGestures`, and then including the methods for the required gestures.

A minimal example is `SwipeScreen`, where we implement one callback method:
```
### A swipe sensitive Screen
class SwipeScreen(Screen, CommonGestures):

    def cg_swipe_horizontal(self, touch, right):
        # here we add the user defined behavior for the gesture
	# this method controls the ScreenManager in response to a swipe
        App.get_running_app().swipe_screen(right)
```
Where the `swipe_screen()` method configures the screen manager. This is fully implemented along with the other gestures [here](https://github.com/Android-for-Python/Common-Gestures-Example).

`CommonGestures` callback methods detect gestures, they do not define behaviors.

## API

`CommonGestures` implements these gesture callbacks, a child class may use any subset:

```
    ############################################
    # User Events
    # define some subset in the derived class
    ############################################

    ############# Tap and Long Press
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

    ############## Move
    def cg_move_start(self, touch, x, y):
        pass

    def cg_move_to(self, touch, x, y, velocity):
        # velocity is average of the last 0.2 sec, in inches/sec  :)
        pass

    def cg_move_end(self, touch, x, y):
        pass

    ############### Move preceded by a long press
    def cg_long_press_move_start(self, touch, x, y):
        pass

    def cg_long_press_move_to(self, touch, x, y, velocity):
        # velocity is average of the last 0.2 sec, in inches/sec  :)
        pass

    def cg_long_press_move_end(self, touch, x, y):
        pass

    ############### fast horizontal movement
    def cg_swipe_horizontal(self, touch, left_to_right):
        pass

    def cg_swipe_vertical(self, touch, bottom_to_top):
        pass

    ############### pinch/spread
    def cg_scale_start(self, touch0, touch1, x, y):
        pass

    def cg_scale(self, touch0, touch1, scale, x, y):
        pass

    def cg_scale_end(self, touch0, touch1):
        pass

    ############# Mouse Wheel, or Windows touch pad two finger vertical move
    
    ############# a common shortcut for scroll
    def cg_wheel(self, touch, scale, x, y):
        pass

    ############# a common shortcut for pinch/spread
    def cg_ctrl_wheel(self, touch, scale, x, y):
        pass

    ############# a common shortcut for horizontal scroll
    def cg_shift_wheel(self, touch, scale, x, y):
        pass
	
```

## Hardware Considerations

#### Mouse

As usual, `Move`, `Long Press Move`, `Swipe`, and `Long Press` are initiated with press the left mouse button, and end when the press ends.

The right mouse button generates a `cg_two_finger_tap()` callback.

Mouse wheel movement generates t `cg_wheel()`, `cg_shift_wheel()`, and `cg_ctrl_wheel()` callbacks.

#### Touch Pad

As usual, `Move`, `Long Press Move`, `Swipe`, and `Long Press` are initiated with **'one and a half taps'**, or a press on the bottom left corner of the trackpad.

A `Swipe` callback is also generated by a two finger horizonal move. A two finger vertical move initaiates a scroll callback.

A two finger tap generates a `cg_two_finger_tap()` callback.

Two finger pinch/spread uses the cursor location as focus. Note that the cursor may move significantly during a pinch/spread.

## OS Considerations

### Android

Pinch/spread focus is the mid point between two fingers. The mouse wheel callbacks are not generated.

Mobile users are not used to a double tap, so use long press. If you do use double tap, the Kivy default detection time is too short for reliable detection of finger taps.
You can change this from the default 250mS, for example:
```
    from kivy.config import Config
    Config.set('postproc', 'double_tap_time', '500')
```

### Windows

On some touchpads pinch/spread will not be detected the if 'mouse, disable_multitouch' feature is not disabled.

Some touch pads report a pinch/spread as a finger movement `cg_scale()`, and some detect the gesture internally and report it as a `cg_ctrl_wheel()`. The safe thing to do is handle both cases in an application.

A two finger horizontal move is inhibited for 2 second following the previous horizontal move [https://github.com/kivy/kivy/issues/7707](https://github.com/kivy/kivy/issues/7707).

### Mac

Two finger pinch/spread is not available. Use `Command` and `vertical scroll`.

Force Click (deep press) is reported as a long press, this is a happy coincidence and not by design.

See [https://github.com/kivy/kivy/issues/7708](https://github.com/kivy/kivy/issues/7708).

### iOS

All screen gestures work.

### Linux

Tested on Raspberry Desktop. Using a touchpad the behavior is non-deterministic, and cannot be used. Use a mouse.

Using a mouse on 'Buster' the `[input]` section in `~/.kivy/config.ini` should contain only one entry:
```
[input]
mouse = mouse
```
Using 'Bullseye' the Kivy default config is good when using a mouse.

## Acknowledgement

A big thank you to Elliot for his analysis, constructive suggestions, and testing.