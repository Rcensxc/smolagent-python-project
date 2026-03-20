from typing import List, Optional


class Aerial3DMapConverter:
    """将无人机俯拍的三维数据转换为程序地图。

    输入可以是：
    - height_grid: 每个格子的相对高度（如由三维重建/深度估计得到）
    - risk_grid: 可选的先验风险分数（0~1，如热红外/语义模型输出）

    输出地图编码与现有环境保持一致：
    - 0: 可通行
    - 1: 障碍
    - 2: 危险区域
    """

    def __init__(
        self,
        obstacle_height_threshold: float = 2.5,
        obstacle_slope_threshold: float = 1.3,
        danger_height_threshold: float = 1.4,
        danger_slope_threshold: float = 0.8,
        risk_threshold: float = 0.65,
    ):
        self.obstacle_height_threshold = obstacle_height_threshold
        self.obstacle_slope_threshold = obstacle_slope_threshold
        self.danger_height_threshold = danger_height_threshold
        self.danger_slope_threshold = danger_slope_threshold
        self.risk_threshold = risk_threshold

    def convert(
        self,
        height_grid: List[List[float]],
        risk_grid: Optional[List[List[float]]] = None,
    ) -> List[List[int]]:
        self._validate_grid(height_grid, "height_grid")
        if risk_grid is not None:
            self._validate_grid(risk_grid, "risk_grid")
            if len(risk_grid) != len(height_grid) or len(risk_grid[0]) != len(height_grid[0]):
                raise ValueError("risk_grid 与 height_grid 尺寸必须一致")

        rows = len(height_grid)
        cols = len(height_grid[0])
        result = [[0 for _ in range(cols)] for _ in range(rows)]

        for x in range(rows):
            for y in range(cols):
                height = float(height_grid[x][y])
                local_slope = self._local_max_slope(height_grid, x, y)
                risk_score = float(risk_grid[x][y]) if risk_grid is not None else 0.0

                if (
                    height >= self.obstacle_height_threshold
                    or local_slope >= self.obstacle_slope_threshold
                ):
                    result[x][y] = 1
                elif (
                    height >= self.danger_height_threshold
                    or local_slope >= self.danger_slope_threshold
                    or risk_score >= self.risk_threshold
                ):
                    result[x][y] = 2

        return result

    def _validate_grid(self, grid: List[List[float]], name: str):
        if not grid or not isinstance(grid, list):
            raise ValueError(f"{name} 不能为空")

        width = len(grid[0])
        if width == 0:
            raise ValueError(f"{name} 不能为空")

        for row in grid:
            if len(row) != width:
                raise ValueError(f"{name} 必须是规则二维矩阵")

    def _local_max_slope(self, height_grid: List[List[float]], x: int, y: int) -> float:
        rows = len(height_grid)
        cols = len(height_grid[0])
        center = float(height_grid[x][y])

        max_diff = 0.0
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < rows and 0 <= ny < cols:
                diff = abs(center - float(height_grid[nx][ny]))
                if diff > max_diff:
                    max_diff = diff

        return max_diff
