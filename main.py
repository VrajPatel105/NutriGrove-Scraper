"""
Multi-University Food Scraping Script
Scrapes food data from multiple universities in parallel
"""

from multi_university_scraper import MultiUniversityScraper
from datetime import datetime
import sys

def main():
    print("Starting Multi-University Food Data Scraping")
    print("=" * 60)

    try:
        # Use today's date or accept date from command line
        if len(sys.argv) > 1:
            date = sys.argv[1]
            print(f"Using provided date: {date}")
        else:
            date = datetime.today().strftime('%Y-%m-%d')
            print(f"Using today's date: {date}")

        # Initialize and run multi-university scraper
        multi_scraper = MultiUniversityScraper(date)

        # Run complete pipeline with 4 parallel workers (adjust as needed)
        results = multi_scraper.run_complete_pipeline(max_workers=4)

        # Exit with success/failure code
        total_universities = len(results['scraping_results'])
        successful_scrapes = results['successful_scrapes']
        successful_processing = results['successful_processing']

        if successful_scrapes == total_universities and successful_processing == total_universities:
            print(f"All {total_universities} universities processed successfully!")
            sys.exit(0)
        else:
            print(f"Some universities failed. Scraping: {successful_scrapes}/{total_universities}, Processing: {successful_processing}/{total_universities}")
            sys.exit(1)

    except Exception as e:
        print(f"Fatal error in multi-university scraper: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
