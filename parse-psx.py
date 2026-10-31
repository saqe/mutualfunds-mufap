import argparse
import sys
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString


INPUT = Path("files/psx.html")
HTML_OUTPUT = Path("files/psx-table.html")
HTML_COLUMNS = (
    "symbol",
    "marketCap",
    "close",
    "percentChange",
    "changeYear",
    "peRatio",
    "dividendYield",
)


def main():
    parser = argparse.ArgumentParser(description="Parse the PSX screener table")
    parser.add_argument("--html-output", type=Path, default=HTML_OUTPUT)
    parser.add_argument("--limit", type=int, help="Limit output to the first N rows")
    args = parser.parse_args()

    if not INPUT.is_file():
        raise FileNotFoundError(f"Input HTML not found: {INPUT}")

    soup = BeautifulSoup(INPUT.read_text(encoding="utf-8"), "html.parser")
    table = soup.find("table", id="screenerTable")
    if table is None:
        raise ValueError("Could not find the PSX screener table (screenerTable)")

    header_cells = table.select("thead th")
    if not header_cells:
        raise ValueError("The PSX screener table has no column headers")

    column_indexes = {
        th.get("data-name"): index for index, th in enumerate(header_cells)
    }
    missing_columns = [column for column in HTML_COLUMNS if column not in column_indexes]
    if missing_columns:
        raise ValueError(f"Missing PSX table columns: {', '.join(missing_columns)}")

    selected_indexes = [column_indexes[column] for column in HTML_COLUMNS]
    rows = table.select("tbody tr")

    if args.limit is not None:
        if args.limit < 0:
            raise ValueError("--limit must be zero or greater")
        for row in rows[args.limit :]:
            row.decompose()

    for row in table.select("tr"):
        cells = row.find_all(["th", "td"], recursive=False)
        for index in reversed(range(len(cells))):
            cell = cells[index]
            if index not in selected_indexes:
                cell.decompose()
                continue

            for tag in cell.select(".tag"):
                tag.decompose()

            if cell.name == "th":
                value = " ".join(cell.stripped_strings)
            else:
                value = cell.get("data-order")
                if value is None:
                    value = " ".join(cell.stripped_strings)
                else:
                    value = value.strip()

            cell.clear()
            cell.attrs.clear()
            if value:
                cell.append(NavigableString(value))
        row.attrs.clear()

    for section in table.select("thead, tbody, tfoot"):
        section.unwrap()
    table.attrs.clear()

    args.html_output.parent.mkdir(parents=True, exist_ok=True)
    args.html_output.write_text(table.prettify() + "\n", encoding="utf-8")

    print(f"Wrote {len(rows)} cleaned PSX rows to {args.html_output}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
