import vtk

from vtkat.poly_data import VerticesData


class SquarePointsActor(vtk.vtkActor):
    def __init__(self, points) -> None:
        super().__init__()
        self.points = points
        self._create_geometry()

    def _create_geometry(self):
        data = VerticesData(self.points)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(data)
        self.SetMapper(mapper)

        self.GetProperty().SetPointSize(20)
        self.GetProperty().LightingOff()

    def set_size(self, size):
        self.GetProperty().SetPointSize(size)

    def appear_in_front(self, cond: bool):
        # this offset is the Z position of the camera buffer.
        # if it is -66000 the object stays in front of everything.
        offset = -66000 if cond else 0
        mapper = self.GetMapper()
        mapper.SetResolveCoincidentTopologyToPolygonOffset()
        mapper.SetRelativeCoincidentTopologyLineOffsetParameters(0, offset)
        mapper.SetRelativeCoincidentTopologyPolygonOffsetParameters(0, offset)
        mapper.SetRelativeCoincidentTopologyPointOffsetParameter(offset)
