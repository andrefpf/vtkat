import vtk
from PIL import Image
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QFrame, QStackedLayout
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.util.numpy_support import vtk_to_numpy
from pathlib import Path

from vtkat import VTKAT_DIR
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

        self.create_info_text()
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

    def get_screenshot(self) -> Image.Image:
        image_filter = vtk.vtkWindowToImageFilter()
        image_filter.SetInput(self.render_interactor.GetRenderWindow())
        image_filter.Update()

        vtk_image = image_filter.GetOutput()
        width, height, _ = vtk_image.GetDimensions()
        vtk_array = vtk_image.GetPointData().GetScalars()
        components = vtk_array.GetNumberOfComponents()

        array = vtk_to_numpy(vtk_array).reshape(height, width, components)
        image = Image.fromarray(array).transpose(Image.FLIP_TOP_BOTTOM)
        return image

    def get_thumbnail(self):
        image = self.get_screenshot()
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
        image = self.get_screenshot()
        with open(path, "w") as file:
            image.save(file)

    def create_axes(self):
        axes_actor = vtk.vtkAxesActor()
        axes_actor.SetTipTypeToSphere()

        axes_actor.SetXAxisLabelText(" X")
        axes_actor.SetYAxisLabelText(" Y")
        axes_actor.SetZAxisLabelText(" Z")

        axes_actor.GetXAxisShaftProperty().LightingOff()
        axes_actor.GetYAxisShaftProperty().LightingOff()
        axes_actor.GetZAxisShaftProperty().LightingOff()
        axes_actor.GetXAxisTipProperty().LightingOff()
        axes_actor.GetYAxisTipProperty().LightingOff()
        axes_actor.GetZAxisTipProperty().LightingOff()     

        x_property = axes_actor.GetXAxisCaptionActor2D().GetCaptionTextProperty()
        y_property = axes_actor.GetYAxisCaptionActor2D().GetCaptionTextProperty()
        z_property = axes_actor.GetZAxisCaptionActor2D().GetCaptionTextProperty()

        for text_property in [x_property, y_property, z_property]:
            text_property: vtk.vtkTextProperty
            text_property.ItalicOff()
            text_property.BoldOn()

        self.axes = vtk.vtkOrientationMarkerWidget()
        self.axes.SetViewport(0, 0, 0.18, 0.18)
        self.axes.SetOrientationMarker(axes_actor)
        self.axes.SetInteractor(self.render_interactor)
        self.axes.EnabledOn()
        self.axes.InteractiveOff()

    def create_scale_bar(self):
        self.scale_bar_actor = vtk.vtkLegendScaleActor()
        self.scale_bar_actor.AllAxesOff()

        font_file = VTKAT_DIR / "fonts/LiberationMono-Bold.ttf"

        title_property: vtk.vtkTextProperty
        title_property = self.scale_bar_actor.GetLegendTitleProperty()
        title_property.SetFontSize(14)
        title_property.ShadowOff()
        title_property.ItalicOff()
        title_property.BoldOn()
        title_property.SetLineOffset(-55)
        title_property.SetVerticalJustificationToTop()
        title_property.SetFontFamily(vtk.VTK_FONT_FILE)
        title_property.SetFontFile(font_file)

        label_property: vtk.vtkTextProperty
        label_property = self.scale_bar_actor.GetLegendLabelProperty()
        label_property.SetFontSize(12)
        label_property.SetColor((0.8, 0.8, 0.8))
        label_property.ShadowOff()
        label_property.ItalicOff()
        label_property.BoldOff()
        label_property.SetLineOffset(-35)
        label_property.SetFontFamily(vtk.VTK_FONT_FILE)
        label_property.SetFontFile(font_file)

        self.renderer.AddActor(self.scale_bar_actor)

    def create_color_bar(self, lookup_table=None):
        if lookup_table is None:
            lookup_table = vtk.vtkLookupTable()
            lookup_table.Build()

        font_file = VTKAT_DIR / "fonts/LiberationMono-Bold.ttf"

        colorbar_title = vtk.vtkTextProperty()
        colorbar_title.ShadowOff()
        colorbar_title.ItalicOff()
        colorbar_title.BoldOn()
        colorbar_title.SetFontSize(13)
        colorbar_title.SetColor((0.8, 0.8, 0.8))
        colorbar_title.SetJustificationToLeft()
        colorbar_title.SetFontFamily(vtk.VTK_FONT_FILE)
        colorbar_title.SetFontFile(font_file)

        colorbar_label = vtk.vtkTextProperty()
        colorbar_label.ShadowOff()
        colorbar_label.ItalicOff()
        colorbar_label.BoldOn()
        colorbar_label.SetFontSize(12)
        colorbar_label.SetColor((0.8, 0.8, 0.8))
        colorbar_label.SetJustificationToLeft()
        colorbar_label.SetFontFamily(vtk.VTK_FONT_FILE)
        colorbar_label.SetFontFile(font_file)

        self.colorbar_actor = vtk.vtkScalarBarActor()
        self.colorbar_actor.SetTitleTextProperty(colorbar_title)
        self.colorbar_actor.SetLabelTextProperty(colorbar_label)
        self.colorbar_actor.SetLabelFormat("%1.0e ")
        self.colorbar_actor.SetLookupTable(lookup_table)
        self.colorbar_actor.SetWidth(0.02)
        self.colorbar_actor.SetPosition(0.94, 0.17)
        self.colorbar_actor.SetHeight(0.7)
        self.colorbar_actor.SetMaximumNumberOfColors(400)
        self.colorbar_actor.SetVerticalTitleSeparation(20)
        self.colorbar_actor.UnconstrainedFontSizeOn()
        self.colorbar_actor.SetTextPositionToPrecedeScalarBar()
        self.renderer.AddActor(self.colorbar_actor)

    def create_info_text(self):
        font_file = VTKAT_DIR / "fonts/LiberationMono-Bold.ttf"

        self.info_text_property = vtk.vtkTextProperty()
        self.info_text_property.SetFontSize(14)
        self.info_text_property.SetVerticalJustificationToTop()
        self.info_text_property.SetColor((0.2, 0.2, 0.2))
        self.info_text_property.SetLineSpacing(1.2)
        self.info_text_property.SetFontFamilyToTimes()
        self.info_text_property.SetFontFamily(vtk.VTK_FONT_FILE)
        self.info_text_property.SetFontFile(font_file)

        self.text_actor = vtk.vtkTextActor()
        self.text_actor.SetTextProperty(self.info_text_property)
        self.renderer.AddActor2D(self.text_actor)

        coord = self.text_actor.GetPositionCoordinate()
        coord.SetCoordinateSystemToNormalizedViewport()
        coord.SetValue(0.01, 0.95)

    def create_logo(self, path: str | Path) -> vtk.vtkLogoRepresentation:
        path = Path(path)

        image_reader = vtk.vtkPNGReader()
        image_reader.SetFileName(path)
        image_reader.Update()

        logo = vtk.vtkLogoRepresentation()
        logo.SetImage(image_reader.GetOutput())
        logo.ProportionalResizeOn()
        logo.GetImageProperty().SetOpacity(0.9)
        logo.GetImageProperty().SetDisplayLocationToBackground()

        self.renderer.AddViewProp(logo)
        logo.SetRenderer(self.renderer)
        return logo

    def create_camera_light(self, offset_x=0, offset_y=0):
        light = vtk.vtkLight()
        light.SetLightTypeToCameraLight()
        light.SetPosition(offset_x, offset_y, 1)
        self.renderer.AddLight(light)

    def set_info_text(self, text):
        self.text_actor.SetInput(text)

    def set_theme(self, theme):
        if theme == "dark":
            self.renderer.GradientBackgroundOn()
            self.renderer.SetBackground(0.06, 0.08, 0.12)
            self.renderer.SetBackground2(0.7, 0.7, 0.75)

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

    def copy_camera_from(self, other):
        if isinstance(other, CommonRenderWidget):
            other_camera = other.renderer.GetActiveCamera() 
        elif isinstance(other, vtk.vtkRenderer):
            other_camera = other.GetActiveCamera() 
        else:
            return

        self.renderer.GetActiveCamera().DeepCopy(other_camera)
        self.renderer.ResetCameraClippingRange()
        self.renderer.GetActiveCamera().Modified()
        self.update()
