const fs = require('fs');
const path = require('path');

// Simple ETL for MVP: deduplication, basic keyword extraction
class ETLProcessor {
  constructor() {
    this.processedData = [];
    this.seenTitles = new Set();
  }

  // Extract and transform RSS data
  processRSSData(rssData) {
    const processed = [];

    rssData.forEach(item => {
      // Deduplication
      if (this.seenTitles.has(item.title)) {
        return; // Skip duplicate
      }
      this.seenTitles.add(item.title);

      // Basic transformation
      const processedItem = {
        id: this.generateId(item),
        title: item.title,
        link: item.link,
        pubDate: new Date(item.pubDate),
        contentSnippet: item.contentSnippet,
        source: item.source,
        keywords: this.extractKeywords(item.title + ' ' + item.contentSnippet),
        severity: this.assessSeverity(item.title + ' ' + item.contentSnippet), // Simple for MVP
        processedAt: new Date()
      };

      processed.push(processedItem);
    });

    this.processedData = [...this.processedData, ...processed];
    return processed;
  }

  // Simple ID generation
  generateId(item) {
    return `${item.source}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  // Basic keyword extraction (simple word frequency for MVP)
  extractKeywords(text) {
    const words = text.toLowerCase().match(/\b\w{4,}\b/g) || [];
    const wordCount = {};

    words.forEach(word => {
      wordCount[word] = (wordCount[word] || 0) + 1;
    });

    return Object.entries(wordCount)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5)
      .map(([word]) => word);
  }

  // Simple severity assessment (MVP: based on keywords)
  assessSeverity(text) {
    const threatWords = ['crisis', 'attack', 'violence', 'emergency', 'threat', 'danger'];
    const lowerText = text.toLowerCase();
    const matches = threatWords.filter(word => lowerText.includes(word));
    return matches.length > 0 ? 'high' : 'low';
  }

  // Save to file (for persistence in MVP)
  saveToFile(filename = 'processed_data.json') {
    const filepath = path.join(__dirname, filename);
    fs.writeFileSync(filepath, JSON.stringify(this.processedData, null, 2));
    console.log(`Saved ${this.processedData.length} items to ${filepath}`);
  }

  // Load from file
  loadFromFile(filename = 'processed_data.json') {
    const filepath = path.join(__dirname, filename);
    if (fs.existsSync(filepath)) {
      this.processedData = JSON.parse(fs.readFileSync(filepath));
      console.log(`Loaded ${this.processedData.length} items from ${filepath}`);
    }
  }

  // Get alerts for missionary UI (high severity)
  getMissionaryAlerts() {
    return this.processedData.filter(item => item.severity === 'high').slice(-10); // Last 10
  }
}

// Export for use in other modules
module.exports = ETLProcessor;

// For testing standalone
if (require.main === module) {
  const processor = new ETLProcessor();

  // Sample data
  const sampleData = [
    {
      title: 'Breaking: Major Crisis in Eastern Europe',
      link: 'https://example.com/1',
      pubDate: new Date().toISOString(),
      contentSnippet: 'A major crisis has erupted...',
      source: 'Sample News'
    },
    {
      title: 'Weather Update: No Issues',
      link: 'https://example.com/2',
      pubDate: new Date().toISOString(),
      contentSnippet: 'Normal weather conditions...',
      source: 'Sample News'
    }
  ];

  const processed = processor.processRSSData(sampleData);
  console.log('Processed items:', processed);
  processor.saveToFile();
}
