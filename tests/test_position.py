import unittest
import math
import position


class PositionTest(unittest.TestCase):
    def test_define_circle(self):
        pts = [(1, 1), (2, 4), (5, 3)]

        expected_cx = 3
        expected_cy = 2
        expected_radius = math.sqrt(5)

        actual_cx, actual_cy, actual_radius = position.define_circle(*pts)

        self.assertEqual(expected_cx, actual_cx)
        self.assertEqual(expected_cy, actual_cy)
        self.assertAlmostEqual(actual_radius, expected_radius, places=5)

    def test_next_circle_point1(self):
        desired_distance1 = math.pi / -2
        desired_distance2 = math.pi / 2

        start_x, start_y = 384, 192
        center_x, center_y = 256, 192
        args1 = start_x, start_y, center_x, center_y, desired_distance1
        args2 = start_x, start_y, center_x, center_y, desired_distance2

        expected_destination1 = (256, 320)
        expected_destination2 = (256, 64)

        actual_destination1 = position.next_circle_point(*args1)
        actual_destination2 = position.next_circle_point(*args2)

        self.assertTupleEqual(expected_destination1, actual_destination1)
        self.assertTupleEqual(expected_destination2, actual_destination2)

    def test_get_angle_radians(self):
        """
        NOTE: Y-axis is INVERTED
        """
        pts2 = (0, 0), (90, 0)
        pts3 = (0, 0), (0, 90)
        pts4 = (0, 0), (-90, 90)
        pts5 = (0, 0), (-90, 0)
        pts6 = (0, 0), (90, 90)
        pts7 = (0, 0), (90, 45)

        expected2 = 0
        expected3 = (math.pi * 3) / 2
        expected4 = (math.pi * 5) / 4
        expected5 = math.pi
        expected6 = (math.pi * 7) / 4
        expected7 = (math.pi * 15) / 8

        self.assertEqual(expected2, position.get_angle_radians(*pts2))
        self.assertEqual(expected3, position.get_angle_radians(*pts3))
        self.assertEqual(expected4, position.get_angle_radians(*pts4))
        self.assertEqual(expected5, position.get_angle_radians(*pts5))
        self.assertEqual(expected6, position.get_angle_radians(*pts6))
        self.assertAlmostEqual(expected7, position.get_angle_radians(*pts7),
                               delta=0.1)

    def test_valid_radian_range(self):

        args1 = 204, 355, 80.37616326530608
        args2 = 60, 360, 80

        intersect_pts1 = [(278, 384), (129, 384)]
        intersect_pts2 = [(136, 384), (0, 307)]

        expected1_0 = position.get_angle_radians(args1[:2], intersect_pts1[0])
        expected1_1 = position.get_angle_radians(args1[:2], intersect_pts1[1])

        expected2_0 = position.get_angle_radians(args2[:2], intersect_pts2[0])
        expected2_1 = position.get_angle_radians(args2[:2], intersect_pts2[1])

        actual1 = position.valid_radian_range(*args1)
        actual2 = position.valid_radian_range(*args2)

        self.assertAlmostEqual(expected1_0, actual1[0], delta=0.1)
        self.assertAlmostEqual(expected1_1, actual1[1], delta=0.1)
        self.assertAlmostEqual(expected2_0, actual2[0], delta=0.1)
        self.assertAlmostEqual(expected2_1, actual2[1], delta=0.1)

    def test_is_between(self):
        """
        NOTE: Y-axis is INVERTED
        """
        pts1 = [(1, 0), (-1, 0), (0, -1)]
        pts2 = [(1, 0), (0, 1), (1, -1)]

        self.assertTrue(position.is_between(*pts1))
        self.assertTrue(position.is_between(*pts2))

    def test_get_quadrant(self):
        """
        NOTE: Y-axis is INVERTED
        """
        origin = (0, 0)
        pt1 = (1, 0)
        pt2 = ((2 ** 0.5) / 2, (2 ** 0.5) / -2)
        pt3 = (0, -1)
        pt4 = ((2 ** 0.5) / -2, (2 ** 0.5) / -2)
        pt5 = (-1, 0)
        pt6 = ((2 ** 0.5) / -2, (2 ** 0.5) / 2)
        pt7 = (0, 1)
        pt8 = ((2 ** 0.5) / 2, (2 ** 0.5) / 2)

        expected1 = 0
        expected2 = 0
        expected3 = 1
        expected4 = 1
        expected5 = 2
        expected6 = 2
        expected7 = 3
        expected8 = 3

        self.assertEqual(expected1, position.get_quadrant(origin, pt1))
        self.assertEqual(expected2, position.get_quadrant(origin, pt2))
        self.assertEqual(expected3, position.get_quadrant(origin, pt3))
        self.assertEqual(expected4, position.get_quadrant(origin, pt4))
        self.assertEqual(expected5, position.get_quadrant(origin, pt5))
        self.assertEqual(expected6, position.get_quadrant(origin, pt6))
        self.assertEqual(expected7, position.get_quadrant(origin, pt7))
        self.assertEqual(expected8, position.get_quadrant(origin, pt8))

    def test_arc_len(self):
        center = 0, 0
        radius = 1
        pts1 = [(1, 0), ((2 ** 0.5) / 2, (2 ** 0.5) / -2)]
        pts2 = [((2 ** 0.5) / 2, (2 ** 0.5) / -2),
                ((2 ** 0.5) / -2, (2 ** 0.5) / -2)]
        pts3 = [((2 ** 0.5) / -2, (2 ** 0.5) / -2),
                ((2 ** 0.5) / 2, (2 ** 0.5) / -2)]

        expected1 = math.pi / 4
        expected2 = math.pi / 2
        expected3 = 3 * math.pi / 2

        self.assertAlmostEqual(
            expected1,
            position.arc_len(pts1[0], pts1[1], center, radius),
            delta=0.001
        )
        self.assertAlmostEqual(
            expected2,
            position.arc_len(pts2[0], pts2[1], center, radius),
            delta=0.001
        )
        self.assertAlmostEqual(
            expected3,
            position.arc_len(pts3[0], pts3[1], center, radius),
            delta=0.001
        )
