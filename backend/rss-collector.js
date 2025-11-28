const Parser = require('rss-parser');
const express = require('express');
const puppeteer = require('puppeteer');
const app = express();
const port = 3001;

const parser = new Parser();

// Sample RSS feeds for threat intelligence and news, including global sources
const rssFeeds = [
  'https://feeds.bbci.co.uk/news/world/rss.xml', // BBC World News
  'https://www.aljazeera.com/xml/rss/all.xml', // Al Jazeera
  'https://rss.dw.com/xml/rss-en-all', // Deutsche Welle (European focus)
  'https://www.euronews.com/rss', // Euronews
  'https://www.reuters.com/world/europe/rss/', // Reuters Europe
  'https://www.reuters.com/world/asia/rss/', // Reuters Asia
  'https://www.reuters.com/world/africa/rss/', // Reuters Africa
  'https://www.reuters.com/world/americas/rss/', // Reuters Americas
  'https://www.reuters.com/world/middle-east/rss/', // Reuters Middle East
  'https://www.nhk.or.jp/rss/news/english.xml', // NHK Japan
  'https://www.aljazeera.com/xml/rss/africa.xml', // Al Jazeera Africa
  'https://www.aljazeera.com/xml/rss/asia-pacific.xml', // Al Jazeera Asia-Pacific
  // Add more as needed
];

// Web scraping functions for OSINT
async function scrapeCNN() {
  let browser;
  try {
    const proxyUrl = process.env.BRIGHT_DATA_PROXY || 'http://brd-customer-hl_XXXXXX-zone-residential:password@brd.superproxy.io:22225';
    browser = await puppeteer.launch({
      headless: true,
      args: [
        `--proxy-server=${proxyUrl}`,
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage'
      ]
    });
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
    await page.goto('https://www.cnn.com/world', { waitUntil: 'networkidle2', timeout: 30000 });
    await page.waitForSelector('.headline__text, .cd__headline-text', { timeout: 10000 });
    const headlines = await page.$$eval('.headline__text, .cd__headline-text', elements =>
      elements.slice(0, 5).map(el => ({
        title: el.textContent.trim(),
        link: el.closest('a') ? el.closest('a').href : 'https://www.cnn.com/world'
      }))
    );
    return headlines.map(item => ({
      title: item.title,
      link: item.link,
      pubDate: new Date().toISOString(),
      contentSnippet: item.title,
      source: 'CNN Scraped'
    }));
  } catch (error) {
    console.error('Error scraping CNN:', error);
    return [];
  } finally {
    if (browser) await browser.close();
  }
}

async function scrapeReuters() {
  let browser;
  try {
    const proxyUrl = process.env.BRIGHT_DATA_PROXY || 'http://brd-customer-hl_XXXXXX-zone-residential:password@brd.superproxy.io:22225';
    browser = await puppeteer.launch({
      headless: true,
      args: [`--proxy-server=${proxyUrl}`, '--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
    await page.goto('https://www.reuters.com/world/', { waitUntil: 'networkidle2', timeout: 30000 });
    await page.waitForSelector('[data-testid="Heading"], .story-title', { timeout: 10000 });
    const headlines = await page.$$eval('[data-testid="Heading"], .story-title', elements =>
      elements.slice(0, 5).map(el => ({
        title: el.textContent.trim(),
        link: el.closest('a') ? el.closest('a').href : 'https://www.reuters.com/world/'
      }))
    );
    return headlines.map(item => ({
      title: item.title,
      link: item.link,
      pubDate: new Date().toISOString(),
      contentSnippet: item.title,
      source: 'Reuters Scraped'
    }));
  } catch (error) {
    console.error('Error scraping Reuters:', error);
    return [];
  } finally {
    if (browser) await browser.close();
  }
}

async function scrapeNHK() {
  let browser;
  try {
    const proxyUrl = process.env.BRIGHT_DATA_PROXY || 'http://brd-customer-hl_XXXXXX-zone-residential:password@brd.superproxy.io:22225';
    browser = await puppeteer.launch({
      headless: true,
      args: [`--proxy-server=${proxyUrl}`, '--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
    await page.goto('https://www3.nhk.or.jp/nhkworld/en/news/', { waitUntil: 'networkidle2', timeout: 30000 });
    await page.waitForSelector('.content--card__headline', { timeout: 10000 });
    const headlines = await page.$$eval('.content--card__headline', elements =>
      elements.slice(0, 5).map(el => ({
        title: el.textContent.trim(),
        link: el.closest('a') ? 'https://www3.nhk.or.jp' + el.closest('a').href : 'https://www3.nhk.or.jp/nhkworld/en/news/'
      }))
    );
    return headlines.map(item => ({
      title: item.title,
      link: item.link,
      pubDate: new Date().toISOString(),
      contentSnippet: item.title,
      source: 'NHK Scraped'
    }));
  } catch (error) {
    console.error('Error scraping NHK:', error);
    return [];
  } finally {
    if (browser) await browser.close();
  }
}

// Function to assess threat using AI service
const assessWithAI = async (text) => {
  try {
    const response = await fetch('http://localhost:5000/detect_threat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });
    if (!response.ok) {
      throw new Error('AI service error');
    }
    return await response.json();
  } catch (error) {
    console.error('Error calling AI service:', error);
    return { threat_level: 'unknown', confidence: 0 };
  }
};

app.get('/api/rss', async (req, res) => {
  try {
    const allItems = [];

    // Scrape additional sources (CNN, Reuters, NHK are defined; others are placeholders)
    const scrapedData = await Promise.allSettled([
      scrapeCNN(),
      scrapeReuters(),
      scrapeNHK()
    ]);

    scrapedData.forEach(result => {
      if (result.status === 'fulfilled') {
        allItems.push(...result.value);
      }
    });

    // Add RSS feeds
    for (const feedUrl of rssFeeds) {
      const feed = await parser.parseURL(feedUrl);
      console.log(`Fetched ${feed.items.length} items from ${feed.title}`);

      // Process items with AI (limit to 5 per feed for MVP performance)
      const processedItems = await Promise.all(
        feed.items.slice(0, 5).map(async (item) => {
          const text = item.title + ' ' + item.contentSnippet;
          const aiResult = await assessWithAI(text);
          return {
            title: item.title,
            link: item.link,
            pubDate: item.pubDate,
            contentSnippet: item.contentSnippet,
            source: feed.title,
            ai_threat_level: aiResult.threat_level,
            ai_confidence: aiResult.confidence
          };
        })
      );

      allItems.push(...processedItems);
    }

    res.json({ success: true, data: allItems });
  } catch (error) {
    console.error('Error fetching data:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.listen(port, () => {
  console.log(`RSS Collector API running on http://localhost:${port}`);
});

// For testing, fetch once on startup
(async () => {
  try {
    for (const feedUrl of rssFeeds) {
      const feed = await parser.parseURL(feedUrl);
      console.log(`Startup fetch: ${feed.title} - ${feed.items.length} items`);
    }
  } catch (error) {
    console.error('Startup fetch error:', error);
  }
})();
