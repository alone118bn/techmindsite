from flask import Flask, render_template
import os
import feedparser

app = Flask(__name__)

RSS_FEEDS = {
    "tech": [
        "https://news.google.com/rss/search?q=android+AI+technology&hl=ru&gl=RU&ceid=RU:ru",
        "https://habr.com/ru/rss/all/all/?fl=ru",
        "https://habr.com/ru/rss/hub/artificial_intelligence/?fl=ru",
        "https://habr.com/ru/rss/hub/android_dev/?fl=ru",
        "https://habr.com/ru/rss/hub/mobile_development/?fl=ru"
    ]
}

def get_news():
    news = []
    seen_titles = set()
    for url in RSS_FEEDS["tech"]:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if entry.title not in seen_titles:
                seen_titles.add(entry.title)
                news.append({"title": entry.title, "link": entry.link})
            if len(news) >= 10:
                break
        if len(news) >= 10:
            break
    return news

@app.route("/")
def home():
    articles = get_news()
    return render_template("index.html", articles=articles)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)