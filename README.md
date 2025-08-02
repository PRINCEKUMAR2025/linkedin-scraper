# LinkedIn Profile Analyzer

A beginner-friendly Python web app that **scrapes LinkedIn profiles** using **Playwright** and generates professional AI-powered summaries and analysis with **Google Gemini**.

---

## ✨ Features

- **LinkedIn Profile Scraping** — Extracts name, headline, about, experience, skills, and education.
- **AI Summaries** — Uses the Google Gemini API to generate clear, professional summaries.
- **Modern Web Interface** — Simple, responsive web UI.
- **Copy & Download** — Easily copy or download the generated summary.
- **Persistent Login** — Log in once; your session is saved.
- **Batch Processing** — Upload CSV files with multiple LinkedIn URLs for bulk analysis.
- **Beginner-Friendly** — No advanced setup or coding skills required.

---

## 📝 Requirements

- **Python 3.8 or higher**
- **Google Gemini API key** ([Get it free](https://aistudio.google.com/app/apikey))
- **Google Chrome or Chromium** (required by Playwright)
- **LinkedIn account** (manual login required on first run)

---

## 🚀 Setup Instructions

1. **Clone this repository**
   ```bash
   git clone <your-repository-url>
   cd linkedin-analyzer
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install
   ```

4. **Set up your Gemini API key**

   - Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
   - Create a `.env` file in the project folder:
     ```env
     GEMINI_API_KEY=your_gemini_api_key_here
     ```

---

## ▶️ How to Run the App

**Run in web mode (recommended):**
```bash
python main.py
```
- The app will show a local address (usually `http://127.0.0.1:5000`).
- Open this address in your browser.

**Run in console mode (optional):**
```bash
python main.py --mode console
```
> In console mode, the scraping runs directly in the terminal instead of the web UI.

---

## 📊 Batch Processing with CSV

The app now supports **batch processing** of multiple LinkedIn profiles using CSV files:

### CSV File Format
Create a CSV file with LinkedIn profile URLs. The file should have a column containing the URLs:

```csv
profile_url,name,notes
https://www.linkedin.com/in/satyanadella/,Satya Nadella,Microsoft CEO
https://www.linkedin.com/in/jeffweiner08/,Jeff Weiner,LinkedIn CEO
https://www.linkedin.com/in/reidhoffman/,Reid Hoffman,LinkedIn Co-founder
```

### How to Use Batch Processing
1. **Select "Batch Processing" mode** in the web interface
2. **Upload your CSV file** with LinkedIn URLs
3. **Specify the column name** containing the URLs (default: `profile_url`)
4. **Choose analysis type** (Bio, Summary, or Analysis)
5. **Start processing** - the app will process each profile sequentially
6. **Download results** - a CSV file with all scraped data and analysis results

### Batch Processing Features
- **Progress tracking** - See which profiles are being processed
- **Error handling** - Failed profiles are logged separately
- **CSV output** - Results saved in structured CSV format
- **Multiple analysis types** - Choose bio, summary, or full analysis for all profiles

### Sample CSV Template
A sample CSV file (`sample_profiles.csv`) is included in the project for reference.

---

## ⚙️ Headless Mode

By default, the scraper runs **with a visible browser window** so you can log in manually.

- To enable headless mode (no visible browser window), update `main.py`:
  ```python
  profile_data = scrape_linkedin_profile(profile_url, headless=True)
  ```
  in both `analyze()` and `api_analyze()` functions.

**Important:**  
You **must log in once** with `headless=False` so your session is saved. After that, you can run headless.

---

## 🖥️ How It Works

### Single Profile Mode
1. Open the web page shown in your terminal.
2. Enter a LinkedIn profile URL (e.g., `https://www.linkedin.com/in/example`).
3. The app opens a **Chromium browser** — log in to LinkedIn if asked.
4. Once logged in, your session is saved in `playwright_user_data`.
5. The scraper fetches data, sends it to Gemini, and shows the AI summary.
6. Copy or download your result.

### Batch Processing Mode
1. Select "Batch Processing" mode in the web interface.
2. Upload a CSV file containing LinkedIn profile URLs.
3. The app processes each URL sequentially, scraping and analyzing each profile.
4. Results are compiled into a downloadable CSV file with all data and analysis.
5. Any errors are logged in a separate error file.

---

