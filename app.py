import logging
from flask import Flask, render_template, request
from datetime import datetime
from cache import ResultsCache, FILENAME_TIMESTAMP_FORMAT as IN_FORMAT
from scrape import Scraper, Result
from scheduler import initialize_scheduler, shutdown_scheduler
from dotenv import dotenv_values, load_dotenv

import os
import atexit

_ = load_dotenv()

LEAGUE = os.getenv("LEAGUE", "Standard")
POESESSID = os.getenv("POESESSID", "")

LOG_LV = os.getenv("LOG", "WARNING").upper()
logging.basicConfig(
    level=logging.getLevelNamesMapping().get(LOG_LV) or logging.WARNING,
    format="[%(asctime)s][%(levelname)s][%(name)s]: %(message)s",
)

# tokens = {"pickapoboo": "El9lgORf5", "tzdprm": "K4gwGDLF5"}

env = dotenv_values()
tokens: dict[str, str] = {}
tokens_str = env.get("FILTERS", None)

if tokens_str:
    for pair in tokens_str.split(","):
        if "=" in pair:
            name, token = pair.split("=", 1)
            tokens[name.strip()] = token.strip()


app = Flask(__name__, static_folder="public")
app.config["DEBUG"] = os.getenv("DEBUG", "False").lower() == "true"

# app.logger.propagate = False
# app.logger.setLevel(level=logging.getLevelNamesMapping().get(LOG_LV) or logging.WARNING)

cache = ResultsCache()
scraper = Scraper(logger=app.logger, league=LEAGUE, session=POESESSID)


def is_item_in(item: Result, list: list[Result]) -> bool:
    for i in list:
        if item == i:
            return True
    return False


def diff_items(
    latest: list[Result], snapshot: list[Result], intermediate: list[Result]
) -> tuple[list[Result], list[Result], list[Result]]:
    latest_dict = {item.id(): item for item in latest}
    snapshot_dict = {item.id(): item for item in snapshot}
    intermediate_dict = {item.id(): item for item in intermediate}

    listed_items: list[Result] = []
    unlisted_items: list[Result] = []
    rest: list[Result] = []

    # Проверяем предметы из промежуточных снапшотов
    for id, item in intermediate_dict.items():
        if id not in snapshot_dict:
            if id in latest_dict:
                listed_items.append(item)
            else:
                unlisted_items.append(item)  # Предмет появился и был продан
        elif id not in latest_dict:
            unlisted_items.append(item)

    # Проверяем предметы из последнего снапшота
    for id, item in latest_dict.items():
        if id not in snapshot_dict and id not in intermediate_dict:
            listed_items.append(item)
        elif id in snapshot_dict:
            rest.append(item)

    # Проверяем предметы из начального снапшота
    for id, item in snapshot_dict.items():
        if id not in latest_dict and id not in intermediate_dict:
            unlisted_items.append(item)

    return (listed_items, unlisted_items, rest)


@app.get("/")
def index():
    app.logger.debug("Hi pidoras")
    token_name = request.args.get("token")
    if not token_name or token_name not in tokens.keys():
        token_name = next(iter(tokens.keys()))
    token = tokens[token_name]

    snapshots = cache.snapshots(token)

    snapshot = request.args.get("snapshot")
    if not snapshot or not cache.has_snapshot(token=token, name=snapshot):
        snapshot = next(iter(snapshots[1:])) if len(snapshots) > 1 else None

    latest = request.args.get("latest")
    if not latest or not cache.has_snapshot(token=token, name=latest):
        latest = snapshots[0] if len(snapshots) > 0 else None

    if snapshot is None or latest is None:
        return render_template(
            "index.html",
            listed_items=[],
            unlisted_items=[],
            rest_items=[],
            tokens_names=list(tokens.keys()),
            selected_token_name=token_name,
            snapshots=snapshots,
            selected_snapshot=snapshot,
            selected_latest=latest,
            time="Нужны апдейты",
        )

    # app.logger.info(f"Selected snapshot: {snapshot}")
    # app.logger.info(f"Selected latest: {latest}")

    latest_cache_items = cache.at(token=token, file=latest)
    snapshot_cache_items = cache.at(token=token, file=snapshot)
    intermediate_items = cache.between(token=token, begin=snapshot, end=latest)

    # app.logger.info(f"Latest cache items: {len(latest_cache_items)}")
    # app.logger.info(f"Snapshot cache items: {len(snapshot_cache_items)}")
    # app.logger.info(f"Intermediate items: {len(intermediate_items)}")

    listed, unlisted, rest = diff_items(
        latest_cache_items, snapshot_cache_items, intermediate_items
    )

    # app.logger.info(
    #     f"After diff_items - Listed: {len(listed)}, Unlisted: {len(unlisted)}, Rest: {len(rest)}"
    # )

    listed.sort(key=lambda x: x.price(), reverse=True)
    unlisted.sort(key=lambda x: x.price(), reverse=True)
    rest.sort(key=lambda x: x.price(), reverse=True)

    OUT_FORMAT = "%Y-%m-%d %H:%M:%S"

    begin = datetime.strptime(snapshot, IN_FORMAT).strftime(OUT_FORMAT)
    end = datetime.strptime(latest, IN_FORMAT).strftime(OUT_FORMAT)

    return render_template(
        "index.html",
        listed_items=listed,
        unlisted_items=unlisted,
        rest_items=rest,
        tokens_names=list(tokens.keys()),
        selected_token_name=token_name,
        snapshots=snapshots,
        selected_snapshot=snapshot,
        selected_latest=latest,
        time=f"{begin} ~ {end}",
    )


@app.post("/update")
def update() -> tuple[dict[str, str], int]:
    data = scraper.process_tokens(tokens)
    for token_name, items_data in data.items():
        cache.write(token=tokens[token_name], items_data=items_data)
    return {}, 200


if __name__ == "__main__":
    initialize_scheduler(app.logger)
    _ = atexit.register(lambda: shutdown_scheduler(app.logger))
    app.run()
