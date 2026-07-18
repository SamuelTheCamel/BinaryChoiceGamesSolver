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

        # cannot win, avoid a loss
        elif ret_x["result"] == LOSS:

            if ret_o["result"] == LOSS:
                # loss is inevitable
                result = LOSS
                if ret_o["num_moves"] < ret_x["num_moves"]:
                    # X will lose slower
                    opt_move = "X"
                    num_moves = ret_x["num_moves"] + 1
                else:
                    # O will lose slower
                    opt_move = "O"
                    num_moves = ret_o["num_moves"] + 1

            else:
                # O prevents losing
                result = ret_o["result"]
                opt_move = "O"
                if "num_moves" in ret_o:
                    num_moves = ret_o["num_moves"] + 1
        
        elif ret_o["result"] == LOSS:
            # X prevents losing
            result = ret_x["result"]
            opt_move = "X"
            if "num_moves" in ret_x:
                num_moves = ret_x["num_moves"] + 1

        # no known way to win or lose, avoid a draw
        elif ret_x["result"] == DRAW:

            if ret_o["result"] == DRAW:
                # draw is inevitable
                result = DRAW
                if ret_o["num_moves"] < ret_x["num_moves"]:
                    # X will draw slower
                    opt_move = "X"
                    num_moves = ret_x["num_moves"] + 1
                else:
                    # O will draw slower
                    opt_move = "O"
                    num_moves = ret_o["num_moves"] + 1

            else:
                # O prevents drawing
                result = UNKNOWN
                opt_move = "O"
                if "num_moves" in ret_o:
                    num_moves = ret_o["num_moves"] + 1

        elif ret_o["result"] == DRAW:
            # X prevents drawing
            result = UNKNOWN
            opt_move = "X"
            if "num_moves" in ret_x:
                num_moves = ret_x["num_moves"] + 1
        
        else:
            # everything is unknown
            result = UNKNOWN
        
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
    

    def tablebase_outcome_stats(self) -> dict[str,int]:
        '''
        Returns the amount of positions in the tablebase with each outcome.

        Returns a dict with the following values:
            p1_win: the number of positions that result in a win for player 1
            p2_win: the number of positions that result in a win for player 2
            draw: the number of positions that result in a draw
            unknown: the number of positions that have an unknown outcome
        '''
        p1_win_count = 0
        p2_win_count = 0
        draw_count = 0
        unknown_count = 0

        for pos in self.tablebase:
            result = self.tablebase[pos][0]
            if result == GameStatus.P1WIN:
                p1_win_count += 1
            elif result == GameStatus.P2WIN:
                p2_win_count += 1
            elif result == GameStatus.DRAW:
                draw_count += 1
            else:
                unknown_count += 1
        
        return {
            "p1_win":p1_win_count,
            "p2_win":p2_win_count,
            "draw":draw_count,
            "unknown":unknown_count
        }
    

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

        NOTE: Players should not be able to keep playing after the game is over.
            If a position is passed to the generated function that includes moves after the
            game is over, the function will have undefined behavior.
        '''

        # unholy nested function
        def ret_func(position:str) -> int:

            # count repitions for player 1
            if len(position) >= p1_len:
                last_pattern = position[-p1_len:]
                short_pos = position[:-p1_len]
                move_num = 0
                p1_reps = 1

                while move_num + p1_len <= len(short_pos):
                    cur_pattern = short_pos[move_num:move_num+p1_len]
                    if cur_pattern == last_pattern:
                        p1_reps += 1
                        move_num += p1_len
                    else:
                        move_num += 1
            else:
                p1_reps = 0

            # count repitions for player 2
            if len(position) >= p2_len:
                last_pattern = position[-p2_len:]
                short_pos = position[:-p2_len]
                move_num = 0
                p2_reps = 1

                while move_num + p2_len <= len(short_pos):
                    cur_pattern = short_pos[move_num:move_num+p2_len]
                    if cur_pattern == last_pattern:
                        p2_reps += 1
                        move_num += p2_len
                    else:
                        move_num += 1
            else:
                p2_reps = 0

            # determine if either player won
            if p1_reps >= p1_freq:
                if p2_reps >= p2_freq:
                    return GameStatus.DRAW
                else:
                    return GameStatus.P1WIN
            elif p2_reps >= p2_freq:
                return GameStatus.P2WIN
            else:
                return GameStatus.NOT_END
            
        return ret_func