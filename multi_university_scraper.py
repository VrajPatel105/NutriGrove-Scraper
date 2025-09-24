import asyncio
import concurrent.futures
from datetime import datetime
import os
import time
from scraper import Scraper
from clean_data import FoodDataCleaner
from database import SupabaseUploader
from university_config import UniversityConfig

class MultiUniversityScraper:
    def __init__(self, date=None):
        self.date = date or datetime.today().strftime('%Y-%m-%d')
        self.is_weekend = datetime.today().weekday() >= 5  # Saturday=5, Sunday=6
        self.universities = UniversityConfig.get_all_universities()
        print(f"Initialized multi-university scraper for {self.date}")
        print(f"Weekend mode: {self.is_weekend}")
        print(f"Universities to scrape: {list(self.universities.keys())}")

    def scrape_university(self, university_key):
        """Scrape a single university - designed to run in parallel"""
        print(f"\n{'='*60}")
        print(f"Starting scraper for {university_key}")
        print(f"{'='*60}")

        scraper = None
        success = False

        try:
            # Check if this is Harvard (API-based)
            from university_config import UniversityConfig
            config = UniversityConfig.get_university_config(university_key)
            if config and config.get('api_based', False):
                print(f"Using API scraper for {university_key}")
                from harvard_api_scraper import scrape_harvard
                success = scrape_harvard(self.date)
            else:
                # Use regular web scraper
                scraper = Scraper(self.date, university_key)

                # Scrape meals based on weekend/weekday
                if self.is_weekend:
                    print(f"Weekend detected for {university_key} - scraping brunch and dinner only")
                    scraper.fetch_breakfast()  # This will contain brunch items
                    scraper.fetch_dinner()
                else:
                    print(f"Weekday detected for {university_key} - scraping all three meals")
                    scraper.fetch_breakfast()
                    scraper.fetch_lunch()
                    scraper.fetch_dinner()

                success = True

            print(f"Successfully completed scraping for {university_key}")

        except Exception as e:
            print(f"Error scraping {university_key}: {str(e)}")
            success = False

        finally:
            if scraper:
                scraper.close()

        return {
            'university': university_key,
            'success': success,
            'scraped_at': datetime.now().isoformat()
        }

    def clean_and_upload_university_data(self, university_key):
        """Clean and upload data for a single university"""
        try:
            # Check if this is Harvard (API-based) - skip cleaning as it's already uploaded
            from university_config import UniversityConfig
            config = UniversityConfig.get_university_config(university_key)
            if config and config.get('api_based', False):
                print(f"Skipping data cleaning for {university_key} - API data already processed and uploaded")
                return True

            print(f"\nCleaning data for {university_key}...")

            # Initialize cleaner with university-specific paths
            cleaner = FoodDataCleaner(university_key)
            cleaned_files = cleaner.clean_food_data()

            if not cleaned_files:
                print(f"No cleaned data files found for {university_key}")
                return False

            # Get database name for this university
            database_name = UniversityConfig.get_database_name(university_key)

            print(f"Uploading data to database '{database_name}' for {university_key}...")

            # Initialize uploader with university-specific database
            uploader = SupabaseUploader(database_name)

            # Upload each cleaned file
            for file_path in cleaned_files:
                if os.path.exists(file_path):
                    uploader.upload_json_file(file_path)
                    print(f"Uploaded {file_path}")
                else:
                    print(f"File not found: {file_path}")

            print(f"Successfully processed data for {university_key}")
            return True

        except Exception as e:
            print(f"Error processing data for {university_key}: {str(e)}")
            return False

    def run_parallel_scraping(self, max_workers=4):
        """Run scraping for all universities in parallel"""
        print(f"\nStarting parallel scraping with {max_workers} workers...")

        results = []

        # Use ThreadPoolExecutor for parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit scraping jobs for all universities
            future_to_university = {
                executor.submit(self.scrape_university, uni_key): uni_key
                for uni_key in self.universities.keys()
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_university):
                university_key = future_to_university[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    print(f"Exception occurred for {university_key}: {str(e)}")
                    results.append({
                        'university': university_key,
                        'success': False,
                        'error': str(e),
                        'scraped_at': datetime.now().isoformat()
                    })

        return results

    def run_parallel_processing(self, max_workers=4):
        """Clean and upload data for all universities in parallel"""
        print(f"\nStarting parallel data processing with {max_workers} workers...")

        processing_results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit processing jobs for all universities
            future_to_university = {
                executor.submit(self.clean_and_upload_university_data, uni_key): uni_key
                for uni_key in self.universities.keys()
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_university):
                university_key = future_to_university[future]
                try:
                    success = future.result()
                    processing_results.append({
                        'university': university_key,
                        'processing_success': success,
                        'processed_at': datetime.now().isoformat()
                    })
                except Exception as e:
                    print(f"Processing exception for {university_key}: {str(e)}")
                    processing_results.append({
                        'university': university_key,
                        'processing_success': False,
                        'error': str(e),
                        'processed_at': datetime.now().isoformat()
                    })

        return processing_results

    def run_complete_pipeline(self, max_workers=4):
        """Run the complete scraping and processing pipeline"""
        start_time = time.time()

        print(f"\nStarting complete multi-university scraping pipeline")
        print(f"Date: {self.date}")
        print(f"Universities: {', '.join(self.universities.keys())}")
        print(f"Max parallel workers: {max_workers}")

        # Step 1: Parallel scraping
        scraping_results = self.run_parallel_scraping(max_workers)

        # Step 2: Parallel data cleaning and uploading
        processing_results = self.run_parallel_processing(max_workers)

        # Summary
        end_time = time.time()
        total_time = end_time - start_time

        print(f"\n{'='*80}")
        print(f"MULTI-UNIVERSITY SCRAPING COMPLETE")
        print(f"{'='*80}")
        print(f"Total execution time: {total_time:.2f} seconds")
        print(f"Date processed: {self.date}")

        # Scraping summary
        successful_scrapes = sum(1 for r in scraping_results if r['success'])
        print(f"\nScraping Results:")
        print(f"Successful: {successful_scrapes}/{len(scraping_results)}")

        for result in scraping_results:
            status = "SUCCESS" if result['success'] else "FAILED"
            print(f"  {status} {result['university']}")

        # Processing summary
        successful_processing = sum(1 for r in processing_results if r['processing_success'])
        print(f"\nProcessing Results:")
        print(f"Successful: {successful_processing}/{len(processing_results)}")

        for result in processing_results:
            status = "SUCCESS" if result['processing_success'] else "FAILED"
            print(f"  {status} {result['university']}")

        print(f"\n{'='*80}")

        return {
            'scraping_results': scraping_results,
            'processing_results': processing_results,
            'total_time': total_time,
            'successful_scrapes': successful_scrapes,
            'successful_processing': successful_processing,
            'date': self.date
        }

if __name__ == "__main__":
    # Create and run the multi-university scraper
    multi_scraper = MultiUniversityScraper()
    results = multi_scraper.run_complete_pipeline(max_workers=4)