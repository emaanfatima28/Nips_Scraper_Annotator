import asyncio
import os
import re
import random
import time
import aiofiles
import aiohttp
from bs4 import BeautifulSoup

class NeuripsPaperFetcher:
    BASE_WEBSITE = "https://papers.nips.cc"
    RETRY_LIMIT = 5
    REQUEST_TIMEOUT = 180
    CONNECTIONS_LIMIT = 1  
    RETRY_DELAYS = [2, 4, 8, 16, 32]
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def __init__(self):
        self.download_folder = "papers"
        os.makedirs(self.download_folder, exist_ok=True)
        self.session_connector = aiohttp.TCPConnector(limit=self.CONNECTIONS_LIMIT)

    async def start_scraping(self):
        end_year = 2024
        begin_year = end_year - 5

        timeout_config = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT, connect=40, sock_read=180, sock_connect=40)
        async with aiohttp.ClientSession(timeout=timeout_config, connector=self.session_connector, headers=self.HEADERS) as session:
            tasks = [self.fetch_papers_by_year(session, year) for year in range(begin_year, end_year + 1)]
            await asyncio.gather(*tasks)

    async def fetch_papers_by_year(self, session, year):
        year_url = f"{self.BASE_WEBSITE}/paper_files/paper/{year}"
        print(f"Retrieving papers from: {year_url}")
        try:
            async with session.get(year_url) as response:
                if response.status != 200:
                    print(f"Failed to retrieve {year_url}, Status: {response.status}")
                    return
                page_content = await response.text()
                soup = BeautifulSoup(page_content, 'html.parser')
                paper_links = soup.select('body > div.container-fluid > div > ul  li a[href]')
                if not paper_links:
                    print(f"No papers found for {year}.")
                    return
                print(f"Discovered {len(paper_links)} papers for {year}")

                # Process each paper with a slight delay
                for paper in paper_links:
                    await self.process_paper(session, year, paper)
                    await asyncio.sleep(random.uniform(2, 5))  # Random delay between 2-5 seconds

        except Exception as err:
            print(f"Error fetching {year_url}: {err}")

    async def process_paper(self, session, year, paper):
        paper_title = paper.text.strip()
        paper_page = f"{self.BASE_WEBSITE}{paper['href']}"
        
        # Fetch the paper's details page to get the correct PDF link
        try:
            async with session.get(paper_page) as response:
                if response.status != 200:
                    print(f"Failed to retrieve {paper_page}, Status: {response.status}")
                    return
                page_content = await response.text()
                soup = BeautifulSoup(page_content, 'html.parser')

                # Find the actual PDF download link
                pdf_link = soup.select_one('a[href$=".pdf"]')
                if not pdf_link:
                    print(f"No PDF link found for {paper_title}")
                    return

                pdf_url = f"{self.BASE_WEBSITE}{pdf_link['href']}"
                
                # Clean title for valid filename
                clean_title = re.sub(r'[<>:"/\\|?*]', '_', paper_title) + ".pdf"
                await self.download_pdf_file(session, pdf_url, clean_title)
        except Exception as err:
            print(f"Error processing {paper_page}: {err}")

    async def download_pdf_file(self, session, pdf_url, file_name):
        return await self.retry_request(session, pdf_url, self._save_pdf, file_name)

    async def _save_pdf(self, session, pdf_url, file_name):
        try:
            async with session.get(pdf_url) as response:
                if response.status == 200:
                    file_path = os.path.join(self.download_folder, file_name)
                    os.makedirs(self.download_folder, exist_ok=True)
                    async with aiofiles.open(file_path, mode='wb') as f:
                        await f.write(await response.read())
                    print(f"Successfully downloaded: {file_name}")
                    return True
                else:
                    print(f"Failed to download {file_name}, Status: {response.status}")
                    return False
        except Exception as err:
            print(f"Error downloading {pdf_url}: {err}")
            return False

    async def retry_request(self, session, url, func, *args, retries=RETRY_LIMIT):
        for attempt, delay in enumerate(self.RETRY_DELAYS, start=1):
            try:
                return await func(session, url, *args)
            except (aiohttp.ClientError, ConnectionResetError, asyncio.TimeoutError, aiohttp.ServerDisconnectedError) as err:
                print(f"Retry {attempt} failed for {url}: {err}")
                if attempt == retries:
                    print(f"All retries failed for {url}")
                    return None
                print(f"Waiting {delay} seconds before retrying {url}...")
                time.sleep(delay)  # Blocking sleep to avoid too many requests
        return None

async def run():
    scraper = NeuripsPaperFetcher()
    await scraper.start_scraping()

if __name__ == "__main__":
    asyncio.run(run())
