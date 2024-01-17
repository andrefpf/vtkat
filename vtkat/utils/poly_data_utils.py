import vtk


def set_polydata_colors(data: vtk.vtkPolyData, color: tuple):
    n_cells = data.GetNumberOfCells()
    cell_colors = vtk.vtkUnsignedCharArray()
    cell_colors.SetName("colors")
    cell_colors.SetNumberOfComponents(3)
    cell_colors.SetNumberOfTuples(n_cells)
    cell_colors.FillComponent(0, color[0])
    cell_colors.FillComponent(1, color[1])
    cell_colors.FillComponent(2, color[2])
    data.GetCellData().SetScalars(cell_colors)


def set_polydata_property(
    data: vtk.vtkPolyData, property_data: int, property_name: str
):
    n_cells = data.GetNumberOfCells()
    cell_identifier = vtk.vtkUnsignedIntArray()
    cell_identifier.SetName(property_name)
    cell_identifier.SetNumberOfTuples(n_cells)
    cell_identifier.Fill(property_data)
    data.GetCellData().AddArray(cell_identifier)
