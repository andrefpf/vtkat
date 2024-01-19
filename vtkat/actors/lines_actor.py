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
