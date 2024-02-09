import numpy as np
import vtk

from .arcball_camera_style import ArcballCameraInteractorStyle


class BoxSelectionInteractorStyle(ArcballCameraInteractorStyle):
    def __init__(self) -> None:
        ArcballCameraInteractorStyle.__init__(self)

        self.is_selecting = False
        self._click_position = (0, 0)
        self._mouse_position = (0, 0)
        self._saved_pixels = vtk.vtkUnsignedCharArray()
        self.selection_color = (255, 0, 0, 255)

    def _left_button_press_event(self, obj, event):
        super()._left_button_press_event(obj, event)
        self._click_position = self.GetInteractor().GetEventPosition()
        self.start_selection()

    def _left_button_release_event(self, obj, event):
        super()._left_button_release_event(obj, event)
        self.stop_selection()

    def _mouse_move_event(self, obj, event):
        super()._mouse_move_event(obj, event)
        self._mouse_position = self.GetInteractor().GetEventPosition()
        self.update_selection()

    def start_selection(self):
        self.is_selecting = True

        size = self.GetInteractor().GetSize()
        render_window = self.GetInteractor().GetRenderWindow()
        render_window.Render()
        # Save the current screen state
        render_window.GetRGBACharPixelData(
            0, 0, size[0] - 1, size[1] - 1, 0, self._saved_pixels
        )

    def update_selection(self):
        if not self.is_selecting:
            return

        size = self.GetInteractor().GetSize()
        min_x, max_x = sorted([self._click_position[0], self._mouse_position[0]])
        min_y, max_y = sorted([self._click_position[1], self._mouse_position[1]])
        min_x, max_x = np.clip([min_x, max_x], 0, size[0])
        min_y, max_y = np.clip([min_y, max_y], 0, size[1])

        # Copy the saved screen state and draw over it
        selected_pixels = vtk.vtkUnsignedCharArray()
        selected_pixels.DeepCopy(self._saved_pixels)

        for x in range(min_x, max_x, 2):
            for y in range(min_y, max_y, 2):
                pixel = y * size[0] + x
                selected_pixels.SetTuple(pixel, self.selection_color)

        renderWindow = self.GetInteractor().GetRenderWindow()
        renderWindow.SetRGBACharPixelData(
            0, 0, size[0] - 1, size[1] - 1, selected_pixels, 0
        )
        renderWindow.Frame()

    def stop_selection(self):
        self.is_selecting = False
        render_window = self.GetInteractor().GetRenderWindow()
        render_window.Render()
