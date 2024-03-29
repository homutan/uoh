from flask import Flask, render_template, request
from cache import ResultsCache
from scrape import Scraper, Result


LEAGUE = "Standard"
POESESSID = ""

tokens = {
    "Minion Wand": "ol2RYj4Ul",
    "Synth Helmet Base": "WqEpnQbcm",
    "Bow Caster Synth": "YDqoRd6cY",
}

app = Flask(__name__, static_folder="public")
cache = ResultsCache()
scraper = Scraper(league=LEAGUE, session=POESESSID)


def is_item_in(item: Result, list: list[Result]) -> bool:
    for i in list:
        if item == i:
            return True
    return False


def diff_items(
    latest: list[Result], snapshot: list[Result]
) -> tuple[list[Result], list[Result]]:
    listed_items = []
    unlisted_items = []

    for cache_item in snapshot:
        if not is_item_in(cache_item, latest):
            unlisted_items.append(cache_item)

    for new_item in latest:
        if not is_item_in(new_item, snapshot):
            listed_items.append(new_item)

    return (listed_items, unlisted_items)


@app.get("/")
def index():
    token_name = request.args.get("token")
    if not token_name or token_name not in tokens.keys():
        token_name = next(iter(tokens.keys()))
    token = tokens[token_name]

    snapshot = request.args.get("snapshot")
    snapshots = cache.snapshots(token)[1:]
    if not snapshot or not cache.has_snapshot(token=token, name=snapshot):
        snapshot = next(iter(snapshots)) if snapshots else ""

    latest_cache_items = cache.latest(token)
    for i in latest_cache_items:
        print(i.name())
    print("latest", len(latest_cache_items))

    snapshot_cache_items = cache.between(token=token, file=snapshot)
    for i in snapshot_cache_items:
        print(i.name())
    print("snapshot", len(snapshot_cache_items))

    listed_items, unlisted_items = diff_items(latest_cache_items, snapshot_cache_items)

    # TODO: filter(lambda x: x.note())

    return render_template(
        "index.html",
        listed_items=listed_items,
        unlisted_items=unlisted_items,
        tokens_names=list(tokens.keys()),
        selected_token_name=token_name,
        snapshots=snapshots,
        selected_snapshot=snapshot,
    )


@app.post("/update")
def update():
    data = scraper.process_tokens(tokens)
    for token_name, items_data in data.items():
        cache.write(token=tokens[token_name], items_data=items_data)
    return {}, 200
