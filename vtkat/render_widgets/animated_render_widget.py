from threading import Lock
from time import time

from .common_render_widget import CommonRenderWidget


class AnimatedRenderWidget(CommonRenderWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.playing_animation = False
        self._animation_lock = Lock()
        self._animation_frame = 0
        self._animation_last_time = 0
        self._animation_total_frames = 30
        self._animation_fps = 30
        self._animation_timer = self.render_interactor.CreateRepeatingTimer(500)
        self.render_interactor.AddObserver("TimerEvent", self._animation_callback)

    def start_animation(self, fps=None, frames=None):
        if isinstance(fps, int | float):
            self._animation_fps = fps
        
        if isinstance(frames, int):
            self._animation_total_frames = frames

        if self.playing_animation:
            return

        self.playing_animation = True

    def stop_animation(self):
        if not self.playing_animation:
            return

        if self._animation_timer is None:
            return

        self.playing_animation = False
    
    def toggle_animation(self):
        if self.playing_animation:
            self.stop_animation()
        else:
            self.start_animation()

    def _animation_callback(self, obj, event):
        """
        Common function with controls that are meaningfull to
        all kinds of animations.
        """

        if not self.playing_animation:
            return

        # Wait the rendering of the last frame
        # before starting a new one
        if self._animation_lock.locked():
            return

        # Only needed because vtk CreateRepeatingTimer(n)
        # does not work =/
        dt = time() - self._animation_last_time
        if (dt) < 1 / self._animation_fps:
            return

        with self._animation_lock:
            self._animation_frame = (
                self._animation_frame + 1
            ) % self._animation_total_frames
            self.update_animation(self._animation_frame)
            self._animation_last_time = time()

    def update_animation(self, frame: int):
        raise NotImplementedError(
            'The function "update_animation" was not implemented!'
        )
