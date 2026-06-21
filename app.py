import streamlit as st
import json
import requests
from ddgs import DDGS
from bs4 import BeautifulSoup
from google import genai
def search_competitor(company_name):
    results = []
    with DDGS() as ddgs:
        queries = [
            f"{company_name} earnings revenue 2025",
            f"{company_name} strategy news 2025",
            f"{company_name} product launch 2025"
        ]
        for q in queries:
            for r in ddgs.text(q, max_results=3):
                results.append(r)
    return results
def fetch_page_content(url):
    try:
        response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)
        return text[:5000]
    except:
        return ""

def analyze_competitor(content, competitor, your_company):
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])
    prompt = f"""You are a competitive intelligence analyst. 
Analyze the following content about {competitor} and extract structured competitive signals.
CONTENT:
{content}
Return ONLY valid JSON in this exact format:
{{
    "company_analyzed": "{competitor}",
    "signals": [
        {{
            "category": "Product Launch | Pricing | Market Share | Strategy | Partnership",
            "signal": "what happened",
            "so_what": "specific implication for {your_company}"
        }}
    ],
    "overall_threat_level": "High | Medium | Low",
    "summary": "2-3 sentence executive summary"
}}"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text
st.set_page_config(page_title="CI Agent", layout="wide")
st.title("Competitive Intelligence Agent")

col1, col2 = st.columns(2)
with col1:
    competitor = st.text_input("Competitor to analyze", placeholder="e.g. Johnson & Johnson Vision")
with col2:
    your_company = st.text_input("So What for", placeholder="e.g. Alcon Vision Care")

run = st.button("Run Agent")
if run and competitor and your_company:
    with st.spinner("Searching for latest intel..."):
        search_results = search_competitor(competitor)

    with st.spinner("Reading sources..."):
        all_content = ""
        for r in search_results:
            all_content += f"\n\nSOURCE: {r['title']}\nURL: {r['href']}\n{r['body']}"

    st.caption(f"Fetched {len(search_results)} results, {len(all_content)} characters of content")
    if len(all_content) < 100:
        st.error("Not enough content fetched. Try a different competitor name.")
        st.stop()
    st.write(f"Found {len(search_results)} results")
    for r in search_results:
        st.caption(f"🔗 {r['title']}")
        st.caption(f"   {r.get('body', 'NO BODY')[:200]}")
    with st.spinner("Analyzing competitive signals..."):
        raw_response = analyze_competitor(all_content, competitor, your_company)
        try:
            clean = raw_response.strip().removeprefix("```json").removesuffix("```").strip()
            data = json.loads(clean)

            st.subheader(f"CI Brief: {data['company_analyzed']}")
            st.markdown(f"**Threat Level:** {data['overall_threat_level']}")
            st.markdown(f"**Summary:** {data['summary']}")

            st.subheader(f"So What for {your_company}")
            for s in data["signals"]:
                with st.expander(f"{s['category']}: {s['signal'][:80]}..."):
                    st.markdown(f"**Signal:** {s['signal']}")
                    st.markdown(f"**So What:** {s['so_what']}")
        except:
            st.error("Failed to parse response. Raw output below:")
            st.code(raw_response)