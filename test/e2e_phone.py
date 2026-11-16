import asyncio, sys
from playwright.async_api import async_playwright
URL = "http://127.0.0.1:8765/?peer=127.0.0.1:9000"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox","--use-fake-device-for-media-stream","--use-fake-ui-for-media-stream","--use-file-for-fake-audio-capture=/tmp/tone.wav","--autoplay-policy=no-user-gesture-required"])
        errs=[]
        def watch(pg, tag):
            pg.on("pageerror", lambda e: errs.append(tag+": "+str(e))); pg.on("console", lambda m: errs.append(tag+": "+m.text) if m.type=="error" else None)
        pc = await (await b.new_context(locale="ko-KR", viewport={"width":900,"height":1000})).new_page(); watch(pc,"pc")
        await pc.goto(URL); await pc.click("#start"); await pc.click("label.choice:has(input[value=phone])")
        await pc.wait_for_selector("#phoneLink", timeout=10000); link = await pc.get_attribute("#phoneLink","href"); print("link:", link)
        print("qr svg:", await pc.locator(".qr svg").count()); await pc.screenshot(path="/tmp/p1.png")
        ph = await (await b.new_context(locale="ko-KR", viewport={"width":390,"height":760})).new_page(); watch(ph,"phone")
        await ph.goto(link); await ph.screenshot(path="/tmp/ph0.png"); await ph.click("#go")
        await pc.wait_for_selector(".note.good", timeout=15000); print("pc:", await pc.inner_text(".note.good"), "| phone:", await ph.inner_text("h1"))
        await pc.click("button[data-go='2']"); await pc.click("#test"); await pc.wait_for_timeout(1500); print("meter:", await pc.inner_text("#barLabel")); await pc.click("#test")
        await pc.click("button[data-go='3']"); print("pos:", (await pc.inner_text("#view p >> nth=1"))[:30])
        await pc.click("button[data-go='4']"); await pc.click("#measure"); await ph.wait_for_timeout(1500); print("phone during:", await ph.inner_text("h1"))
        await pc.wait_for_selector("#plot, .note.bad", timeout=60000)
        print("pc after:", await pc.inner_text("h1"), "| rec:", await pc.evaluate("window.__lastRec"), "| notes:", await pc.locator(".note").all_inner_texts())
        print("fHi limited filters max fc:", await pc.evaluate("S.result ? Math.max(0,...S.result.L.filters.map(f=>f.fc),...S.result.R.filters.map(f=>f.fc)) : null"))
        print("phone end:", await ph.inner_text("h1")); print("errors:", errs); await b.close(); sys.exit(1 if errs else 0)
asyncio.run(main())
