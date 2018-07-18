import unittest
import markov


class MarkovTest(unittest.TestCase):
    def test_area_number(self):
        w_s1 = 5
        h_s1 = 2

        def area_number(position, w, h):
            return markov.get_area_number(*position, width=w, height=h)

        def area_number1(position):
            return area_number(position, w_s1, h_s1)

        position1 = (0, 0)
        position2 = (511, 383)
        position3 = (127, 127)  # w/ padding = (191, 159)
        position4 = (127, 128)
        position5 = (128, 128)
        position6 = (64, 64)
        position7 = (63, 64)

        expected1 = 0
        expected2 = 9
        expected3 = 1
        expected4 = 1
        expected5 = 1
        expected6 = 1
        expected7 = 0

        self.assertEqual(area_number1(position1), expected1)
        self.assertEqual(area_number1(position2), expected2)
        self.assertEqual(area_number1(position3), expected3)
        self.assertEqual(area_number1(position4), expected4)
        self.assertEqual(area_number1(position5), expected5)
        self.assertEqual(area_number1(position6), expected6)
        self.assertEqual(area_number1(position7), expected7)

    def test_random_area(self):
        seed = 500  # choice will be 1.) 1, 2.) 1
        start_area1 = 9
        expected_next_area1 = 8

        self.assertEqual(markov.random_area(start_area1, seed),
                         expected_next_area1)

    def test_area_key(self):
        path1 = [0, 1, 2]

        expected1 = '0_1_2'

        self.assertEqual(markov.area_key(*path1), expected1)

    def test_interval_positions(self):
        # 15 seconds
        positions1 = [(-1, -1) for _ in range(markov.interval_frames * 6)]
        positions2 = [(-1, -1) for _ in range(markov.interval_frames * 6)]

        positions2[markov.interval_frames] = [5, 5]
        positions2[markov.interval_frames * 2 - markov.leniency_frames - 1] = [
            5, 5]
        positions2[markov.interval_frames * 3 - markov.leniency_frames] = [5, 5]

        positions2[markov.interval_frames * 4 - markov.leniency_frames + 5] = [
            4, 4]

        positions2[markov.interval_frames * 4 + 5] = [5, 5]

        expected1 = [(-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1), (-1, -1)]
        expected2 = [(-1, -1), (5, 5), (-1, -1), (5, 5), (5, 5), (-1, -1)]

        self.assertListEqual(markov.interval_positions(positions1), expected1)
        self.assertListEqual(markov.interval_positions(positions2), expected2)

    def test_positions_to_areas(self):
        positions1 = [(0, 0), (511, 383), (127, 127), (127, 128), (128, 128)]

        expected1 = [0, 11, 0, 4, 5]

        self.assertListEqual(markov.positions_to_areas(positions1), expected1)
