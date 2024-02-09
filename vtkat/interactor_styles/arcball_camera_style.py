import numpy as np
import vtk

from vtkat.actors import RoundPointsActor


class ArcballCameraInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    """
    Interactor style that rotates and zooms around the cursor.
    """

    def __init__(self):
        self.center_of_rotation = None
        self.default_center_of_rotation = None

        self.is_left_clicked = False
        self.is_right_clicked = False
        self.is_mid_clicked = False

        self.is_rotating = False
        self.is_panning = False

        # cor = center of rotation
        self.cor_actor = self._make_default_cor_actor()
        self._create_observers()

    def set_default_center_of_rotation(self, center):
        self.default_center_of_rotation = center

    def set_cor_actor(self, actor):
        self.cor_actor = actor

    def _create_observers(self):
        self.AddObserver("LeftButtonPressEvent", self._left_button_press_event)
        self.AddObserver("LeftButtonReleaseEvent", self._left_button_release_event)
        self.AddObserver("RightButtonPressEvent", self._right_button_press_event)
        self.AddObserver("RightButtonReleaseEvent", self._right_button_release_event)
        self.AddObserver("MouseMoveEvent", self._mouse_move_event)
        self.AddObserver("MouseWheelForwardEvent", self._mouse_wheel_forward_event)
        self.AddObserver("MouseWheelBackwardEvent", self._mouse_wheel_backward_event)
        self.AddObserver("MiddleButtonPressEvent", self._click_mid_button_press_event)
        self.AddObserver(
            "MiddleButtonReleaseEvent", self._click_mid_button_release_event
        )

    def _left_button_press_event(self, obj, event):
        # Implemented to stop the superclass movement
        self.is_left_clicked = True

    def _left_button_release_event(self, obj, event):
        # Implemented to stop the superclass movement
        self.is_left_clicked = False

    def _right_button_press_event(self, obj, event):
        self.is_right_clicked = True
        self.is_rotating = True

        cursor = self.GetInteractor().GetEventPosition()
        self.FindPokedRenderer(cursor[0], cursor[1])

        renderer = self.GetCurrentRenderer() or self.GetDefaultRenderer()
        camera = renderer.GetActiveCamera()

        if renderer is None:
            return

        picker = vtk.vtkPropPicker()
        picker.Pick(cursor[0], cursor[1], 0, renderer)
        pos = picker.GetPickPosition()

        if pos != (0, 0, 0):
            self.center_of_rotation = pos

        elif self.default_center_of_rotation is not None:
            self.center_of_rotation = self.default_center_of_rotation

        else:
            x0, x1, y0, y1, z0, z1 = renderer.ComputeVisiblePropBounds()
            self.center_of_rotation = [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2]

        dx, dy, dz = np.array(camera.GetPosition()) - np.array(camera.GetFocalPoint())
        distance_factor = np.sqrt(dx**2 + dy**2 + dz**2)

        self.cor_actor.SetPosition(self.center_of_rotation)
        self.cor_actor.SetScale(
            (distance_factor / 3.5, distance_factor / 3.5, distance_factor / 3.5)
        )
        renderer.AddActor(self.cor_actor)

    def _right_button_release_event(self, obj, event):
        self.is_right_clicked = False
        self.is_rotating = False
        renderer = self.GetDefaultRenderer() or self.GetCurrentRenderer()
        renderer.RemoveActor(self.cor_actor)
        self.GetInteractor().Render()
        self.EndDolly()

    def _click_mid_button_press_event(self, obj, event):
        self.is_mid_clicked = True
        self.is_panning = True
        int_pos = self.GetInteractor().GetEventPosition()
        self.FindPokedRenderer(int_pos[0], int_pos[1])

    def _click_mid_button_release_event(self, obj, event):
        self.is_mid_clicked = False
        self.is_panning = False

    def _mouse_move_event(self, obj, event):
        if self.is_rotating:
            self.rotate()

        if self.is_panning:
            self.Pan()

        self.OnMouseMove()

    def _mouse_wheel_forward_event(self, obj, event):
        int_pos = self.GetInteractor().GetEventPosition()

        self.FindPokedRenderer(int_pos[0], int_pos[1])

        if self.GetCurrentRenderer() is None:
            return

        motion_factor = 10
        mouse_motion_factor = 1

        factor = motion_factor * 0.2 * mouse_motion_factor

        self.dolly(1.1**factor)

        self.ReleaseFocus()

    def _mouse_wheel_backward_event(self, obj, event):
        int_pos = self.GetInteractor().GetEventPosition()

        self.FindPokedRenderer(int_pos[0], int_pos[1])

        if self.GetCurrentRenderer() is None:
            return

        motion_factor = 10
        mouse_motion_factor = 1

        factor = motion_factor * -0.2 * mouse_motion_factor

        self.dolly(1.1**factor)

        self.ReleaseFocus()

    def rotate(self):
        renderer = self.GetDefaultRenderer() or self.GetCurrentRenderer()
        if renderer is None:
            return

        rwi = self.GetInteractor()
        delta_mouse = np.array(rwi.GetEventPosition()) - np.array(
            rwi.GetLastEventPosition()
        )
        size = np.array(renderer.GetRenderWindow().GetSize())
        motion_factor = 10
        elevation_azimuth = -20 / size
        rotation_factor = delta_mouse * motion_factor * elevation_azimuth

        camera = renderer.GetActiveCamera()

        self.rotate_around_center(rotation_factor[0], rotation_factor[1])

        camera.OrthogonalizeViewUp()

        renderer.ResetCameraClippingRange()

        if rwi.GetLightFollowCamera():
            renderer.UpdateLightsGeometryToFollowCamera()

        rwi.Render()

    def rotate_around_center(self, anglex, angley):
        renderer = self.GetDefaultRenderer() or self.GetCurrentRenderer()
        camera = renderer.GetActiveCamera()

        transform_camera = vtk.vtkTransform()
        transform_camera.Identity()

        axis = [
            -camera.GetViewTransformObject().GetMatrix().GetElement(0, 0),
            -camera.GetViewTransformObject().GetMatrix().GetElement(0, 1),
            -camera.GetViewTransformObject().GetMatrix().GetElement(0, 2),
        ]

        saved_view_up = camera.GetViewUp()
        transform_camera.RotateWXYZ(angley, axis)
        new_view_up = transform_camera.TransformPoint(camera.GetViewUp())
        camera.SetViewUp(new_view_up)
        transform_camera.Identity()

        cor = self.center_of_rotation

        transform_camera.Translate(+cor[0], +cor[1], +cor[2])
        transform_camera.RotateWXYZ(anglex, camera.GetViewUp())
        transform_camera.RotateWXYZ(angley, axis)
        transform_camera.Translate(-cor[0], -cor[1], -cor[2])

        new_camera_position = transform_camera.TransformPoint(camera.GetPosition())
        camera.SetPosition(new_camera_position)

        new_focal_point = transform_camera.TransformPoint(camera.GetFocalPoint())
        camera.SetFocalPoint(new_focal_point)

        camera.SetViewUp(saved_view_up)

        camera.Modified()

    def dolly(self, factor):
        renderer = self.GetDefaultRenderer() or self.GetCurrentRenderer()
        camera = renderer.GetActiveCamera()
        cursor = self.GetInteractor().GetEventPosition()

        if factor <= 0:
            return

        cam_up = np.array(camera.GetViewUp())
        cam_in = np.array(camera.GetDirectionOfProjection())
        cam_side = np.cross(cam_in, cam_up)

        displacements = self.get_dolly_displacements(
            factor,
            cursor,
            camera,
            renderer,
        )

        camera_position = np.array(camera.GetPosition())
        focal_point = np.array(camera.GetFocalPoint())
        rotated_displacements = cam_side * displacements[0] + cam_up * displacements[1]
        camera.SetPosition(camera_position + rotated_displacements)
        camera.SetFocalPoint(focal_point + rotated_displacements)

        if camera.GetParallelProjection():
            camera.SetParallelScale(camera.GetParallelScale() / factor)
        else:
            camera.Dolly(factor)
            if self.GetAutoAdjustCameraClippingRange():
                renderer.ResetCameraClippingRange()

        if self.GetInteractor().GetLightFollowCamera():
            renderer.UpdateLightsGeometryToFollowCamera()

        self.GetInteractor().Render()

    def get_dolly_displacements(self, factor, cursor, camera, renderer):
        cursor = np.array(cursor)
        view_center = np.array(renderer.GetSize()) / 2
        cursor_to_center = cursor - view_center

        if camera.GetParallelProjection():
            view_height = 2 * camera.GetParallelScale()
        else:
            correction = camera.GetDistance()
            view_height = 2 * correction * np.tan(0.5 * camera.GetViewAngle() / 57.296)

        scale = view_height / renderer.GetSize()[1]
        return cursor_to_center * scale * (1 - 1 / factor)

    def _make_default_cor_actor(self):
        actor = RoundPointsActor([(0, 0, 0)])
        actor.appear_in_front(True)
        actor.GetProperty().SetColor(1, 0, 0)
        actor.GetProperty().SetPointSize(10)
        return actor
