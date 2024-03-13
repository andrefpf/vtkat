import vtk


class CellAreaPicker(vtk.vtkPropPicker):
    def __init__(self) -> None:
        super().__init__()
        self._picked_cells = []
        self._picked_actors = []
        self._picked = dict()

        self._area_picker = vtk.vtkAreaPicker()
        self._cell_picker = vtk.vtkCellPicker()
        self._cell_picker.SetTolerance(0.01)

    def pick(self, x: float, y: float, z: float, renderer: vtk.vtkRenderer):
        self._picked.clear()
        self._cell_picker.Pick(x, y, z, renderer)
        self._picked[self._cell_picker.GetActor()] = [self._cell_picker.GetCellId()]

        # # select a small area around the mouse click
        # delta = 10
        # self.area_pick(x-delta, y-delta, x+delta, y+delta, renderer)

        # # keep at most a single cell selected for every picked actor
        # for actor, selection in self._picked.items():
        #     self._picked[actor] = selection[:1]

    def area_pick(
        self, x0: float, y0: float, x1: float, y1: float, renderer: vtk.vtkRenderer
    ):
        self._picked.clear()
        self._area_picker.AreaPick(x0, y0, x1, y1, renderer)
        extractor = vtk.vtkExtractSelectedFrustum()
        extractor.SetFrustum(self._area_picker.GetFrustum())

        for actor in self._area_picker.GetProp3Ds():
            if not isinstance(actor, vtk.vtkActor):
                continue

            data: vtk.vtkPolyData = actor.GetMapper().GetInput()
            if data is None:
                continue

            cells = []
            for i in range(data.GetNumberOfCells()):
                bounds = [0, 0, 0, 0, 0, 0]
                data.GetCellBounds(i, bounds)
                if extractor.OverallBoundsTest(bounds):
                    cells.append(i)
            self._picked[actor] = cells

    def get_picked(self):
        return dict(self._picked)
