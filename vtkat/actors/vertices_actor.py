import vtk

from vtkat.poly_data import VerticesData


class VerticesActor(vtk.vtkActor):
    def __init__(self, points) -> None:
        super().__init__()
        self.points = points

    def _create_geometry(self):
        data = VerticesData(self.points)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(data)
        self.SetMapper(mapper)

    def appear_in_front(self, cond: bool):
        # this offset is the Z position of the camera buffer.
        # if it is -66000 the object stays in front of everything.
        offset = -66000 if cond else 0
        mapper = self.GetMapper()
        mapper.SetResolveCoincidentTopologyToPolygonOffset()
        mapper.SetRelativeCoincidentTopologyLineOffsetParameters(0, offset)
        mapper.SetRelativeCoincidentTopologyPolygonOffsetParameters(0, offset)
        mapper.SetRelativeCoincidentTopologyPointOffsetParameter(offset)
