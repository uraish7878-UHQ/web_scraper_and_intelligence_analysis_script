import time
import matplotlib.pyplot as plt
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Dictionary mapping word ratings to numerical integers (1-5)
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def scrape_books(max_pages=5, scrape_all=False):
    """Scrapes book data from books.toscrape.com.

    Parameters:
    - max_pages (int): Number of pages to scrape (e.g., 3 or 5).
    - scrape_all (bool): Set True for Boss Level (scrapes all 50 catalog pages).

    Returns:
    - pd.DataFrame: Cleaned competitor dataset.
    """
    base_catalog_url = "https://books.toscrape.com/catalogue/"
    current_page_url = "https://books.toscrape.com/catalogue/page-1.html"

    records = []
    page_count = 0

    print("==================================================")
    print("   STARTING BOOKSTORE INTELLIGENCE SCRAPER")
    print("==================================================")

    while current_page_url:
        page_count += 1
        print(f"-> Scraping Page {page_count}: {current_page_url}")

        response = requests.get(
            current_page_url, headers={"User-Agent": "Mozilla/5.0"}
        )
        if response.status_code != 200:
            print(f"Failed to load page. Status Code: {response.status_code}")
            break

        soup = BeautifulSoup(response.content, "html.parser")
        product_pods = soup.find_all("article", class_="product_pod")

        for pod in product_pods:
            # 1. Title (Extract full untruncated string from 'title' attribute)
            a_tag = pod.find("h3").find("a")
            title = a_tag.get("title", a_tag.text.strip())

            # 2. Price Cleaning (£ symbol removal and conversion to float)
            raw_price = pod.find("p", class_="price_color").text
            price_clean = (
                raw_price.encode("ascii", "ignore")
                .decode("ascii")
                .replace("£", "")
                .strip()
            )
            price = float(price_clean)

            # 3. Rating Conversion (Word to integer 1-5)
            rating_classes = pod.find("p", class_="star-rating")["class"]
            rating_word = (
                rating_classes[1]
                if len(rating_classes) > 1
                else rating_classes[0]
            )
            rating = RATING_MAP.get(rating_word, 0)

            # 4. Stock Availability Cleaning
            availability = pod.find(
                "p", class_="instock availability"
            ).text.strip()

            # 5. Product Page URL (Bonus 2)
            rel_href = a_tag["href"]
            if rel_href.startswith("catalogue/"):
                full_url = f"https://books.toscrape.com/{rel_href}"
            else:
                full_url = f"https://books.toscrape.com/catalogue/{rel_href}"

            records.append(
                {
                    "Title": title,
                    "Price": price,
                    "Rating": rating,
                    "Availability": availability,
                    "URL": full_url,
                }
            )

        # Pagination Logic (Find Next button)
        next_button = soup.find("li", class_="next")
        if next_button and (scrape_all or page_count < max_pages):
            next_page_rel = next_button.find("a")["href"]
            current_page_url = f"{base_catalog_url}{next_page_rel}"
        else:
            current_page_url = None

        time.sleep(0.2)  # Politeness delay

    df = pd.DataFrame(records)
    df.to_csv("competitor_books.csv", index=False)
    print(
        f"\n[SUCCESS] Scraped {len(df)} records across {page_count} page(s)."
    )
    print("[FILE SAVED] Output written to 'competitor_books.csv'\n")
    return df


def run_intelligence_analysis(df):
    """Executes Pandas queries for Mission 4 & CEO Challenge."""
    print("==================================================")
    print("          MISSION 4: INTELLIGENCE ANALYSIS")
    print("==================================================")

    # Question 1
    most_exp = df.loc[df["Price"].idxmax()]
    print(
        f"1. Most Expensive Book: '{most_exp['Title']}' (£{most_exp['Price']:.2f})"
    )

    # Question 2
    cheapest = df.loc[df["Price"].idxmin()]
    print(
        f"2. Cheapest Book: '{cheapest['Title']}' (£{cheapest['Price']:.2f})"
    )

    # Question 3
    avg_p = df["Price"].mean()
    print(f"3. Average Book Price: £{avg_p:.2f}")

    # Question 4
    five_star_cnt = (df["Rating"] == 5).sum()
    print(f"4. Count of 5-Star Books: {five_star_cnt}")

    # Question 5
    in_stock_pct = (df["Availability"].str.contains("In stock").mean()) * 100
    print(f"5. Percentage In-Stock: {in_stock_pct:.1f}%")

    # Question 6
    top_5 = df.sort_values(
        by=["Rating", "Price"], ascending=[False, True]
    ).head(5)
    print("\n6. Top 5 Highest-Rated Books (Ranked by Rating, then Price):")
    for idx, row in top_5.reset_index(drop=True).iterrows():
        print(
            f"   {idx+1}. {row['Title']} - {row['Rating']} Stars (£{row['Price']:.2f})"
        )

    # Question 7
    cheapest_5 = df[df["Rating"] == 5].sort_values(by="Price").iloc[0]
    print(
        f"\n7. Cheapest 5-Star Book: '{cheapest_5['Title']}' (£{cheapest_5['Price']:.2f})"
    )

    # CEO £100 Challenge
    print("\n==================================================")
    print("          CEO £100 MARKET-RESEARCH CHALLENGE")
    print("==================================================")
    df_sorted = df.sort_values(by=["Rating", "Price"], ascending=[False, True])

    budget = 100.00
    spent = 0.0
    total_stars = 0
    portfolio = []

    for _, row in df_sorted.iterrows():
        if spent + row["Price"] <= budget:
            portfolio.append(row)
            spent += row["Price"]
            total_stars += row["Rating"]

    ceo_df = pd.DataFrame(portfolio)
    print(f"Budget: £{budget:.2f} | Total Spent: £{spent:.2f} | Remaining: £{budget - spent:.2f}")
    print(f"Total Cumulative Star Score: {total_stars} Stars")
    print(f"Total Books Purchased: {len(ceo_df)}\n")
    print(ceo_df[["Title", "Price", "Rating"]].to_string(index=False))


def generate_rating_chart(df):
    """Generates and saves a bar chart of star ratings (Bonus 4)."""
    rating_counts = df["Rating"].value_counts().sort_index(ascending=True)

    plt.figure(figsize=(8, 5))
    bars = plt.bar(
        rating_counts.index,
        rating_counts.values,
        color="#2b5c8f",
        edgecolor="black",
    )

    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            yval + 0.3,
            int(yval),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    plt.title("Competitor Book Catalog: Star Rating Distribution", fontsize=14)
    plt.xlabel("Star Rating (1-5)", fontsize=12)
    plt.ylabel("Number of Books", fontsize=12)
    plt.xticks([1, 2, 3, 4, 5])
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()
    plt.savefig("rating_distribution.png", dpi=300)
    print("\n[CHART SAVED] Chart output written to 'rating_distribution.png'")


if __name__ == "__main__":
    # Scrape 5 pages (Bonus Mission 1)
    df_data = scrape_books(max_pages=5, scrape_all=False)

    # Run Analysis
    run_intelligence_analysis(df_data)

    # Plot Chart
    generate_rating_chart(df_data)