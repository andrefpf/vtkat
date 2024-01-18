from .square_points_actor import SquarePointsActor


class RoundPointsActor(SquarePointsActor):
    def __init__(self, points) -> None:
        super().__init__(points)
        self.GetProperty().RenderPointsAsSpheresOn()
