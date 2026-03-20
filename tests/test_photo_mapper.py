import unittest

from environment import Environment
from photo_mapper import Aerial3DMapConverter


class Aerial3DMapConverterTest(unittest.TestCase):

    def test_detect_obstacle_and_danger(self):
        converter = Aerial3DMapConverter(
            obstacle_height_threshold=2.5,
            danger_height_threshold=1.4,
            obstacle_slope_threshold=2.0,
            risk_threshold=0.65,
        )
        heights = [
            [0.0, 0.1, 0.2],
            [0.1, 3.2, 0.2],
            [0.1, 0.2, 1.6],
        ]
        risks = [
            [0.1, 0.1, 0.8],
            [0.1, 0.1, 0.1],
            [0.1, 0.1, 0.1],
        ]

        mapped = converter.convert(heights, risks)

        self.assertEqual(mapped[1][1], 1)  # 高障碍
        self.assertEqual(mapped[2][2], 2)  # 高度危险
        self.assertEqual(mapped[0][2], 2)  # 风险危险

    def test_environment_load_from_aerial_3d(self):
        env = Environment(size=3, vision_radius=1)
        heights = [
            [0.0, 0.0, 0.0],
            [0.0, 2.8, 0.0],
            [0.0, 0.0, 0.0],
        ]

        env.load_from_aerial_3d(heights, start=(0, 0), target=(2, 2))

        self.assertEqual(env.true_grid[1][1], 1)
        self.assertEqual(env.true_grid[0][0], 0)
        self.assertEqual(env.true_grid[2][2], 0)
        self.assertEqual(env.size, 3)


if __name__ == "__main__":
    unittest.main()
