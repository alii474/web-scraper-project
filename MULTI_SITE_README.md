# 🌐 Multi-Site Web Scraper - Complete Upgrade

**एक powerful, production-ready multi-site web scraper जो automatically detect करता है कि किस website को scrape करना है और सभी data को common format में normalize करता है।**

---

## 🚀 **Key Features**

### **✅ Multi-Site Support**
- **4 Websites Pre-Configured**:
  - 📚 [Books to Scrape](http://books.toscrape.com/) - Book data with prices
  - 💬 [Quotes to Scrape](http://quotes.toscrape.com/) - Quotes and authors
  - 📰 [Hacker News](https://news.ycombinator.com/) - News articles and scores
  - 💻 [GitHub](https://github.com/) - Repository information

### **🎯 Automatic Detection**
- **Smart URL Detection**: Automatically identifies website from URL
- **Dynamic Configuration**: Uses appropriate scraper based on URL
- **Flexible Field Mapping**: Maps different HTML structures to common fields

### **📊 Data Normalization**
- **Common Format**: All data normalized to standard schema
- **Field Mapping**: price, rating, author, title, URL, etc.
- **Tagging**: Automatic source and category tagging
- **Combined Dataset**: Merge data from multiple sites

### **⚙️ Configuration-Driven**
- **JSON Configuration**: Easy to add new websites
- **Flexible Selectors**: CSS selectors for each field
- **Field Transformations**: Data cleaning and formatting
- **Pagination Support**: Automatic multi-page scraping

---

## 📁 **Project Structure**

```
multi-site-scraper/
├── config.json                 # Website configurations
├── multi_site_scraper.py       # Main entry point
├── sample_urls.txt            # Sample URLs for testing
├── src/
│   ├── core/
│   │   └── multi_site_scraper.py    # Core scraping engine
│   ├── cli/
│   │   └── multi_site_cli.py        # Command-line interface
│   └── utils/                   # Utilities
├── output/                    # Generated files
└── templates/                 # Web templates
```

---

## 🛠️ **Installation & Setup**

### **Prerequisites**
- Python 3.8+
- Required packages (see requirements.txt)

### **Installation**
```bash
# Clone or download the project
cd multi-site-scraper

# Install dependencies
pip install -r requirements.txt

# Verify installation
python multi_site_scraper.py --list-sites
```

---

## 🎮 **Usage Examples**

### **1. List Configured Websites**
```bash
python multi_site_scraper.py --list-sites
```

**Output:**
```
🌐 CONFIGURED WEBSITES:
  books.toscrape.com:
    Name: Books to Scrape
    Category: books
    Max Pages: 50
  quotes.toscrape.com:
    Name: Quotes to Scrape
    Category: quotes
    Max Pages: 10
```

### **2. Scrape Specific Websites**
```bash
# Scrape multiple websites
python multi_site_scraper.py --sites books.toscrape.com,quotes.toscrape.com --max-pages 2

# With normalization and combination
python multi_site_scraper.py --sites books.toscrape.com,news.ycombinator.com --normalize --combine
```

### **3. Scrape from URL File**
```bash
# Create sample_urls.txt with URLs
python multi_site_scraper.py --file sample_urls.txt --max-pages 1 --normalize --output combined_data
```

### **4. Advanced Options**
```bash
# Full featured scraping
python multi_site_scraper.py --file sample_urls.txt \
    --max-pages 3 \
    --normalize \
    --combine \
    --formats csv excel json sqlite \
    --visualize \
    --output multi_site_results
```

---

## 📊 **Configuration System**

### **config.json Structure**
```json
{
  "websites": {
    "books.toscrape.com": {
      "name": "Books to Scrape",
      "category": "books",
      "item_selector": "article.product_pod",
      "fields": {
        "title": {
          "selector": "h3 a",
          "attribute": "title",
          "required": true
        },
        "price": {
          "selector": "p.price_color",
          "attribute": "text",
          "type": "price"
        }
      }
    }
  }
}
```

### **Adding New Websites**
```json
{
  "newsite.com": {
    "name": "New Site",
    "category": "category",
    "base_url": "https://newsite.com/",
    "item_selector": "div.item",
    "fields": {
      "title": {"selector": "h2", "attribute": "text"},
      "price": {"selector": ".price", "attribute": "text"}
    }
  }
}
```

---

## 📈 **Data Normalization**

### **Common Schema**
All scraped data is normalized to include:
- `title` - Item title/name
- `url` - Item URL
- `price` - Price (if available)
- `rating` - Rating/score (if available)
- `author` - Author/creator (if available)
- `source` - Source website name
- `category` - Content category
- `scraped_at` - Timestamp

### **Field Mapping**
- **Price Fields**: `price`, `cost`, `amount`, `value`
- **Rating Fields**: `rating`, `score`, `stars`, `points`
- **Author Fields**: `author`, `author_name`, `posted_by`
- **Description Fields**: `description`, `summary`, `content`

---

## 🎯 **Working Examples**

### **✅ Successfully Scraped**
```
📊 MULTI-SITE SCRAPER STATISTICS:
  Total Items Scraped: 40
  Sites Scraped: 4
  Errors: 0
  Runtime: 46.4 seconds
  Success Rate: 100.0%

📈 BY WEBSITE:
  books.toscrape.com: 20 items
  quotes.toscrape.com: 10 items
  news.ycombinator.com: 5 items
  github.com: 5 items
```

### **📁 Generated Files**
- `multi_site_demo.csv` - Combined normalized data
- `multi_site_demo.xlsx` - Excel format with analysis
- `multi_site_demo_visualization_analysis_20260319_171921.png` - Data visualization

---

## 🔧 **Advanced Features**

### **1. Smart Field Extraction**
```python
# Price extraction with currency handling
price_match = re.search(r'[\d,]+\.?\d*', value.replace('£', '').replace('$', ''))

# Rating extraction from different formats
rating_map = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}
```

### **2. Data Cleaning**
- Quote removal: `"Hello"` → `Hello`
- Whitespace normalization
- URL absolute path conversion
- Number extraction from text

### **3. Error Handling**
- Graceful degradation on missing fields
- Retry logic for failed requests
- Comprehensive logging

---

## 💼 **Real-World Applications**

### **🎯 Use Cases**
1. **E-commerce Price Comparison**
   - Scrape product prices from multiple sites
   - Normalize to common format for comparison
   - Generate price alerts

2. **Content Aggregation**
   - News from multiple sources
   - Social media content
   - Blog posts and articles

3. **Market Research**
   - Competitor monitoring
   - Trend analysis
   - Price tracking

4. **Data Collection**
   - Academic research
   - Business intelligence
   - Content curation

### **💰 Business Value**
- **Time Savings**: Automated data collection
- **Data Quality**: Normalized, clean data
- **Scalability**: Multiple sites simultaneously
- **Flexibility**: Easy to add new sources

---

## 🌐 **Web Interface Integration**

### **Simple Web App**
```bash
# Run the web interface
python simple_web_app.py

# Access at: http://localhost:5000
```

### **Features**
- 📱 Modern, responsive interface
- 🔄 Real-time scraping progress
- 📊 Live statistics
- 💾 Download results
- 🎨 Data visualization

---

## 📊 **Sample Output**

### **Normalized CSV Data**
```csv
scraped_at,source,category,title,url,price,availability,source_site
2026-03-19T17:19:19,Books to Scrape,books,A Light in the Attic,http://...,51.77,In stock,books.toscrape.com
2026-03-19T17:19:19,Quotes to Scrape,quotes,"The world as we have created it...",http://...,NA,NA,quotes.toscrape.com
2026-03-19T17:19:19,Hacker News,news,New Python Release,https://...,NA,NA,news.ycombinator.com
```

### **Combined Analysis**
- **Total Items**: 40 from 4 websites
- **Categories**: books, quotes, news, code
- **Data Fields**: title, price, rating, author, URL
- **Visualization**: Price distribution, category breakdown

---

## 🔍 **Technical Details**

### **Architecture**
- **Multi-Site Engine**: Core scraping with detection
- **Configuration System**: JSON-driven website configs
- **Data Pipeline**: Extract → Clean → Normalize → Store
- **CLI Interface**: Comprehensive command-line tool

### **Performance**
- **Concurrent Scraping**: Multiple sites simultaneously
- **Rate Limiting**: Respectful scraping delays
- **Error Recovery**: Retry logic and fallbacks
- **Memory Efficient**: Streaming data processing

### **Extensibility**
- **Plugin Architecture**: Easy to add new websites
- **Field Mapping**: Flexible data transformation
- **Output Formats**: CSV, Excel, JSON, SQLite
- **Visualization**: Built-in chart generation

---

## 🚀 **Future Enhancements**

### **Planned Features**
1. **More Websites**: Amazon, eBay, Reddit, Twitter
2. **API Integration**: REST API for programmatic access
3. **Database Support**: PostgreSQL, MongoDB integration
4. **Machine Learning**: Content classification and analysis
5. **Scheduling**: Automated recurring scraping

### **Advanced Options**
- **Proxy Rotation**: IP rotation for large-scale scraping
- **JavaScript Rendering**: Puppeteer/Selenium integration
- **Distributed Scraping**: Multi-machine coordination
- **Real-time Updates**: WebSocket streaming

---

## 📞 **Support & Documentation**

### **Help Commands**
```bash
# Show all options
python multi_site_scraper.py --help

# List configured sites
python multi_site_scraper.py --list-sites

# Show statistics
python multi_site_scraper.py --stats
```

### **Troubleshooting**
- Check `config.json` for website configurations
- Verify URLs are accessible
- Monitor logs for error messages
- Adjust delay settings for rate limiting

---

## 🏆 **Why This is Better**

### **vs Single-Site Scrapers**
- ✅ **Multiple Sources**: One tool for many sites
- ✅ **Consistent Data**: Normalized format
- ✅ **Easy Extension**: Add sites without code changes
- ✅ **Better Value**: More data per effort

### **vs Manual Scraping**
- ✅ **Automated**: Set and forget
- ✅ **Reliable**: Error handling and retries
- ✅ **Scalable**: Handle large datasets
- ✅ **Professional**: Production-ready code

---

## 🎉 **Conclusion**

**यह Multi-Site Web Scraper एक complete solution है जो:**

✅ **Multiple Websites** को support करता है  
✅ **Automatic Detection** करता है  
✅ **Data Normalization** करता है  
✅ **Configuration-Driven** है  
✅ **Production Ready** है  
✅ **Easy to Extend** है  

**Perfect for:**
- 🎯 **Freelance Projects** - High-value data collection
- 📊 **Business Intelligence** - Market research and analysis
- 🔬 **Academic Research** - Data collection for studies
- 💼 **E-commerce** - Price comparison and monitoring

---

**🚀 Ready to use: Just run `python multi_site_scraper.py --list-sites` to get started!**
