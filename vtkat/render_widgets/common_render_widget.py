import vtk
from PIL import Image
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QStackedLayout
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtk.util.numpy_support import vtk_to_numpy

from vtkat.interactor_styles import ArcballCameraInteractorStyle


class CommonRenderWidget(QFrame):
    """
    This class is needed to show vtk renderers in pyqt.

    A vtk widget must always have a renderer, even if it is empty.
    """

    left_clicked = pyqtSignal(int, int)
    left_released = pyqtSignal(int, int)
    right_clicked = pyqtSignal(int, int)
    right_released = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.renderer = vtk.vtkRenderer()
        self.interactor_style = ArcballCameraInteractorStyle()
        self.render_interactor = QVTKRenderWindowInteractor(self)

        self.render_interactor.Initialize()
        self.render_interactor.GetRenderWindow().AddRenderer(self.renderer)
        self.render_interactor.SetInteractorStyle(self.interactor_style)
        self.renderer.ResetCamera()

        self.render_interactor.AddObserver(
            "LeftButtonPressEvent", self.left_click_press_event
        )
        self.render_interactor.AddObserver(
            "LeftButtonReleaseEvent", self.left_click_release_event
        )
        self.render_interactor.AddObserver(
            "RightButtonPressEvent", self.right_click_press_event
        )
        self.render_interactor.AddObserver(
            "RightButtonReleaseEvent", self.right_click_release_event
        )

        layout = QStackedLayout()
        layout.addWidget(self.render_interactor)
        self.setLayout(layout)

        self.set_theme("dark")

    def update_plot(self):
        raise NotImplementedError("The function update_plot was not implemented")

    def update(self):
        ren_win = self.render_interactor.GetRenderWindow()
        if ren_win is not None:
            ren_win.Render()

    def left_click_press_event(self, obj, event):
        x, y, *_ = self.render_interactor.GetEventPosition()
        self.left_clicked.emit(x, y)

    def left_click_release_event(self, obj, event):
        x, y, *_ = self.render_interactor.GetEventPosition()
        self.left_released.emit(x, y)

    def right_click_press_event(self, obj, event):
        x, y, *_ = self.render_interactor.GetEventPosition()
        self.right_clicked.emit(x, y)

    def right_click_release_event(self, obj, event):
        x, y, *_ = self.render_interactor.GetEventPosition()
        self.right_released.emit(x, y)

    def get_thumbnail(self):
        image_filter = vtk.vtkWindowToImageFilter()
        image_filter.SetInput(self.render_interactor.GetRenderWindow())
        image_filter.Update()

        vtk_image = image_filter.GetOutput()
        width, height, _ = vtk_image.GetDimensions()
        vtk_array = vtk_image.GetPointData().GetScalars()
        components = vtk_array.GetNumberOfComponents()

        array = vtk_to_numpy(vtk_array).reshape(height, width, components)
        image = Image.fromarray(array).transpose(Image.FLIP_TOP_BOTTOM)

        size = min(image.width, image.height)
        box = (
            (image.width - size) // 2,
            (image.height - size) // 2,
            (image.width + size) // 2,
            (image.height + size) // 2,
        )
        image = image.crop(box=box).resize(size=(512, 512))
        return image

    def save_png(self, path):
        imageFilter = vtk.vtkWindowToImageFilter()
        imageFilter.SetInput(self.render_interactor.GetRenderWindow())
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(path)
        writer.SetInputConnection(imageFilter.GetOutputPort())
        writer.Write()

    def create_axes(self):
        axes_actor = vtk.vtkAxesActor()

        x_property = axes_actor.GetXAxisCaptionActor2D().GetCaptionTextProperty()
        y_property = axes_actor.GetYAxisCaptionActor2D().GetCaptionTextProperty()
        z_property = axes_actor.GetZAxisCaptionActor2D().GetCaptionTextProperty()

        for i in [x_property, y_property, z_property]:
            i.ItalicOff()
            i.BoldOff()

        self.axes = vtk.vtkOrientationMarkerWidget()
        self.axes.SetOrientationMarker(axes_actor)
        self.axes.SetInteractor(self.render_interactor)
        self.axes.EnabledOn()
        self.axes.InteractiveOff()

    def create_scale_bar(self):
        self.scale_bar = vtk.vtkLegendScaleActor()
        self.scale_bar.AllAxesOff()

        title_property = self.scale_bar.GetLegendTitleProperty()
        title_property.SetFontSize(14)
        title_property.ShadowOff()
        title_property.ItalicOff()
        title_property.SetLineOffset(-35)
        title_property.SetVerticalJustificationToTop()

        label_property = self.scale_bar.GetLegendLabelProperty()
        label_property.SetFontSize(12)
        label_property.ShadowOff()
        label_property.ItalicOff()
        label_property.BoldOff()
        label_property.SetLineOffset(-25)

        self.renderer.AddActor(self.scale_bar)

    def create_color_bar(self, lookup_table=None):
        if lookup_table is None:
            lookup_table = vtk.vtkLookupTable()
            lookup_table.Build()

        colorbar_label = vtk.vtkTextProperty()
        colorbar_label.ShadowOff()
        colorbar_label.ItalicOff()
        colorbar_label.BoldOn()
        colorbar_label.SetFontSize(12)
        colorbar_label.SetJustificationToLeft()

        self.colorbar = vtk.vtkScalarBarActor()
        self.colorbar.SetLabelTextProperty(colorbar_label)
        self.colorbar.SetLookupTable(lookup_table)
        self.colorbar.SetWidth(0.02)
        self.colorbar.SetPosition(0.94, 0.07)
        self.colorbar.SetMaximumNumberOfColors(400)
        self.colorbar.UnconstrainedFontSizeOn()
        self.colorbar.SetTextPositionToPrecedeScalarBar()
        self.renderer.AddActor(self.colorbar)

    def set_theme(self, theme):
        if theme == "dark":
            self.renderer.GradientBackgroundOn()
            self.renderer.SetBackground(0.06, 0.08, 0.12)
            self.renderer.SetBackground2(0, 0, 0)
        elif theme == "light":
            self.renderer.GradientBackgroundOn()
            self.renderer.SetBackground(0.5, 0.5, 0.65)
            self.renderer.SetBackground2(1, 1, 1)
        else:
            NotImplemented

    #
    def set_custom_view(self, position, view_up):
        self.renderer.GetActiveCamera().SetPosition(position)
        self.renderer.GetActiveCamera().SetViewUp(view_up)
        self.renderer.GetActiveCamera().SetParallelProjection(True)
        self.renderer.ResetCamera(*self.renderer.ComputeVisiblePropBounds())
        self.update()

    def set_top_view(self):
        x, y, z = self.renderer.GetActiveCamera().GetFocalPoint()
        position = (x, y + 1, z)
        view_up = (0, 0, -1)
        self.set_custom_view(position, view_up)

    def set_bottom_view(self):
        x, y, z = self.renderer.GetActiveCamera().GetFocalPoint()
        position = (x, y - 1, z)
        view_up = (0, 0, 1)
        self.set_custom_view(position, view_up)

    def set_left_view(self):
        x, y, z = self.renderer.GetActiveCamera().GetFocalPoint()
        position = (x - 1, y, z)
        view_up = (0, 1, 0)
        self.set_custom_view(position, view_up)

    def set_right_view(self):
        x, y, z = self.renderer.GetActiveCamera().GetFocalPoint()
        position = (x + 1, y, z)
        view_up = (0, 1, 0)
        self.set_custom_view(position, view_up)

    def set_front_view(self):
        x, y, z = self.renderer.GetActiveCamera().GetFocalPoint()
        position = (x, y, z + 1)
        view_up = (0, 1, 0)
        self.set_custom_view(position, view_up)

    def set_back_view(self):
        x, y, z = self.renderer.GetActiveCamera().GetFocalPoint()
        position = (x, y, z - 1)
        view_up = (0, 1, 0)
        self.set_custom_view(position, view_up)

    def set_isometric_view(self):
        x, y, z = self.renderer.GetActiveCamera().GetFocalPoint()
        position = (x + 1, y + 1, z + 1)
        view_up = (0, 1, 0)
        self.set_custom_view(position, view_up)
