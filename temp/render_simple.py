import asyncio, os
from playwright.async_api import async_playwright
from pypdf import PdfWriter, PdfReader

TEMP = 'C:/Users/richm/.claude/temp'
HTML = f'{TEMP}/unreleased_simple.html'
OUT  = f'{TEMP}/Claude_Code_Unreleased_4Slides.pdf'

async def render():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1080, 'height': 1080})
        await page.goto(f'file:///{HTML}')
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(3000)

        heights = await page.evaluate(
            'Array.from(document.querySelectorAll(".page")).map(el => el.scrollHeight)'
        )
        print(f'Page heights: {heights}')

        page_files = []
        for i, h in enumerate(heights):
            path = f'{TEMP}/simple_page_{i:02d}.pdf'
            await page.evaluate(f'''
                var pages = document.querySelectorAll(".page");
                pages.forEach(function(p, idx) {{
                    p.style.display = idx === {i} ? "flex" : "none";
                }});
            ''')
            await page.pdf(
                path=path,
                width='1080px',
                height=f'{h + 2}px',
                print_background=True,
                margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'}
            )
            page_files.append(path)
            print(f'  Page {i+1}/{len(heights)}: {h}px')

        await browser.close()

        writer = PdfWriter()
        for path in page_files:
            for pg in PdfReader(path).pages:
                writer.add_page(pg)

        with open(OUT, 'wb') as f:
            writer.write(f)

        for path in page_files:
            os.remove(path)

        print(f'\nDone: {OUT}')

asyncio.run(render())
