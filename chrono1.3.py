import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import StringIO
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# ---- App Config ----
st.set_page_config(page_title="ChronoLense – Wikipedia Events by Year", layout="centered")

# ---- Title ----
st.title("🕰️ ChronoLense: Wikipedia Events by Year")
st.write("Explore major historical events from Wikipedia for any selected year. Filter by language, search keywords, and more.")

# ---- Sidebar Filters ----
with st.sidebar:
    st.header("📋 Filters")
    language = st.selectbox("🌍 Wikipedia Language", ["en", "fr", "es", "de", "hi"])
    year = st.selectbox("📅 Select Year", list(reversed(range(1900, 2025))))
    search_term = st.text_input("🔍 Search in events", "")
    categories = st.multiselect("🏷️ Filter by Category", ["Politics", "Science", "Sports", "Disaster", "Culture"])

# ---- Manual Category Matcher ----
def match_category(event):
    categories_map = {
        "Politics": ["election", "government", "president", "minister", "parliament"],
        "Science": ["scientist", "research", "discovered", "space", "nobel"],
        "Sports": ["tournament", "match", "cup", "olympics", "world championship"],
        "Disaster": ["earthquake", "flood", "storm", "crash", "explosion"],
        "Culture": ["movie", "film", "music", "festival", "released"]
    }
    matched = []
    for cat, keywords in categories_map.items():
        if any(kw.lower() in event.lower() for kw in keywords):
            matched.append(cat)
    return matched

# ---- Fetch Wikipedia Events ----
def get_wikipedia_events(year, lang="en"):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "page": str(year),
        "format": "json",
        "prop": "text",
        "redirects": True
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None

    data = response.json()
    if "parse" not in data:
        return None

    soup = BeautifulSoup(data["parse"]["text"]["*"], 'html.parser')
    events_header = soup.find(id="Events")
    if not events_header:
        return None

    events_list = []
    for tag in events_header.parent.find_next_siblings():
        if tag.name == "h2":
            break
        if tag.name == "ul":
            for li in tag.find_all("li"):
                text = li.get_text().strip()
                if text:
                    events_list.append(text)
        if len(events_list) >= 50:
            break
    return events_list[:50]

# ---- Today in History ----
today = pd.Timestamp.today()
today_url = f"https://en.wikipedia.org/wiki/{today.strftime('%B')}_{today.day}"
st.sidebar.markdown(f"📆 [Today in History: {today.strftime('%B %d')}]({today_url})")

# ---- Main Display ----
if year:
    st.info(f"Fetching top 50 events from Wikipedia for {year} ({language})...")
    with st.spinner("Loading events..."):
        events = get_wikipedia_events(year, language)

    if events:
        # ---- Category Tagging ----
        tagged_events = [(e, match_category(e)) for e in events]

        # ---- Apply Search & Category Filters ----
        filtered_events = []
        for e, tags in tagged_events:
            if search_term.lower() in e.lower():
                if not categories or any(cat in tags for cat in categories):
                    filtered_events.append((e, tags))

        st.success(f"Showing {len(filtered_events)} filtered events for {year}")

        if filtered_events:
            # ---- Two-column display ----
            col1, col2 = st.columns(2)
            for i, (event, tags) in enumerate(filtered_events):
                tag_str = f"`{'`, `'.join(tags)}`" if tags else ""
                if i % 2 == 0:
                    col1.markdown(f"**{i+1}.** {event} {tag_str}")
                else:
                    col2.markdown(f"**{i+1}.** {event} {tag_str}")

            # ---- Word Cloud ----
            st.markdown("---")
            st.subheader("☁️ Word Cloud of Events")
            text_blob = " ".join([e for e, _ in filtered_events])
            wc = WordCloud(width=800, height=300, background_color="white").generate(text_blob)
            fig, ax = plt.subplots()
            ax.imshow(wc, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

            # ---- Download Buttons ----
            df = pd.DataFrame(filtered_events, columns=["Event", "Tags"])
            csv = df.to_csv(index=False).encode('utf-8')
            txt = StringIO("\n".join([e for e, _ in filtered_events])).getvalue().encode('utf-8')

            st.download_button("⬇️ Download CSV", csv, file_name=f"chronolense_events_{year}.csv", mime="text/csv")
            st.download_button("⬇️ Download TXT", txt, file_name=f"chronolense_events_{year}.txt", mime="text/plain")
        else:
            st.warning("No events match your filters. Please try a different year, language, or category.")

        # ---- Wikipedia Link ----
        wiki_url = f"https://{language}.wikipedia.org/wiki/{year}"
        st.markdown(f"🔗 [More on Wikipedia →]({wiki_url})")

        # ---- Feedback Form ----
        st.markdown("---")
        st.subheader("💬 Share Feedback")
        with st.form("feedback_form"):
            name = st.text_input("Your Name")
            rating = st.slider("Rate ChronoLense", 1, 5, 3)
            comments = st.text_area("Comments or Suggestions")
            submitted = st.form_submit_button("Submit")
            if submitted:
                st.success("Thanks for your feedback!")
    else:
        st.warning("No events found or Wikipedia format may have changed.")
