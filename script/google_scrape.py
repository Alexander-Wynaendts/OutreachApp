import urllib.parse
import asyncio
from pyppeteer import launch
from bs4 import BeautifulSoup

async def google_scrape(url):

    # Lancer le navigateur headless avec Pyppeteer
    browser = await launch(headless=False, args=['--no-sandbox'])
    page = await browser.newPage()

    # Simuler un vrai User-Agent pour éviter d'être détecté
    await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36")

    # Naviguer vers l'URL de Google Search
    await page.goto(url)

    await page.waitForSelector('input[aria-label="Tout accepter"]', timeout=10000)
    await page.click('input[aria-label="Tout accepter"]')

    await page.waitForSelector('div.BNeawe.s3v9rd.AP7Wnd', timeout=30000)

    # Récupérer le contenu HTML de la page
    response = await page.content()

    # Parse avec BeautifulSoup
    soup = BeautifulSoup(response, 'html.parser')

    # Fermer le navigateur
    await browser.close()

    return soup
