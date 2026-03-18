import argparse
import csv
import random
import copy

class CrosswordGenerator:
    def __init__(self, words_with_hints):
        # Sort by length descending to place long "backbone" words first
        self.data = sorted(words_with_hints, key=lambda x: len(x[1]), reverse=True)
        self.grid = {}  # (x, y) -> char
        self.placed_words = [] # List of {word, hint, x, y, direction, number, final_num}

    def reset(self):
        self.grid = {}
        self.placed_words = []

    def generate_once(self):
        self.reset()
        if not self.data:
            return 0, 0, 0
            
        # Randomize the first word slightly
        first_idx = random.randint(0, min(2, len(self.data) - 1))
        first_hint, first_word = self.data[first_idx]
        remaining_data = self.data[:first_idx] + self.data[first_idx+1:]
        
        self._place(first_word.upper().strip(), first_hint, 0, 0, 'H', 1)
        random.shuffle(remaining_data)

        for hint, word in remaining_data:
            word = word.upper().strip()
            possible_placements = []
            
            for (gx, gy), char in list(self.grid.items()):
                for idx, letter in enumerate(word):
                    if letter == char:
                        for direction in ['H', 'V']:
                            nx = gx - idx if direction == 'H' else gx
                            ny = gy if direction == 'H' else gy - idx
                            if self._can_place(word, nx, ny, direction):
                                score = self._score_placement(word, nx, ny, direction)
                                possible_placements.append((score, nx, ny, direction))
            
            if possible_placements:
                possible_placements.sort(key=lambda x: x[0], reverse=True)
                # Favor higher scores more aggressively
                best = possible_placements[0]
                _, bx, by, bdir = best
                self._place(word, hint, bx, by, bdir, len(self.placed_words) + 1)
        
        if not self.grid:
            return 0, 0, 0
            
        min_x, min_y, max_x, max_y = self.get_bounds()
        area = (max_x - min_x + 1) * (max_y - min_y + 1)
        return len(self.placed_words), self._total_intersections(), area

    def generate_best(self, attempts=100):
        best_grid = None
        best_placed = None
        max_score = -float('inf')

        for _ in range(attempts):
            num_placed, intersections, area = self.generate_once()
            if num_placed == 0:
                continue
            
            # Score: more words, more intersections, smaller area
            score = (num_placed * 1000) + (intersections * 200) - (area * 5)
            
            if score > max_score:
                max_score = score
                best_grid = copy.deepcopy(self.grid)
                best_placed = copy.deepcopy(self.placed_words)
        
        self.grid = best_grid
        self.placed_words = best_placed
        self._renumber()

    def _renumber(self):
        if not self.placed_words:
            return
        self.placed_words.sort(key=lambda w: (w['y'], w['x']))
        starts = {}
        current_num = 1
        for w in self.placed_words:
            pos = (w['x'], w['y'])
            if pos not in starts:
                starts[pos] = current_num
                current_num += 1
            w['final_num'] = starts[pos]

    def _total_intersections(self):
        cells = {}
        for w in self.placed_words:
            for i in range(len(w['word'])):
                cx = w['x'] + (i if w['dir'] == 'H' else 0)
                cy = w['y'] + (0 if w['dir'] == 'H' else i)
                cells[(cx, cy)] = cells.get((cx, cy), 0) + 1
        return sum(1 for count in cells.values() if count > 1)

    def _score_placement(self, word, x, y, direction):
        intersections = 0
        for i, char in enumerate(word):
            cx, cy = (x + i, y) if direction == 'H' else (x, y + i)
            if (cx, cy) in self.grid:
                intersections += 1
        return intersections

    def _can_place(self, word, x, y, direction):
        before = (x - 1, y) if direction == 'H' else (x, y - 1)
        after = (x + len(word), y) if direction == 'H' else (x, y + len(word))
        if before in self.grid or after in self.grid:
            return False

        intersections = 0
        for i, char in enumerate(word):
            cx, cy = (x + i, y) if direction == 'H' else (x, y + i)
            existing = self.grid.get((cx, cy))
            
            if existing is not None:
                if existing != char:
                    return False
                intersections += 1
            else:
                if direction == 'H':
                    if (cx, cy - 1) in self.grid or (cx, cy + 1) in self.grid:
                        return False
                else:
                    if (cx - 1, cy) in self.grid or (cx + 1, cy) in self.grid:
                        return False
        
        return intersections > 0

    def _place(self, word, hint, x, y, direction, number):
        for i, char in enumerate(word):
            cx, cy = (x + i, y) if direction == 'H' else (x, y + i)
            self.grid[(cx, cy)] = char
        self.placed_words.append({'word': word, 'hint': hint, 'x': x, 'y': y, 'dir': direction, 'num': number})

    def get_bounds(self):
        if not self.grid:
            return 0, 0, 0, 0
        xs, ys = zip(*self.grid.keys())
        return min(xs), min(ys), max(xs), max(ys)

    def draw_crossword(self, filename, solved=False, cell_size=60):
        if not self.grid: return
        
        min_x, min_y, max_x, max_y = self.get_bounds()
        cols, rows = max_x - min_x + 1, max_y - min_y + 1
        padding = cell_size
        img_w, img_h = cols * cell_size + 2 * padding, rows * cell_size + 2 * padding
        
        svg_lines = [
            f'<svg width="{img_w}" height="{img_h}" viewBox="0 0 {img_w} {img_h}" xmlns="http://www.w3.org/2000/svg">'
        ]

        # Draw all cells
        for (gx, gy) in self.grid.keys():
            x = (gx - min_x) * cell_size + padding
            y = (gy - min_y) * cell_size + padding
            svg_lines.append(f'  <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="none" stroke="black" stroke-width="1" />')
            
            if solved:
                char = self.grid[(gx, gy)]
                char_x = x + cell_size / 2
                char_y = y + cell_size / 2
                font_size = int(cell_size * 0.6)
                svg_lines.append(f'  <text x="{char_x}" y="{char_y}" font-family="sans-serif" font-size="{font_size}" text-anchor="middle" dominant-baseline="central" fill="black">{char}</text>')

        # Draw numbers
        num_font_size = cell_size // 4
        for w in self.placed_words:
            x = (w['x'] - min_x) * cell_size + padding
            y = (w['y'] - min_y) * cell_size + padding
            svg_lines.append(f'  <text x="{x + 3}" y="{y + 2 + num_font_size}" font-family="sans-serif" font-size="{num_font_size}" fill="black">{w["final_num"]}</text>')

        svg_lines.append('</svg>')
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(svg_lines))
        
        print(f"Saved: {filename} ({cols}x{rows})")

    def to_suggestions(self, filename="suggestions.txt"):
        horizontal = sorted([w for w in self.placed_words if w['dir'] == 'H'], key=lambda x: x['final_num'])
        vertical = sorted([w for w in self.placed_words if w['dir'] == 'V'], key=lambda x: x['final_num'])

        with open(filename, "w", encoding='utf-8') as f:
            f.write("HORIZONTAL\n==========\n")
            for w in horizontal:
                f.write(f"{w['final_num']}. {w['hint']}\n")
            f.write("\nVERTICAL\n========\n")
            for w in vertical:
                f.write(f"{w['final_num']}. {w['hint']}\n")
        print(f"Saved: {filename}")

def main(csv_file):
    import os
    if not os.path.exists(csv_file):
        print(f"Error: File '{csv_file}' not found.")
        return

    words = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 2:
                words.append((row[0], row[1]))

    cw = CrosswordGenerator(words)
    cw.generate_best(attempts=150) # Even more attempts for density
    
    cw.draw_crossword("crossword.svg", solved=False)
    cw.draw_crossword("crossword_solved.svg", solved=True)
    cw.to_suggestions("suggestions.txt")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generatore di Cruciverba')
    parser.add_argument('csv_file', nargs='?', default='data.csv', help='Percorso del file CSV (default: data.csv)')
    args = parser.parse_args()
    
    main(args.csv_file)
