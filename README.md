BinaryChoiceGamesSolver
=======================

This code finds winning strategies for perfect information games with two players where on each player's turn, they can make one of two choices.

The two choices are represented as X and O, and all the players' previous choices are presented as a string of Xs and Os.

Since the number of possible game states increases exponentially the further you look out, this solver has a maximum turn limit (the default is 20). You can change this limit as you please, but it may cause the search to take a very long time. You can also start the search from a future position to see the optimal moves from that position.

The code is made to be flexible so you can specify your own custom rules. To do this, you need to create a function to determine when a game is a win, a draw, or not finished yet. Then, create a `Game` instance with your function passed as a parameter. There are also some pre-built functions in the `StatusFunc` class for you to use.

This is inspired by a game described by WebGoatGuy in this video: <https://www.youtube.com/watch?v=A-lh1-bTzTw>

## Example Code

```python
my_func = StatusFunc.repeated_patterns_gen(5,2,3,4) # you can replace this with your own custom function
my_game = Game(my_func)
my_game.search() # search for winning strategy from the starting position
my_game.search("XOXXO") # search for winning strategy from custom position
my_game.search("OOX", max_depth=10) # search 10 moves ahead from custom position
```
