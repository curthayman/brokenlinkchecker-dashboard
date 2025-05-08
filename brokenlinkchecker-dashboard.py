import streamlit as st
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from urllib.parse import urljoin, urlparse
from datetime import datetime
import warnings
import io

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

def is_internal(url, base_netloc):
    parsed = urlparse(url)
    return parsed.netloc == '' or parsed.netloc == base_netloc

def check_link(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code, response.status_code < 400
    except Exception:
        return None, False

def extract_links(soup, base_url):
    tags_attrs = [
        ('a', 'href'),
        ('img', 'src'),
        ('script', 'src'),
        ('link', 'href')
    ]
    links = set()
    for tag, attr in tags_attrs:
        for element in soup.find_all(tag):
            link = element.get(attr)
            if link:
                full_url = urljoin(base_url, link)
                links.add(full_url)
    return links

def crawl(url, base_netloc, visited, results, depth, max_depth, progress_bar=None, progress_state=None, live_log=None):
    if depth > max_depth or url in visited:
        return
    visited.add(url)
    try:
        page = requests.get(url, timeout=10)
        page.raise_for_status()
    except Exception as e:
        results.append((url, None, False, "PAGE ERROR"))
        if live_log is not None:
            live_log.markdown(f'<span style="color:red;">[BROKEN]</span> {url} (PAGE ERROR)', unsafe_allow_html=True)
        return

    soup = BeautifulSoup(page.text, "html.parser")
    links = extract_links(soup, url)
    for link in links:
        if link not in visited:
            status_code, ok = check_link(link)
            results.append((link, status_code, ok, ""))
            if live_log is not None:
                color = "green" if ok else "red"
                label = "OK" if ok else "BROKEN"
                status_str = f"{status_code}" if status_code else "ERR"
                live_log.markdown(
                    f'<span style="color:{color};">[{label}]</span> <a href="{link}">{link}</a> (Status: {status_str})',
                    unsafe_allow_html=True
                )
            if progress_bar is not None and progress_state is not None:
                progress_state[0] += 1
                progress_bar.progress(min(progress_state[0] / progress_state[1], 1.0))
            if is_internal(link, base_netloc):
                crawl(link, base_netloc, visited, results, depth + 1, max_depth, progress_bar, progress_state, live_log)

def generate_html_report(base_url, base_netloc, results):
    total = len(results)
    broken = sum(1 for _, _, ok, _ in results if not ok)
    working = total - broken
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = base_netloc.replace('.', '_')
    filename = f"broken_link_report_{domain}_{timestamp}.html"

    html_content = "<html><head><title>Broken Link Report</title></head><body>"
    html_content += f"<h2>Broken Link Report for {base_url}</h2>"
    html_content += f"<p><b>Total links checked:</b> {total}<br>"
    html_content += f"<b>Working links:</b> {working}<br>"
    html_content += f"<b>Broken links:</b> {broken}</p><ul>"
    for url, status_code, ok, note in results:
        color = "green" if ok else "red"
        label = "OK" if ok else "BROKEN"
        status_str = f"{status_code}" if status_code else "ERR"
        html_content += f'<li><span style="color:{color};font-weight:bold;">[{label}]</span> <a href="{url}">{url}</a> (Status: {status_str}) {note}</li>'
    html_content += "</ul></body></html>"
    return filename, html_content

st.set_page_config(page_title="Broken Link Checker Dashboard", layout="wide")
st.title("🔗 Broken Link Checker Dashboard")

with st.sidebar:
    st.header("Settings")
    base_url = st.text_input("Enter the URL to check", "https://example.com")
    depth = st.selectbox(
        "Crawl depth",
        options=[0, 1, 2, 3],
        format_func=lambda x: {
            0: "0 = Only the main page",
            1: "1 = Main page + links on main page",
            2: "2 = Main page + links on main page + links on those pages",
            3: "3 = ...and one level deeper"
        }[x],
        index=1
    )
    start = st.button("Start Checking")

if start:
    crawl_status = st.empty()
    crawl_status.info(f"Starting crawl for {base_url} (depth={depth})...")
    parsed_url = urlparse(base_url)
    base_netloc = parsed_url.netloc

    visited = set()
    results = []

    # Estimate total links for progress bar (rough, for UI feedback)
    progress_bar = st.progress(0)
    progress_state = [0, 100]  # [current, total] (will update total after first crawl)

    # First crawl to get initial links for progress estimate
    try:
        page = requests.get(base_url, timeout=10)
        page.raise_for_status()
        soup = BeautifulSoup(page.text, "html.parser")
        initial_links = extract_links(soup, base_url)
        progress_state[1] = max(len(initial_links), 1)
    except Exception:
        progress_state[1] = 1

    live_log = st.empty()
    crawl(base_url, base_netloc, visited, results, 0, depth, progress_bar, progress_state, live_log)

    # After crawl is done, show green success message
    crawl_status.success(f"Finished crawl for {base_url} (depth={depth})!")

    # Remove duplicates
    unique_results = {}
    for url, status_code, ok, note in results:
        unique_results[url] = (status_code, ok, note)
    results = [(url, *unique_results[url]) for url in unique_results]

    # Summary
    total = len(results)
    broken = sum(1 for _, _, ok, _ in results if not ok)
    working = total - broken

    st.subheader("Summary")
    st.write(f"**Total links checked:** {total}")
    st.write(f"**Working links:** {working}")
    st.write(f"**Broken links:** {broken}")

    st.subheader("Results")
    for url, status_code, ok, note in results:
        status_str = f"{status_code}" if status_code else "ERR"
        if ok:
            st.markdown(f'<span style="color:green;font-weight:bold;">[OK]</span> <a href="{url}">{url}</a> (Status: {status_str})', unsafe_allow_html=True)
        else:
            st.markdown(f'<span style="color:red;font-weight:bold;">[BROKEN]</span> <a href="{url}">{url}</a> (Status: {status_str}) {note}', unsafe_allow_html=True)

    # HTML report download
    filename, html_content = generate_html_report(base_url, base_netloc, results)
    st.subheader("Download Report")
    st.download_button(
        label="Download HTML Report",
        data=html_content,
        file_name=filename,
        mime="text/html"
    )