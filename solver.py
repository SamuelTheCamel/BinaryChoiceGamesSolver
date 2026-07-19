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

    ATTRIBUTES:

    tablebase: a cache of previously searched positions
        format: {position : (outcome, best move, # of moves to outcome, # of moves searched)}
    '''
    def __init__(self, status_func:Callable[[str],int]):
        '''
        Creates a new Game instance where the game outcome is determined by win_func.

        win_func: a function that takes the prior moves as a string 
            and returns the game status using GameStatus.
        '''
        self._status_func = status_func
        self.tablebase:dict[str,tuple[int,str|None,int|None,int]] = dict()

    def status(self, position:str) -> int:
        '''
        Returns the game status for the given position. Return values are defined in GameStatus.
        '''
        return self._status_func(position)

    def search(self, start_pos:str = "", max_depth:int = 20, _recursive=False) -> dict:
        '''
        Attempts to find the optimal move in the given start_pos (the start of the game by default)
            by looking max_depth moves ahead.

        start_pos: the previous moves as a string
        max_depth: the maximum number of moves to look ahead
        _recursive: should be False (set to True during recursive calls)

        Returns a dict with the following values:
            result: the result of the game given optimal play, represented as a GameStatus value
            opt_move: the optimal move represented as "X" or "O" if found (MAY NOT BE PRESENT)
                If both moves are equally good, opt_move will not be present
            num_moves: the number of moves to reach the end of the game given optimal play (MAY NOT BE PRESENT)
            opt_game: the optimal series of moves, given that optimal moves were found
        '''

        # check if game is already over
        status = self.status(start_pos)
        if status != GameStatus.NOT_END:
            self.tablebase[start_pos] = (status,None,0,0)
            return {
                "result" : status,
                "num_moves" : 0,
                "opt_game" : start_pos
            }
        
        # recursive base case
        if max_depth <= 0:
            self.tablebase[start_pos] = (GameStatus.NOT_END,None,None,0)
            return {
                "result" : GameStatus.NOT_END,
                "opt_game" : start_pos
            }
        
        # check if position is in tablebase
        if start_pos in self.tablebase:
            tb_result, tb_opt_move, tb_num_moves, tb_search_depth = self.tablebase[start_pos]
            if tb_search_depth >= max_depth:
            
                ret_dict = dict()
                ret_dict["result"] = tb_result
                if tb_opt_move is not None:
                    ret_dict["opt_move"] = tb_opt_move
                if tb_num_moves is not None:
                    ret_dict["num_moves"] = tb_num_moves
                ret_dict["opt_game"] = start_pos + self.tablebase_best_cont(start_pos)

                return ret_dict
        
        turn = len(start_pos) % 2 # 0 for player 1, 1 for player 2

        if turn == 0:
            WIN = GameStatus.P1WIN
            LOSS = GameStatus.P2WIN
        else:
            WIN = GameStatus.P2WIN
            LOSS = GameStatus.P1WIN
        DRAW = GameStatus.DRAW
        UNKNOWN = GameStatus.NOT_END

        # this is used to get input arguments for _compare_strats
        result_to_str = {
            WIN:"win",
            LOSS:"loss",
            DRAW:"draw",
            UNKNOWN:"unknown"
        }
        
        # recursively search next moves
        ret_x = self.search(start_pos + "X", max_depth - 1, _recursive=True)
        result_x = ret_x.get("result")
        num_moves_x = ret_x.get("num_moves")

        # OPTIMIZATION: if winning series of moves has been found for X, only search up to that many moves for O
        if result_x == WIN:
            o_depth = num_moves_x
        else:
            o_depth = max_depth - 1
        
        ret_o = self.search(start_pos + "O", o_depth, _recursive=True)
        result_o = ret_o.get("result")
        num_moves_o = ret_o.get("num_moves")

        result:int = UNKNOWN
        opt_move:str|None = None
        num_moves:int|None = None

        # determine best move
        result_x_str = result_to_str[result_x]
        result_o_str = result_to_str[result_o]
        ret_comp = self._compare_strats(result_x_str, num_moves_x, result_o_str, num_moves_o)

        if ret_comp == 1:
            # X is optimal move
            result = result_x
            opt_move = "X"
            if num_moves_x is not None:
                num_moves = num_moves_x + 1
        elif ret_comp == 2:
            # O is optimal move
            result = result_o
            opt_move = "O"
            if num_moves_o is not None:
                num_moves = num_moves_o + 1
        else:
            # both moves are equally good
            result = result_x
            if num_moves_x is not None:
                num_moves = num_moves_x + 1
        
        # add position to tablebase
        tb_update = False
        if start_pos in self.tablebase:
            if result != GameStatus.NOT_END:
                tb_result, tb_opt_move, tb_num_moves, tb_search_depth = self.tablebase[start_pos]
                if tb_search_depth < max_depth:
                    self.tablebase[start_pos] = (result, opt_move, num_moves, max_depth)
                    tb_update = True
                            
        else:
            self.tablebase[start_pos] = (result, opt_move, num_moves, max_depth)
            tb_update = True

        # check if previous positions in tablebase need to be updated
        prev_pos = start_pos[:-1]
        if tb_update and len(start_pos) > 0 and not _recursive:
            self._tablebase_update_pos(prev_pos)


        # get best move list
        if opt_move == "X":
            opt_game = ret_x.get("opt_game")
        elif opt_move == "O":
            opt_game = ret_o.get("opt_game")
        elif result != UNKNOWN:
            opt_game = ret_x.get("opt_game") # choose X by default
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
    

    def tablebase_best_cont(self, position:str) -> str:
        '''
        Gets the best move continuation from the given position by using the tablebase.

        position: the prior sequence of moves (ex. "XOOXO")
        '''
        if position not in self.tablebase:
            return ""
        
        tb_result, tb_opt_move, tb_num_moves, tb_search_depth = self.tablebase[position]
        if tb_opt_move is None:
            if tb_result == GameStatus.NOT_END or tb_num_moves == 0:
                return ""
            else:
                return "X" + self.tablebase_best_cont(position + "X") # choose X by default
        else:
            return tb_opt_move + self.tablebase_best_cont(position + tb_opt_move)
        

    def _tablebase_update_pos(self, position:str):
        '''
        Updates the given position by checking the next two positions.
        Recursively updates all previous positions as necessary.
        '''
        print(f"Updating {position}")

        if position not in self.tablebase:
            # add dummy entry to tablebase so the following code can work
            self.tablebase[position] = (0,None,None,0)

        old_result, old_opt_move, old_num_moves, old_search_depth = self.tablebase[position]

        if position + "X" in self.tablebase:
            result_x, opt_move_x, num_moves_x, search_depth_x = self.tablebase[position + "X"]
        else:
            result_x = GameStatus.NOT_END
            opt_move_x = None
            num_moves_x = None
            search_depth_x = 0
        
        if position + "O" in self.tablebase:
            result_o, opt_move_o, num_moves_o, search_depth_o = self.tablebase[position + "O"]
        else:
            result_o = GameStatus.NOT_END
            opt_move_o = None
            num_moves_o = None
            search_depth_o = 0

        turn = len(position) % 2 # 0 for player 1, 1 for player 2

        if turn == 0:
            WIN = GameStatus.P1WIN
            LOSS = GameStatus.P2WIN
        else:
            WIN = GameStatus.P2WIN
            LOSS = GameStatus.P1WIN
        DRAW = GameStatus.DRAW
        UNKNOWN = GameStatus.NOT_END

        # this is used to get input arguments for _compare_strats
        result_to_str = {
            WIN:"win",
            LOSS:"loss",
            DRAW:"draw",
            UNKNOWN:"unknown"
        }

        result:int = UNKNOWN
        opt_move:str|None = None
        num_moves:int|None = None

        # determine best move
        result_x_str = result_to_str[result_x]
        result_o_str = result_to_str[result_o]
        ret_comp = self._compare_strats(result_x_str, num_moves_x, result_o_str, num_moves_o)

        if ret_comp == 1:
            # X is optimal move
            result = result_x
            opt_move = "X"
            if num_moves_x is not None:
                num_moves = num_moves_x + 1
        elif ret_comp == 2:
            # O is optimal move
            result = result_o
            opt_move = "O"
            if num_moves_o is not None:
                num_moves = num_moves_o + 1
        else:
            # both moves are equally good
            result = result_x
            if num_moves_x is not None:
                num_moves = num_moves_x + 1

        self.tablebase[position] = (result, opt_move, num_moves, old_search_depth)

        # if something has changed, update previous position
        if (old_result, old_num_moves) != (result, num_moves) and len(position) > 0:
            self._tablebase_update_pos(position[:-1])
        

    def _compare_strats(self, outcome1:str, num_moves1:int|None, outcome2:str, num_moves2:int|None) -> int:
        '''
        Compares two strategies by their outcome ("win", "loss", "draw", or "unknown") 
            and the number of moves to reach that outcome in order to determine which strategy
            is better.

        outcome1: the outcome of strategy 1 ("win", "loss", "draw", or "unknown")
        num_moves1: the number of moves to reach the outcome of strategy 1 (or None if the outcome is "unknown")
        outcome2: the outcome of strategy 2 ("win", "loss", "draw", or "unknown")
        num_moves2: the number of moves to reach the outcome of strategy 2 (or None if the outcome is "unknown")

        Returns:
            1 if strategy 1 is better
            2 if strategy 2 is better
            0 if both strategies are equally good
        '''
        if outcome1 == "win":
            if outcome2 == "win":
                # both strategies are winning, choose fastest one
                if num_moves1 < num_moves2:
                    return 1
                elif num_moves1 > num_moves2:
                    return 2
                else:
                    return 0
            else:
                return 1
        elif outcome2 == "win":
            return 2
        # cannot win, avoid a loss
        elif outcome1 == "loss":
            if outcome2 == "loss":
                # both strategies are losing, choose slowest one
                if num_moves1 < num_moves2:
                    return 2
                elif num_moves1 > num_moves2:
                    return 1
                else:
                    return 0
            else:
                return 2
        elif outcome2 == "loss":
            return 1
        # no known way to win or lose, avoid a draw
        elif outcome1 == "draw":
            if outcome2 == "draw":
                # draw is inevitable, choose slowest one
                if num_moves1 < num_moves2:
                    return 2
                elif num_moves1 > num_moves2:
                    return 1
                else:
                    return 0
            else:
                return 2
        elif outcome2 == "draw":
            return 1
        else:
            # both strategies lead to unknown outcomes
            return 0
    

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