import os
import json
from flask import Flask, jsonify, send_from_directory
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from xml.etree import ElementTree
from datetime import datetime, timezone, timedelta
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


@app.route("/api/fixtures")
def fixtures():
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY")

    if not api_key:
        return jsonify({"error": "Football API key is not configured"}), 503

    today = datetime.now(timezone.utc).date()
    end_date = today + timedelta(days=7)

    params = urlencode({
        "dateFrom": today.isoformat(),
        "dateTo": end_date.isoformat()
    })

    api_request = Request(
        "https://api.football-data.org/v4/matches?" + params,
        headers={"X-Auth-Token": api_key}
    )

    try:
        with urlopen(api_request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))

        matches = []

        for match in data.get("matches", []):
            score = match.get("score", {}).get("fullTime", {})

            matches.append({
                "id": match.get("id"),
                "date": match.get("utcDate"),
                "status": match.get("status"),
                "competition": match.get("competition", {}).get("name"),
                "homeTeam": match.get("homeTeam", {}).get("name"),
                "awayTeam": match.get("awayTeam", {}).get("name"),
                "homeScore": score.get("home"),
                "awayScore": score.get("away")
            })

        return jsonify({"matches": matches})

    except HTTPError as error:
        app.logger.exception("Football API returned an error")
        return jsonify({"error": "Football API request failed", "status": error.code}), 502

    except (URLError, TimeoutError):
        app.logger.exception("Unable to reach football API")
        return jsonify({"error": "Unable to reach football API"}), 502

    except Exception:
        app.logger.exception("Unable to load fixtures")
        return jsonify({"error": "Unable to load fixtures"}), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 10000))
    )
