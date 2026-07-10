from solver import *
import unittest

class TestSolver(unittest.TestCase):

    def test_repeated_patterns(self):
        test_func_1 = StatusFunc.repeated_patterns_gen(5,2,3,4)
        self.assertEqual(test_func_1(""), GameStatus.NOT_END)
        self.assertEqual(test_func_1("XXXXXXXXXX"), GameStatus.P1WIN)
        self.assertEqual(test_func_1("OOOOOOOOOO"), GameStatus.P1WIN)
        self.assertEqual(test_func_1("XOXXOXXOOOXXOXOO"), GameStatus.P1WIN)
        self.assertEqual(test_func_1("XOXOOXOXXOXOXOX"), GameStatus.P2WIN)
        self.assertEqual(test_func_1("XOXOXXOXXOXXOXOX"), GameStatus.DRAW)
        
        game_1 = Game(test_func_1)
        print(game_1.search())
        print(game_1.tablebase["O"])

if __name__ == '__main__':
    unittest.main()

