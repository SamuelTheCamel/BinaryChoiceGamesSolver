from collections.abc import Callable


class GameStatus():
    '''
    Enum for representing the status of a position.
    '''
    P1WIN = 1 # player 1 wins
    P2WIN = 2 # player 2 wins
    DRAW = -1 # game has ended in a draw
    NOT_END = 0 # the game has not ended yet


class Game():
    '''
    A binary choice game.

    Positions are represented as a string of moves where each character is an "X" or "O". (ex. "XOOXO")
    '''
    def __init__(self, status_func:Callable[[str],int]):
        '''
        Creates a new Game instance where the game outcome is determined by win_func.

        win_func: a function that takes the prior moves as a string 
            and returns the game status using GameStatus.
        '''
        self._status_func = status_func
        self.tablebase:dict[str,tuple[int,str|None,int|None]] = dict() # format: {position : (outcome, best move, # of moves)}

    def status(self, position:str) -> int:
        '''
        Returns the game status for the given position. Return values are defined in GameStatus.
        '''
        return self._status_func(position)

    def search(self, start_pos:str = "", max_depth:int = 20) -> dict:
        '''
        Find the optimal move in the given start_pos (the start of the game by default) if the game
        can be won in 500 moves.

        start_pos: the previous moves as a string
        max_depth: the maximum number of moves to look ahead

        Returns a dict with the following values:
            result: the result of the game given optimal play, represented as a GameStatus value
            opt_move: the optimal move represented as "X" or "O" if found (MAY NOT BE PRESENT)
            num_moves: the number of moves to reach the end of the game given optimal play (MAY NOT BE PRESENT)
            opt_game: the optimal series of moves, given that optimal moves were found
        '''

        # check if game is already over
        status = self.status(start_pos)
        if status != GameStatus.NOT_END:
            self.tablebase[start_pos] = (status,None,0)
            return {
                "result" : status,
                "num_moves" : 0,
                "opt_game" : start_pos
            }
        
        if max_depth == 0:
            self.tablebase[start_pos] = (GameStatus.NOT_END,None,None)
            return {
                "result" : GameStatus.NOT_END,
                "opt_game" : start_pos
            }
        
        turn = len(start_pos) % 2 # 0 for player 1, 1 for player 2

        if turn == 0:
            WIN = GameStatus.P1WIN
            LOSS = GameStatus.P2WIN
        else:
            WIN = GameStatus.P2WIN
            LOSS = GameStatus.P1WIN
        DRAW = GameStatus.DRAW
        UNKNOWN = GameStatus.NOT_END
        
        # recursively search next moves
        ret_x = self.search(start_pos + "X", max_depth - 1)

        # OPTIMIZATION: if winning series of moves has been found for X, only search up to that many moves for O
        if ret_x["result"] == WIN:
            o_depth = ret_x["num_moves"]
        else:
            o_depth = max_depth - 1
        
        ret_o = self.search(start_pos + "O", o_depth)

        result:int = UNKNOWN
        opt_move:str|None = None
        num_moves:int|None = None

        if ret_x["result"] == WIN:
            # can win by choosing X
            result = WIN

            if ret_o["result"] == WIN and ret_o["num_moves"] < ret_x["num_moves"]:
                # O will win faster
                opt_move = "O"
                num_moves = ret_o["num_moves"] + 1
            else:
                # O will not win faster
                opt_move = "X"
                num_moves = ret_x["num_moves"] + 1
        
        elif ret_o["result"] == WIN:
            # can win by choosing O
            result = WIN
            opt_move = "O"
            num_moves = ret_o["num_moves"] + 1

        # cannot win
        elif ret_x["result"] == DRAW:
            # can draw by choosing X
            result = DRAW
            
            if ret_o["result"] == DRAW and ret_o["num_moves"] < ret_x["num_moves"]:
                # O will draw faster
                opt_move = "O"
                num_moves = ret_o["num_moves"] + 1
            else:
                # O will not draw faster
                opt_move = "X"
                num_moves = ret_x["num_moves"] + 1

        elif ret_o["result"] == DRAW:
            # can draw by choosing O
            result = DRAW
            opt_move = "O"
            num_moves = ret_o["num_moves"] + 1

        # cannot win or draw
        elif ret_x["result"] == LOSS:
            
            if ret_o["result"] == LOSS:
                # losing is inevitable
                result = LOSS
                if ret_o["num_moves"] < ret_x["num_moves"]:
                    opt_move = "X"
                    num_moves = ret_x["num_moves"] + 1
                else:
                    opt_move = "O"
                    num_moves = ret_o["num_moves"] + 1
            else:
                # O leads to an uncertain result
                result = UNKNOWN
                opt_move = "O"
        
        else:
            # X leads to an uncertain result
            result = UNKNOWN
            opt_move = "X"
        
        
        # add position to tablebase
        if start_pos in self.tablebase:
            if result != GameStatus.NOT_END:
                tb_result, tb_opt_move, tb_num_moves = self.tablebase[start_pos]
                if tb_result == GameStatus.NOT_END or tb_num_moves is None or tb_num_moves > num_moves:
                    self.tablebase[start_pos] = (result, opt_move, num_moves)
        else:
            self.tablebase[start_pos] = (result, opt_move, num_moves)

        # get best move list
        if opt_move == "X":
            opt_game = ret_x["opt_game"]
        elif opt_move == "O":
            opt_game = ret_o["opt_game"]
        else:
            opt_game = start_pos
        
        ret_dict = dict()
        ret_dict["result"] = result
        if opt_move is not None:
            ret_dict["opt_move"] = opt_move
        if num_moves is not None:
            ret_dict["num_moves"] = num_moves
        ret_dict["opt_game"] = opt_game

        return ret_dict
    

class StatusFunc():
    '''
    Contains functions for creating status functions for determining when a game is a win or draw
    '''

    @staticmethod
    def repeated_patterns_gen(p1_len:int, p1_freq:int, p2_len:int, p2_freq:int) -> Callable[[str],int]:
        '''
        Generates a status function for the game where either player can win if they get a certain
        number of repeated moves of a certain length.

        p1_len: length of Player 1's patterns
        p1_freq: number of repeated patterns for Player 1 to win
        p2_len: length of Player 2's patterns
        p2_freq: number of repeated patterns for Player 2 to win
        '''

        # unholy nested function
        def ret_func(position:str) -> int:

            p1_reps:dict[str,int] = dict() # format: { pattern : # of occurances }
            p2_reps:dict[str,int] = dict()
            p1_last_occurance:dict[str,int] = dict() # format: { pattern : move # of most recent occurance }
            p2_last_occurance:dict[str,int] = dict()
            p1_win_move:int|None = None # the move when player 1 wins, or None if they do not win
            p2_win_move:int|None = None # same for player 2

            # count repitions for player 1
            for move_num in range(len(position) - p1_len + 1):
                cur_substr = position[move_num : move_num+p1_len]

                if cur_substr in p1_reps:
                    if move_num >= p1_last_occurance[cur_substr] + p1_len: # ensure overlapping patterns are not counted
                        p1_reps[cur_substr] += 1
                        p1_last_occurance[cur_substr] = move_num

                        if p1_reps[cur_substr] >= p1_freq:
                            p1_win_move = move_num + p1_len
                            break # no need to calculate future moves
                else:
                    p1_reps[cur_substr] = 1
                    p1_last_occurance[cur_substr] = move_num

            for move_num in range(len(position) - p2_len + 1):
                cur_substr = position[move_num : move_num+p2_len]

                if cur_substr in p2_reps:
                    if move_num >= p2_last_occurance[cur_substr] + p2_len: # ensure overlapping patterns are not counted
                        p2_reps[cur_substr] += 1
                        p2_last_occurance[cur_substr] = move_num

                        if p2_reps[cur_substr] >= p2_freq:
                            p2_win_move = move_num + p2_len
                            break # no need to calculate future moves
                else:
                    p2_reps[cur_substr] = 1
                    p2_last_occurance[cur_substr] = move_num

            if p1_win_move is None:
                if p2_win_move is None:
                    return GameStatus.NOT_END
                else:
                    return GameStatus.P2WIN
            elif p2_win_move is None or p1_win_move < p1_win_move:
                return GameStatus.P1WIN
            elif p1_win_move > p1_win_move:
                return GameStatus.P2WIN
            else:
                return GameStatus.DRAW
            
        return ret_func