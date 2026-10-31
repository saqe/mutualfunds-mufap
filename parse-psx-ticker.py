import sys
from pathlib import Path
import argparse

from bs4 import BeautifulSoup, NavigableString


HEADERS = (
    "SYMBOL",
    "MARKET CAP.",
    "PRICE",
    "CHANGE (%)",
    "1-YEAR CH. (%) *",
    "PE RATIO (TTM)",
    "DIVIDEND YIELD (%)",
)


def text_or_na(element):
    return " ".join(element.stripped_strings) if element else "N/A"


def ticker_values(input_path, ticker):
    if not input_path.is_file():
        raise FileNotFoundError(f"Input HTML not found: {input_path}")

    source = BeautifulSoup(input_path.read_text(encoding="utf-8"), "html.parser")
    quote = source.select_one(".quote__price")
    if quote is None:
        raise ValueError(f"Could not find quote values for {ticker}")

    price = text_or_na(quote.select_one(".quote__close"))
    if price.startswith("Rs."):
        price = price.removeprefix("Rs.").strip()

    change = text_or_na(quote.select_one(".quote__change .change__percent"))
    if change != "N/A":
        change = change.strip("() ")

    pe_ratio = "N/A"
    regular_panel = source.select_one('.tabs__panel[data-name="REG"]')
    if regular_panel:
        for item in regular_panel.select(".stats_item"):
            label = text_or_na(item.select_one(".stats_label"))
            if label.startswith("P/E Ratio"):
                pe_ratio = text_or_na(item.select_one(".stats_value"))
                break

    # These metrics are not provided on either ETF quote page.
    return (ticker, "N/A", price, change, "N/A", pe_ratio, "N/A")


def render_table(values):
    soup = BeautifulSoup("", "html.parser")
    table = soup.new_tag("table")

    for cells, tag_name in ((HEADERS, "th"), (values, "td")):
        row = soup.new_tag("tr")
        for value in cells:
            cell = soup.new_tag(tag_name)
            cell.append(NavigableString(value))
            row.append(cell)
        table.append(row)

    return table.prettify() + "\n"


def main():
    parser = argparse.ArgumentParser(description="Extract a PSX ETF ticker summary")
    parser.add_argument("input_file", type=Path, help="Saved PSX ticker HTML file")
    parser.add_argument("output_file", type=Path, help="Output HTML table file")
    args = parser.parse_args()

    ticker = args.input_file.stem.upper()
    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    args.output_file.write_text(
        render_table(ticker_values(args.input_file, ticker)), encoding="utf-8"
    )
    print(f"Wrote {ticker} values to {args.output_file}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
