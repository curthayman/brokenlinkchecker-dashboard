# Broken Link Checker Dashboard

A simple Streamlit dashboard to recursively check for broken links (including images, scripts, and CSS) on a website.  
Generates a summary and downloadable HTML report.

## Features

- Checks all links, images, scripts, and CSS files for HTTP status
- Recursive crawling up to a user-selected depth
- Live progress and log display
- Summary of working and broken links
- Downloadable HTML report

## Requirements

- Python 3.7+
- [Streamlit](https://streamlit.io/)
- requests
- beautifulsoup4

## Installation

1. Clone this repository:
    
    - git clone https://github.com/yourusername/brokenlinkchecker-dashboard.git
    - cd brokenlinkchecker-dashboard
    

2. Install dependencies:
    
    - pip install -r requirements.txt
    
    - Or, install individually:
    
    - pip install streamlit requests beautifulsoup4
    

## Usage

**Run the Streamlit app:**

- streamlit run brokenlinkchecker-dashboard.py
