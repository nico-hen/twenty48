// PROTOTYPE — throwaway. Answers: "how boring/maintainable can we make this?"
// Deliberately the simplest thing that fulfils the spec: one file, no
// dependencies, plain line-based input. Easy for anyone to read and maintain.
//
// Run:      go run prototypes/simple-go/main.go
// Controls: type w/a/s/d then Enter to move, h for an AI hint, q to quit.
package main

import (
	"bufio"
	"fmt"
	"math/rand"
	"os"
	"strings"
)

const size = 4
const win = 2048

type board [size][size]int // 0 means empty

func empties(b board) [][2]int {
	var out [][2]int
	for r := 0; r < size; r++ {
		for c := 0; c < size; c++ {
			if b[r][c] == 0 {
				out = append(out, [2]int{r, c})
			}
		}
	}
	return out
}

func spawn(b *board, onlyTwo bool) {
	cells := empties(*b)
	if len(cells) == 0 {
		return
	}
	p := cells[rand.Intn(len(cells))]
	val := 2
	if !onlyTwo && rand.Intn(4) == 0 { // 25% chance of a 4
		val = 4
	}
	b[p[0]][p[1]] = val
}

func newBoard() board {
	var b board
	n := 2 + rand.Intn(5) // req 1: random number of 2s
	for i := 0; i < n; i++ {
		spawn(&b, true)
	}
	return b
}

// compressMerge slides + merges one row to the left.
func compressMerge(row [size]int) [size]int {
	var vals []int
	for _, v := range row {
		if v != 0 {
			vals = append(vals, v)
		}
	}
	var out []int
	for i := 0; i < len(vals); i++ {
		if i+1 < len(vals) && vals[i] == vals[i+1] {
			out = append(out, vals[i]*2)
			i++
		} else {
			out = append(out, vals[i])
		}
	}
	var res [size]int
	copy(res[:], out)
	return res
}

func transpose(b board) board {
	var t board
	for r := 0; r < size; r++ {
		for c := 0; c < size; c++ {
			t[c][r] = b[r][c]
		}
	}
	return t
}

func reverseRows(b board) board {
	for r := 0; r < size; r++ {
		for i, j := 0, size-1; i < j; i, j = i+1, j-1 {
			b[r][i], b[r][j] = b[r][j], b[r][i]
		}
	}
	return b
}

// move returns the new board and whether anything changed.
func move(b board, dir byte) (board, bool) {
	orig := b
	if dir == 'w' || dir == 's' {
		b = transpose(b)
	}
	if dir == 'd' || dir == 's' {
		b = reverseRows(b)
	}
	for r := 0; r < size; r++ {
		b[r] = compressMerge(b[r])
	}
	if dir == 'd' || dir == 's' {
		b = reverseRows(b)
	}
	if dir == 'w' || dir == 's' {
		b = transpose(b)
	}
	return b, b != orig
}

func won(b board) bool {
	for _, row := range b {
		for _, v := range row {
			if v == win {
				return true
			}
		}
	}
	return false
}

func lost(b board) bool {
	if len(empties(b)) > 0 {
		return false
	}
	for _, d := range []byte{'w', 'a', 's', 'd'} {
		if _, changed := move(b, d); changed {
			return false
		}
	}
	return true
}

// score + suggest: offline heuristic AI (no network, no credentials).
func score(b board) int {
	s := len(empties(b)) * 10
	for _, m := range []board{b, transpose(b)} {
		for _, row := range m {
			for i := 0; i < size-1; i++ {
				if row[i] != 0 && row[i] == row[i+1] {
					s += row[i]
				}
			}
		}
	}
	return s
}

func suggest(b board) string {
	best, bestS := byte(0), -1
	for _, d := range []byte{'a', 'd', 'w', 's'} {
		if nb, changed := move(b, d); changed && score(nb) > bestS {
			best, bestS = d, score(nb)
		}
	}
	names := map[byte]string{'a': "Left", 'd': "Right", 'w': "Up", 's': "Down"}
	if name, ok := names[best]; ok {
		return name
	}
	return "no move"
}

func render(b board) {
	fmt.Println("\n  2048 — PROTOTYPE (Go, plain CLI)")
	for _, row := range b {
		fmt.Print("  ")
		for _, v := range row {
			if v == 0 {
				fmt.Printf("%5s", ".")
			} else {
				fmt.Printf("%5d", v)
			}
		}
		fmt.Println()
	}
	fmt.Println("  (w/a/s/d = move, h = hint, q = quit)")
}

func main() {
	b := newBoard()
	sc := bufio.NewScanner(os.Stdin)
	for {
		render(b)
		if won(b) {
			fmt.Println("  You reached 2048! 🎉")
		} else if lost(b) {
			fmt.Println("  No moves left — game over. 💀")
		}
		fmt.Print("  > ")
		if !sc.Scan() {
			return
		}
		in := strings.TrimSpace(sc.Text())
		if in == "" {
			continue
		}
		switch in[0] {
		case 'q':
			return
		case 'h':
			fmt.Println("  AI suggests:", suggest(b))
		case 'w', 'a', 's', 'd':
			if nb, changed := move(b, in[0]); changed {
				b = nb
				spawn(&b, false) // req 5
			}
		}
	}
}
