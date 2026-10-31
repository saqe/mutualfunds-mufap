import csv
import html
import sys
from pathlib import Path

from bs4 import BeautifulSoup


INPUT = Path("files/psx.html")
OUTPUT = Path("files/psx.csv")
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

    column_indexes = [headers.index(column) for column in HTML_COLUMNS]
    header_labels = {
        th.get("data-name"): " ".join(th.stripped_strings)
        for th in table.select("thead th")
    }
    html_rows = [
        [row[index] if index < len(row) else "" for index in column_indexes]
        for row in rows
    ]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as output_file:
        writer = csv.writer(output_file)
        writer.writerow(headers)
        writer.writerows(rows)

    html_table = ["<table>", "  <tr>"]
    html_table.extend(
        f"    <th>{html.escape(header_labels[column])}</th>"
        for column in HTML_COLUMNS
    )
    html_table.append("  </tr>")
    for row in html_rows:
        html_table.append("  <tr>")
        html_table.extend(f"    <td>{html.escape(value)}</td>" for value in row)
        html_table.append("  </tr>")
    html_table.extend(["</table>", ""])
    HTML_OUTPUT.write_text("\n".join(html_table), encoding="utf-8")

    print(f"Wrote {len(rows)} cleaned PSX rows to {OUTPUT} and {HTML_OUTPUT}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
