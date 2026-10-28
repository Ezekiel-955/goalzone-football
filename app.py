from flask import Flask, jsonify, send_from_directory
from urllib.request import Request, urlopen
from xml.etree import ElementTree
from datetime import datetime, timezone
from pathlib import Path

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
FEED_URL = "https://feeds.bbci.co.uk/sport/football/rss.xml"


@app.route("/")
def home():
    return send_from_directory(BASE_DIR, "index.html")


@app.route("/api/news")
def news():
    try:
        request = Request(
            FEED_URL,
            headers={"User-Agent": "GoalZone/1.0"}
        )

        with urlopen(request, timeout=20) as response:
            root = ElementTree.fromstring(response.read())

        articles = []

        for item in root.findall("./channel/item")[:20]:
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            description = item.findtext("description", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()

            if title and link.startswith("https://"):
                articles.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "published": pub_date,
                    "source": "BBC Sport"
                })

        return jsonify({
            "source": "BBC Sport",
            "updated": datetime.now(timezone.utc).isoformat(),
            "articles": articles
        })

    except Exception:
        app.logger.exception("Unable to fetch football news")
        return jsonify({
            "error": "Unable to fetch football news"
        }), 502


if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
