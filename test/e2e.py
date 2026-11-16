import asyncio, sys
from playwright.async_api import async_playwright
URL = "http://127.0.0.1:8765/"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox","--use-fake-device-for-media-stream","--use-fake-ui-for-media-stream","--autoplay-policy=no-user-gesture-required"])
        ctx = await b.new_context(locale="ko-KR", viewport={"width":900,"height":900})
        pg = await ctx.new_page(); errs=[]
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("console", lambda m: errs.append(m.text) if m.type=="error" else None)
        await pg.goto(URL)
        # 체험 모드
        await pg.click("#demo"); await pg.wait_for_selector("#plot", timeout=30000)
        await pg.screenshot(path="/tmp/s5.png")
        print("findings:", await pg.locator("ul.find li").all_inner_texts())
        await pg.click("label.choice:has(input[value=warm])"); await pg.click("button[data-view=R]")
        print("R warm:", await pg.locator("ul.find li").count())
        await pg.click("button[data-go='6']"); await pg.wait_for_selector("#apply", timeout=5000)
        await pg.click("#apply"); await pg.wait_for_selector(".note.good >> nth=1"); await pg.screenshot(path="/tmp/s6.png")
        print("applied:", open("/tmp/apo/bangeum_eq.txt").read().splitlines()[:3], "|", open("/tmp/apo/config.txt").read().strip().splitlines())
        await pg.click("#toggle"); await pg.wait_for_timeout(300); print("off:", open("/tmp/apo/bangeum_eq.txt").read().strip())
        # 영어 + 실제 측정 흐름 (가짜 마이크)
        await pg.click("button[data-lang=en]"); await pg.click("button[data-go='0']"); await pg.click("#start"); await pg.click("#allow")
        await pg.wait_for_selector("#inSel"); print("mics:", await pg.locator("#inSel option").count(), "| h1:", await pg.inner_text("h1"))
        await pg.screenshot(path="/tmp/s1.png")
        await pg.click("button[data-go='2']"); await pg.click("#test"); await pg.wait_for_timeout(1500); print("meter:", await pg.inner_text("#barLabel")); await pg.screenshot(path="/tmp/s2.png")
        await pg.click("button[data-go='3']"); await pg.click("button[data-go='4']"); await pg.click("#measure")
        await pg.wait_for_selector("#plot, .note.bad", timeout=40000)
        print("after real measure -> h1:", await pg.inner_text("h1"), "| notes:", await pg.locator(".note").all_inner_texts())
        print("errors:", errs); await b.close(); sys.exit(1 if errs else 0)
asyncio.run(main())
