Gestures for Kivy
=================

*Detect common touch gestures in Kivy apps*

**Now with an all new, simpler, input device independent api. The classic api is still implemented, but will be depreciated.**

## Install

Desktop OS:
```
pip3 install gestures4kivy
```

Android:

Add `gestures4kivy` to `buildozer.spec` requirements.

iOS:
```
toolchain pip3 install gestures4kivy
```

## Usage

Import using:
```
from gestures4kivy import CommonGestures
```

The following is required at the top of the app's main.py to disable Kivy's multitouch emulation feature:
```
Config.set('input', 'mouse', 'mouse, disable_multitouch')
```

The class `CommonGestures` detects the common gestures for primary event, secondary event, select, drag, scroll, pan, zoom, rotate, and page. These are reported in an input device independent way, see below for details.

Each gesture results in a callback, which defines the required action. These gestures can be **added** to Kivy widgets by subclassing a Kivy Widget and `CommonGestures`, and then including the methods for the required gestures.

A minimal example is `SwipeScreen`, where we implement one callback method:
```python
# A swipe sensitive Screen

class SwipeScreen(Screen, CommonGestures):

    def cgb_horizontal_page(self, touch, right):
        # here we add the user defined behavior for the gesture
	# this method controls the ScreenManager in response to a swipe
        App.get_running_app().swipe_screen(right)
```
Where the `swipe_screen()` method configures the screen manager. This is fully implemented along with the other gestures [here](https://github.com/Android-for-Python/Common-Gestures-Example).

`CommonGestures` callback methods detect gestures; they do not implement behaviors.

## API

`CommonGestures` implements the following gesture callbacks, a child class may use any subset. The callbacks are initiated by input device events as described below.

Callback arguments report the original Kivy touch event(s), the focus of a gesture (the location of a cursor, finger, or mid point between two fingers) in Widget coordinates, and parameters representing the change described by a gesture.

Gesture sensitivities can be adjusted by setting values in the class that inherits from `CommonGestures`. These values are contained in the `self._SOME_NAME` variables declared in the `__init__()` method of `CommonGestures`. 

For backwards compatibility a legacy api is implemented (method names begin with 'cg_' not 'cgb_'). The legacy api will eventually be depreciated, and is not documented. 

### Primary event
```python
    def cgb_primary(self, touch, focus_x, focus_y):
        pass
```
 - Mouse - Left button click
 - Touchpad - one finger tap 
 - Mobile  - one finger tap

### Secondary event
```python
    def cgb_secondary(self, touch, focus_x, focus_y):
        pass
```
 - Mouse - Right button click
 - Touchpad - two finger tap 
 - Mobile  - two finger tap 

### Select
```python
    def cgb_select(self, touch, focus_x, focus_y, long_press):
        # If long_press == True
        # Then on a mobile device set visual feedback.
        pass

    def cgb_long_press_end(self, touch, focus_x, focus_y):
        # Only called if cgb_select() long_press argument was True
        # On mobile device reset visual feedback.
        pass
```
 - Mouse - double click
 - Touchpad - double tap, or long deep press  
 - Mobile  - double tap, long press

`cgb_long_press_end()` is called when a user raises a finger after a long press. This may occur after a select or after a drag initiated by a long press.

### Drag
```python
    def cgb_drag(self, touch, focus_x, focus_y, delta_x, delta_y):
        pass
```
 - Mouse - hold mouse button and move mouse   
 - Touchpad - deep press (or one and a half taps) and move finger
 - Mobile  - long press (provide visual feeback) and move finger

### Scroll
```python
    def cgb_scroll(self, touch, focus_x, focus_y, delta_y, velocity):
        pass
```
 - Mouse - rotate scroll wheel
 - Touchpad - two finger vertical motion
 - Mobile  - one finger vertical motion

A scroll gesture is very similar to a vertical page gesture, using the two in the same layout may be a challenge particularly on a touchpad.

### Pan
```python
    def cgb_pan(self, touch, focus_x, focus_y, delta_x, velocity):
        pass
```
 - Mouse - Press Shift key, and rotate scroll wheel
 - Touchpad - two finger horizontal motion
 - Mobile  - one finger horizontal motion

A pan gesture is very similar to a horizontal page gesture, using the two in the same layout may be a challenge particularly on a touchpad.

### Zoom
```python
    def cgb_zoom(self, touch0, touch1, focus_x, focus_y, delta_scale):
        pass
```
 - Mouse - Press Ctrl key, and rotate scroll wheel
 - Touchpad - two finger pinch/spread
 - Mobile  - two finger  pinch/spread

On a Mac, the Command key is the convention for zoom, either Command or Ctrl can be used.

The touch1 parameter may be `None`.

### Rotate
```python
    def cgb_rotate(self, touch0, touch1, focus_x, focus_y, delta_angle):
        pass
```
 - Mouse - Press Alt key, and rotate scroll wheel
 - Touchpad - Press Alt key, plus two finger vertical motion 
 - Mobile  - two finger twist

On a Mac, Alt is the key labeled Option

On Linux, Alt is not available as a modifier, use the sequence CapsLock,Scroll,CapsLock.

The touch1 parameter may be `None`.

### Horizontal Page
```python
    def cgb_horizontal_page(self, touch, left_to_right):
        pass
```
 - Mouse - hold mouse button and fast horizontal move mouse
 - Touchpad - fast two finger horizontal motion 
 - Mobile  - fast one finger horizontal motion

See [Pan](#pan) for possible interactions.

### Vertical Page
```python
    def cgb_vertical_page(self, touch, bottom_to_top):
        pass
```
 - Mouse - hold mouse button and fast vertical move mouse
 - Touchpad - fast two finger vertical motion 
 - Mobile  - fast one finger vertical motion

See [Scroll](#scroll) for possible interactions.


## Known Issues:

### Kivy Multitouch

Kivy multitouch must be disabled. A ctrl-scroll with a mouse (the common convention for zoom), a pinch-spread with a touchpad, a right click, or a two finger tap will place an orange dot on the screen and inhibit zoom functionality.

```python
Config.set('input', 'mouse', 'mouse, disable_multitouch')
```

### Mac

Trackpap two finger pinch/spread is not available. Use `Command` or `Ctrl` and `Scroll`. This is apparently an SDl2 issue.

### Linux

Alt is not a keyboard modifier on Linux. For the rotate operation set CapsLock, scroll, and unset CapsLock.



