import vtk

from vtkat.poly_data import VerticesData


class SquarePointsActor(vtk.vtkActor):
    def __init__(self, points_list) -> None:
        super().__init__()
        self.points_list = points_list
        self.build()

    def build(self):
        data = VerticesData(self.points_list)
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
