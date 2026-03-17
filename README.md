# Crossword Generator

A script to generate crossword puzzles from a CSV file containing hints and words.

## Requirements

- Python 3.14+
- Pillow

## Usage

### With uv

```
uv sync
uv run main.py [path/to/your_file.csv]
```

### Without uv

```bash
pip install Pillow
python main.py [path/to/your_file.csv]
```

## CSV Format

The CSV file should use a semicolon (`;`) as a separator:

```csv
hint;word
hint;word
...
```
