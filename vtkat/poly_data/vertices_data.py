import vtk


class VerticesData(vtk.vtkPolyData):
    """
    This class describes a polydata composed by a set of points.
    """

    def __init__(self, points_list: list[tuple[int, int, int]]) -> None:
        super().__init__()

        points = vtk.vtkPoints()
        self.Allocate(len(points_list))

        for i, (x, y, z) in enumerate(points_list):
            points.InsertNextPoint(x, y, z)
            self.InsertNextCell(vtk.VTK_VERTEX, 1, [i])

        self.SetPoints(points)
