#!/usr/bin/env python3
"""Diagnóstico rápido de Bumeran (URLs + API)."""

from __future__ import annotations

import asyncio
import json

from playwright.async_api import async_playwright

TESTS = [
    "https://www.bumeran.com.ar/empleos-area-tecnologia-sistemas-y-telecomunicaciones.html",
    "https://www.bumeran.com.ar/en-buenos-aires/empleos.html",
    "https://www.bumeran.com.ar/empleos-busqueda-desarrollador.html",
]

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


async def probe(url: str) -> None:
    apis: list[dict] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(user_agent=UA, locale="es-AR")
        await ctx.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        page = await ctx.new_page()

        async def on_req(request) -> None:
            if "searchV2" in request.url:
                print("REQ", request.method, request.url)
                print("BODY", request.post_data)

        async def on_resp(response) -> None:
            u = response.url
            if "/api/" not in u:
                return
            entry: dict = {"method": response.request.method, "url": u}
            try:
                body = await response.json()
                if isinstance(body, dict):
                    entry["keys"] = list(body.keys())
                    for key in ("content", "avisos", "results", "data"):
                        if key in body and isinstance(body[key], list):
                            entry["list_key"] = key
                            entry["count"] = len(body[key])
                            if body[key]:
                                entry["sample"] = body[key][0]
                            break
                else:
                    entry["type"] = type(body).__name__
            except Exception as exc:
                entry["error"] = str(exc)
            apis.append(entry)

        page.on("request", on_req)
        page.on("response", on_resp)
        if "tecnologia" not in url and "busqueda-desarrollador" not in url:
            return
        await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        await page.wait_for_timeout(12_000)

        info = await page.evaluate(
            """() => {
              const all = Array.from(document.querySelectorAll('a'))
                .map(a => a.getAttribute('href') || '')
                .filter(h => h.includes('/empleos/'));
              const html = all.filter(h => h.endsWith('.html'));
              return {
                title: document.title,
                h1: document.querySelector('h1')?.innerText || null,
                bodyLen: (document.body?.innerText || '').length,
                empleoLinks: all.length,
                htmlLinks: html.length,
                samples: all.slice(0, 8),
              };
            }"""
        )
        print("URL", url)
        print(json.dumps(info, ensure_ascii=False, indent=2))
        for entry in apis:
            print("API", json.dumps(entry, ensure_ascii=False, default=str)[:3000])
        await browser.close()


async def main() -> None:
    for url in TESTS:
        await probe(url)
        print("---")


if __name__ == "__main__":
    asyncio.run(main())