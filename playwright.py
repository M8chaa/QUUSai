async def fetch_and_process_url(url, session, playwright, semaphore):
    async with semaphore:  # This will block if the limit is reached
        browser = await playwright.chromium.launch()
        context = await browser.new_context()
        page = await context.new_page()
        try:
            response = await page.goto("https://www.moyoplan.com/plans/13793", wait_until='domcontentloaded')
            if response.ok:  # Checks if the response status is 200-299
                # Proceed if the main document loads successfully
                asyncio.create_task(process_page_content(page, url, session, playwright, semaphore))
            else:
                # Handle non-2xx status codes
                print(f"Failed to load {url}: {response.status()}")
        except TimeoutError as e:
            # Handle timeout exceptions
            print(f"Timeout while loading {url}: {e}")

    cpu_percent = psutil.cpu_percent()
    memory_info = psutil.virtual_memory()
    memory_percent = memory_info.percent
    print(f"CPU: {cpu_percent}%, Physical Memory: {memory_percent}%")

async def process_page_content(page, url, session, playwright, semaphore):
    attempts = 0
    try:
        html_content = await page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        strSoup = soup.get_text()
        await page.wait_for_selector(".css-yg1ktq", state="attached")
        await page.click(".css-yg1ktq")
        사은품_링크_element = await page.query_selector('a.css-1hdj7cf.e17wbb0s4')
        사은품_링크 = await 사은품_링크_element.get_attribute('href') if 사은품_링크_element else None

        카드할인_링크_element = await page.query_selector('a.css-pnutty.ema3yz60')
        카드할인_링크 = await 카드할인_링크_element.get_attribute('href') if 카드할인_링크_element else None

        regex_formula = regex_extract(strSoup)
        if regex_formula[18] != "제공안함" and 사은품_링크 is not None:
            regex_formula[18] += (f", link:{사은품_링크}")
        if regex_formula[19] != "제공안함" and 카드할인_링크 is not None:
            regex_formula[19] += (f", link:{카드할인_링크}")
        planUrl = str(url)
        data = [planUrl] + regex_formula
        print(f"Data queued for {url}\n {data}")
    except Exception as e:
        attempts += 1
        print(f"Attempt {attempts} failed for {url}: {e}, retrying...////////////////////////")
        if attempts == 5:
            print(f"Failed to fetch data after 5 attempts for URL: {url}")
        else:
            asyncio.create_task(fetch_and_process_url(url, session, playwright, semaphore))  # Refresh with the same URL
    finally:
        if page:
            await page.close()
    if stop_signal.is_set():
        return



async def fetch_url_list(session, playwright, semaphore, base_url="https://www.moyoplan.com/plans"):
    i = 1
    end_of_list = False
    tasks = []
    while not end_of_list:
        plan_list_url = f"{base_url}?page={i}"
        async with session.get(plan_list_url) as response:
            if response.status != 200:
                print(f"Failed to fetch data from {plan_list_url}. Status code: {response.status}")
                break
            soup = BeautifulSoup(await response.text(), 'html.parser')
            a_tags = soup.find_all('a', class_='e3509g015')
            if not a_tags:
                end_of_list = True
                break
            for a_tag in a_tags:
                link = a_tag['href']
                Baseurl = "https://www.moyoplan.com"
                full_url = f"{Baseurl}{link}"
                
                # Monitor system resources (This part seems to be for debugging/monitoring, ensure it's necessary for your final use case)
                # system monitoring output...
                task = asyncio.create_task(fetch_and_process_url(full_url, session, playwright, semaphore))
                tasks.append(task)
                if len(tasks) > 3:
                    await asyncio.gather(*tasks)
                    tasks = []
            i += 1
    if tasks:
        await asyncio.gather(*tasks)

async def main():
    async with aiohttp.ClientSession() as session, async_playwright() as playwright:
        semaphore = asyncio.Semaphore(5)  # Adjusted to limit to 3 concurrent browsers
        await fetch_url_list(session, playwright, semaphore, base_url="https://www.moyoplan.com/plans")

asyncio.run(main())