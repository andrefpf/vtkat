import vtk


class CellPropertyAreaPicker(vtk.vtkPropPicker):
    def __init__(self, property_name: str, desired_actor: vtk.vtkActor) -> None:
        super().__init__()

        self.property_name = property_name
        self.desired_actor = desired_actor
        self._picked = set()

        self._cell_picker = vtk.vtkCellPicker()
        self._area_picker = vtk.vtkAreaPicker()
        self._cell_picker.SetTolerance(0.005)

    def pick(self, x: float, y: float, z: float, renderer: vtk.vtkRenderer):
        # maybe a behaviour like the one implemented in CellAreaPicker
        # would fit nicely here
        self._picked.clear()
        self._cell_picker.Pick(x, y, z, renderer)

        if self.desired_actor != self._cell_picker.GetActor():
            return self.get_picked()

        data: vtk.vtkPolyData = self.desired_actor.GetMapper().GetInput()
        if data is None:
            return self.get_picked()

        property_array = data.GetCellData().GetArray(self.property_name)
        if property_array is None:
            return self.get_picked()

        cell = self._cell_picker.GetCellId()
        property_val = property_array.GetValue(cell)
        self._picked.add(property_val)
        return self.get_picked()

    def area_pick(
        self, x0: float, y0: float, x1: float, y1: float, renderer: vtk.vtkRenderer
    ):
        self._picked.clear()
        self._area_picker.AreaPick(x0, y0, x1, y1, renderer)
        extractor = vtk.vtkExtractSelectedFrustum()
        extractor.SetFrustum(self._area_picker.GetFrustum())

        if self.desired_actor not in self._area_picker.GetProp3Ds():
            return self.get_picked()

        data: vtk.vtkPolyData = self.desired_actor.GetMapper().GetInput()
        if data is None:
            return self.get_picked()

        property_array = data.GetCellData().GetArray(self.property_name)
        if property_array is None:
            return self.get_picked()
    
        if property_array.GetNumberOfValues() < data.GetNumberOfCells():
            return self.get_picked()

        for cell in range(data.GetNumberOfCells()):
            property_val = property_array.GetValue(cell)

            # if the property was already picked
            # we don't even need to check if the cell
            # is inside the selection box
            if property_val in self._picked:
                continue

            bounds = [0, 0, 0, 0, 0, 0]
            data.GetCellBounds(cell, bounds)
            if extractor.OverallBoundsTest(bounds):
                self._picked.add(property_val)
        return self.get_picked()

    def get_picked(self):
        return set(self._picked)
