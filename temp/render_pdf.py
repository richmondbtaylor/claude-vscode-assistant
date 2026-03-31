import asyncio, os
from playwright.async_api import async_playwright
from pypdf import PdfWriter, PdfReader

TEMP = 'C:/Users/richm/.claude/temp'
OUT  = f'{TEMP}/ESAF_GTM_Proposal_Wendy_BishopAI.pdf'

async def render():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={'width': 1100, 'height': 900})
        await page.goto('file:///C:/Users/richm/.claude/temp/esaf_proposal_pa.html')
        await page.wait_for_load_state('networkidle')
        await page.wait_for_timeout(2000)

        heights = await page.evaluate(
            'Array.from(document.querySelectorAll(".page")).map(el => el.scrollHeight)'
        )
        print(f'Page heights: {heights}')

        page_files = []
        for i, h in enumerate(heights):
            path = f'{TEMP}/page_{i:02d}.pdf'
            await page.evaluate(f'''
                var pages = document.querySelectorAll(".page");
                pages.forEach(function(p, idx) {{
                    p.style.display = idx === {i} ? "flex" : "none";
                }});
            ''')
            margin = {'top': '0', 'right': '0', 'bottom': '0', 'left': '0'}
            await page.pdf(
                path=path,
                width='1100px',
                height=f'{h + 2}px',
                print_background=True,
                margin=margin
            )
            page_files.append(path)
            print(f'  Page {i+1}: {h}px')

        await browser.close()

        writer = PdfWriter()
        for path in page_files:
            reader = PdfReader(path)
            for pg in reader.pages:
                writer.add_page(pg)

        with open(OUT, 'wb') as f:
            writer.write(f)

        for path in page_files:
            os.remove(path)

        print(f'Done: {OUT}')

asyncio.run(render())
