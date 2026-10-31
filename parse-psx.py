import csv
import sys
from pathlib import Path

from bs4 import BeautifulSoup


INPUT = Path("files/psx.html")
OUTPUT = Path("files/psx.csv")


def clean_cell(cell):
    """Return a plain, stable value for a screener table cell."""
    for tag in cell.select(".tag"):
        tag.decompose()

    ordered_value = cell.get("data-order")
    if ordered_value is not None:
        return ordered_value.strip()
    return " ".join(cell.stripped_strings)


def main():
    if not INPUT.is_file():
        raise FileNotFoundError(f"Input HTML not found: {INPUT}")

    soup = BeautifulSoup(INPUT.read_text(encoding="utf-8"), "html.parser")
    table = soup.find("table", id="screenerTable")
    if table is None:
        raise ValueError("Could not find the PSX screener table (screenerTable)")

    headers = [
        th.get("data-name") or " ".join(th.stripped_strings)
        for th in table.select("thead th")
    ]
    if not headers:
        raise ValueError("The PSX screener table has no column headers")

    rows = []
    for tr in table.select("tbody tr"):
        cells = tr.find_all("td", recursive=False)
        if not cells:
            continue
        values = [clean_cell(cell) for cell in cells]
        if len(values) < len(headers):
            values.extend([""] * (len(headers) - len(values)))
        rows.append(values[: len(headers)])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(headers)
        writer.writerows(rows)

    print(f"Wrote {len(rows)} cleaned PSX rows to {OUTPUT}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
