import vtk


class LinesData(vtk.vtkPolyData):
    def __init__(self, lines_list) -> None:
        super().__init__()

        self.lines_list = lines_list
        self.build()

    def build(self):
        points = vtk.vtkPoints()
        self.Allocate(len(self.lines_list))

        current_point = 0
        for x0, y0, z0, x1, y1, z1 in self.lines_list:
            points.InsertPoint(current_point, x0, y0, z0)
            points.InsertPoint(current_point + 1, x1, y1, z1)
            self.InsertNextCell(vtk.VTK_LINE, 2, [current_point, current_point + 1])
            current_point += 2

        self.SetPoints(points)
