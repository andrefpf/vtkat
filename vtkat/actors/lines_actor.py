import vtk

from vtkat.poly_data import LinesData


class LinesActor(vtk.vtkActor):
    def __init__(self, lines_list) -> None:
        super().__init__()
        self.lines_list = lines_list

        self.build()
    
    def build(self):
        data = LinesData(self.lines_list)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(data)
        self.SetMapper(mapper)
        self.GetProperty().SetLineWidth(3)

    def set_width(self, width):
        self.GetProperty().SetLineWidth(width)

    def appear_in_front(self, cond: bool):
        # this offset is the Z position of the camera buffer.
        # if it is -66000 the object stays in front of everything.
        offset = -66000 if cond else 0
        mapper = self.GetMapper()
        mapper.SetResolveCoincidentTopologyToPolygonOffset()
        mapper.SetRelativeCoincidentTopologyLineOffsetParameters(0, offset)
        mapper.SetRelativeCoincidentTopologyPolygonOffsetParameters(0, offset)
        mapper.SetRelativeCoincidentTopologyPointOffsetParameter(offset)
