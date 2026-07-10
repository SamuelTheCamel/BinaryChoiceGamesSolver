BinaryChoiceGamesSolver
=======================

This code finds winning strategies games with two players where on each player's turn, they can make one of two binary choices.

Since these games can potentially go on forever and the number of possible positions increases exponentially the further you look out, this solver has a maximum turn limit. To look further, you can specify a specific position to start from.

The code is made to be flexible so you can specify your own custom rules. To do this, you need to create a function to determine when a game is a win, a draw, or not finished yet.

This is inspired by a game described by WebGoatGuy in this video: <https://www.youtube.com/watch?v=A-lh1-bTzTw>