2048 (https://play2048.co) is an interesting game, why not make our own? Please follow the requirements below and create your own invention.

1. Generate an initial board with a random number of `2`s at random cells, e.g.:

```json
[
  [2, null, 2, null],
  [null, 2, null, 2],
  [2, null, 2, null],
  [null, 2, null, 2]
]
```

2. Support _Move Left_ on the board. E.g.:

Before:

```json
[
  [null, 8, 2, 2],
  [4, 2, null, 2],
  [null, null, null, null],
  [null, null, null, 2]
]
```

After Move Left:

```json
[
  [8, 4, null, null],
  [4, 4, null, null],
  [null, null, null, null],
  [2, null, null, null]
]
```

3. Support _Move Right_. E.g.:

Before:

```json
[
  [null, 8, 2, 2],
  [4, 2, null, 2],
  [null, null, null, null],
  [null, null, null, 2]
]
```

After Move Right:

```json
[
  [null, null, 8, 4],
  [null, null, 4, 4],
  [null, null, null, null],
  [null, null, null, 2]
]
```

4. Support _Move Up_ and _Move Down_. E.g.:

Before:

```json
[
  [null, 8, 2, 2],
  [4, 2, null, 2],
  [null, null, null, null],
  [null, null, null, 2]
]
```

After Merge Up:

```json
[
  [4, 8, 2, 4],
  [null, 2, null, 2],
  [null, null, null, null],
  [null, null, null, null]
]
```

5. Generate a `2` or `4` at a random empty space after each valid move that changes the board. E.g.:

Before:

```json
[
  [null, 8, 2, 2],
  [4, 2, null, 2],
  [null, null, null, null],
  [null, null, null, 2]
]
```

After Move Up and adding a new 2 or 4:

```json
[
  [4, 8, 2, 4],
  [null, 2, null, 2],
  [null, null, null, null],
  [2, null, null, null]
]
```

5. Determine endgame condition (Lose or Win). E.g.:

No more moves (Lose):

```json
[
  [2, 4, 2, 4],
  [4, 2, 4, 2],
  [2, 4, 2, 4],
  [4, 2, 4, 2]
]
```

Or, we've reached the goal of 2048 (Win):

```json
[
  [4, null, null, 2],
  [2048, null, null, null],
  [4, 2, null, null],
  [4, null, null, null]
]
```

6. AI Suggestion. During a gameplay, allow players to ask for the best possible move from an AI model to avoid gameover and maximize the chance of winning the game. You can use an offline AI model or connect with a remote AI server. Please do not submit with any credentials.

Remarks:

- Any programming language is welcome.
- You may make reasonable assumptions and clearly state them if anything is not explicitly mentioned above.
- The goal is to create a well-structured and maintainable codebase. Don’t overthink the task or worry about performance.
- A very basic user interface would be appreciated. However, adding extra features to the game will not earn additional credit.
- The requirements may deviate from the original 2048 game. In case of any conflict, priority should be given to the former.
