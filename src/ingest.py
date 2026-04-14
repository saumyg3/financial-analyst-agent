import requests
import os
import json

HEADERS = {"User-Agent": "financial-analyst-agent saumyg3@uci.edu"}

def get_cik(ticker: str) -> str:
    """Convert a stock ticker (e.g. AAPL) to SEC's internal company ID (CIK)."""
    url = "https://efts.sec.gov/LATEST/search-index?q=%22{}%22&dateRange=custom&startdt=2020-01-01&enddt=2024-12-31&forms=10-K".format(ticker)
    
    # SEC has a handy ticker→CIK mapping file
    mapping_url = "https://www.sec.gov/files/company_tickers.json"
    response = requests.get(mapping_url, headers=HEADERS)
    data = response.json()
    
    # Search through the mapping for our ticker
    for entry in data.values():
        if entry["ticker"].upper() == ticker.upper():
            # CIK needs to be 10 digits, padded with zeros
            return str(entry["cik_str"]).zfill(10)
    
    raise ValueError(f"Ticker '{ticker}' not found in SEC database")


def get_latest_10k_url(cik: str) -> tuple[str, str]:
    """Given a CIK, find the most recent 10-K filing and return its text file URL."""
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    
    filings = data["filings"]["recent"]
    forms = filings["form"]
    accession_numbers = filings["accessionNumber"]
    filing_dates = filings["filingDate"]
    
    # Find the most recent 10-K
    for i, form in enumerate(forms):
        if form == "10-K":
            accession = accession_numbers[i].replace("-", "")
            date = filing_dates[i]
            
            # Build the URL to the filing index page
            index_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{accession_numbers[i]}-index.htm"
            return index_url, date
    
    raise ValueError(f"No 10-K found for CIK {cik}")


def get_10k_text(index_url: str) -> str:
    """Scrape the filing index page to find and download the actual 10-K text."""
    response = requests.get(index_url, headers=HEADERS)
    
    # Find the main document link from the index page
    from html.parser import HTMLParser
    
    class LinkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.links = []
        
        def handle_starttag(self, tag, attrs):
            if tag == "a":
                attrs_dict = dict(attrs)
                if "href" in attrs_dict:
                    self.links.append(attrs_dict["href"])
    
    parser = LinkParser()
    parser.feed(response.text)
    
    # Look for the .htm file that is the actual 10-K document
    base_url = "https://www.sec.gov"
    for link in parser.links:
        if link.endswith(".htm") and "index" not in link.lower():
            # Strip the XBRL viewer wrapper SEC sometimes adds
            raw = base_url + link if link.startswith("/") else link
            doc_url = raw.replace("https://www.sec.gov/ix?doc=", "https://www.sec.gov")
            print(f"  Downloading filing from: {doc_url}")
            doc_response = requests.get(doc_url, headers=HEADERS)
            
            # Strip HTML tags to get plain text
            from html.parser import HTMLParser
            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                    self.skip = False
                
                def handle_starttag(self, tag, attrs):
                    if tag in ["script", "style"]:
                        self.skip = True
                
                def handle_endtag(self, tag):
                    if tag in ["script", "style"]:
                        self.skip = False
                
                def handle_data(self, data):
                    if not self.skip:
                        stripped = data.strip()
                        if stripped:
                            self.text_parts.append(stripped)
            
            extractor = TextExtractor()
            extractor.feed(doc_response.text)
            return "\n".join(extractor.text_parts)
    
    raise ValueError("Could not find 10-K document in filing index")


def fetch_and_save(ticker: str) -> str:
    """
    Main function: given a ticker symbol, fetch its latest 10-K and save to data/.
    Returns the path to the saved file.
    """
    print(f"[1/3] Looking up CIK for {ticker}...")
    cik = get_cik(ticker)
    print(f"  Found CIK: {cik}")
    
    print(f"[2/3] Finding latest 10-K filing...")
    index_url, date = get_latest_10k_url(cik)
    print(f"  Found 10-K filed on: {date}")
    
    print(f"[3/3] Downloading filing text...")
    text = get_10k_text(index_url)
    
    # Save to data/ folder
    output_path = f"data/{ticker.upper()}_{date}.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"  Saved {len(text):,} characters to {output_path}")
    return output_path


if __name__ == "__main__":
    # Test it — fetch Apple's latest 10-K
    path = fetch_and_save("AAPL")
    print(f"\nDone! File saved to: {path}")