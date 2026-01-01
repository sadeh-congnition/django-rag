# Django RAG - Documentation Scraping and Processing

A Django application for scraping, processing, and analyzing Django documentation for RAG (Retrieval-Augmented Generation) applications.

## Django Management Commands

This project includes three custom Django management commands for scraping and processing documentation:

### 1. `scrape_django_docs`

Scrapes Django documentation from a specified base URL and stores the HTML content in the database.

**Usage:**
```bash
python manage.py scrape_django_docs [base_url] [--delete-existing]
```

**Arguments:**
- `base_url` (optional): The base URL to start scraping from. Defaults to `https://docs.djangoproject.com/en/6.0/`

**Options:**
- `--delete-existing`: Flag to delete all existing `NotFoundURL` and `URLToVisit` entries before starting the scrape.

**What it does:**
- Scrapes HTML content from Django documentation pages
- Stores each page's HTML content in the `Page` model
- Tracks URLs to visit and URLs that return 404 errors
- Follows links within the documentation to discover additional pages
- Uses caching to avoid re-scraping already processed URLs

**Models involved:**
- `Page`: Stores scraped HTML content with URL, content, and metadata
- `URLToVisit`: Tracks URLs that need to be processed
- `NotFoundURL`: Records URLs that returned 404 errors
- `HREFScraped`: Tracks scraped href URLs

### 2. `extract_text`

Extracts clean text content from scraped HTML pages and converts it to markdown format.

**Usage:**
```bash
python manage.py extract_text
```

**What it does:**
- Processes all `Page` objects in the database
- Converts HTML content to clean markdown text using the `text_extraction.to_markdown` module
- Stores the extracted text in the `cleaned_text` field of each `Page`
- Logs progress for each processed page

**Models involved:**
- `Page`: Updates the `cleaned_text` field with extracted markdown content

### 3. `count_tokens`

Counts the total tokens in all extracted text content using tiktoken encoding.

**Usage:**
```bash
python manage.py count_tokens
```

**What it does:**
- Retrieves all `Page` objects with extracted text
- Combines all cleaned text content
- Uses tiktoken's `cl100k_base` encoding (compatible with OpenAI models)
- Logs total token count and character count
- Useful for understanding the size of your knowledge base

**Models involved:**
- `Page`: Reads from the `cleaned_text` field

## Typical Workflow

1. **Scrape the documentation:**
   ```bash
   python manage.py scrape_django_docs --delete-existing
   ```

2. **Extract clean text:**
   ```bash
   python manage.py extract_text
   ```

3. **Count tokens (optional):**
   ```bash
   python manage.py count_tokens
   ```

## Project Structure

- `html_download/`: Main app for scraping and storing HTML content
  - `management/commands/`: Django management commands
  - `models.py`: Database models for pages, URLs, and scraping state
  - `html_scraper.py`: Core scraping logic
- `text_extraction/`: Text processing and markdown conversion
- `tokenization/`: Token counting utilities

## Dependencies

- Django
- djclick (for enhanced command-line interface)
- BeautifulSoup4 (HTML parsing)
- requests (HTTP client)
- tiktoken (token counting)
- loguru (logging)
- rich (formatted output)

## Database Models

The application uses the following main models:

- **Page**: Stores scraped HTML content and extracted text
- **URLToVisit**: Queue of URLs to be processed
- **NotFoundURL**: URLs that returned 404 errors
- **HREFScraped**: History of scraped href URLs

Each page includes metadata like creation/update timestamps and content hashes for change detection.

# Experiment Tracking
uv run manage.py load_project ..
uv run manage.py chunk_code
uv run manage.py describe_chunk