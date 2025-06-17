import logging
import requests
import json
import time
import typing

from dataclasses import dataclass
from itertools import zip_longest


@dataclass
class Result:
    data: object

    def __eq__(self, other: typing.Self) -> bool:
        return (
            self.name() == other.name()
            and self.base() == other.base()
            and self.implicits() == other.implicits()
        )

    def __lt__(self, other: typing.Self):
        return self.name() < other.name()

    def __hash__(self) -> int:
        return hash(f"{self.name()}{self.base()}")

    def pretty_print(self):
        print(self.id())

        name = self.name()
        if name:
            print(name)

        base = self.base()
        if base:
            print(base)

        separator = "-----"

        print(separator)

        implicits = self.implicits()
        for implicit in implicits:
            print(implicit)

        if implicits:
            print(separator)

        fractureds = self.fractureds()
        for fracture in fractureds:
            print(fracture)

        explicits = self.explicits()
        for explicit in explicits:
            print(explicit)

        crafteds = self.crafteds()
        for crafted in crafteds:
            print(crafted)

        if fractureds or explicits or crafteds:
            print(separator)

        note = self.note()
        print(note or "empty price note", end="\n\n")

    def __item_has(self, pa: str) -> bool:
        return pa in self.data["item"]

    def __item_param(self, pa: str) -> str | object | None:
        return self.data["item"][pa] if self.__item_has(pa) else None

    def __item_param_list(self, pa: str) -> list[str]:
        out = self.__item_param(pa)
        return list(out) if out else []

    def compare(self, other: typing.Self) -> bool:
        return (
            self.name() == other.name()
            and self.base() == other.base()
            and self.implicits() == other.implicits()
            and self.price() == other.price()
        )

    def id(self) -> str:
        return f"{self.name()}{self.base()}"
        # return self.data["id"]

    def name(self) -> str:
        return self.__item_param("name") or ""

    def base(self) -> str:
        return self.__item_param("typeLine") or self.__item_param("baseType") or ""

    def implicits(self) -> list[str]:
        return self.__item_param_list("implicitMods")

    def explicits(self) -> list[str]:
        return self.__item_param_list("explicitMods")

    def fractureds(self) -> list[str]:
        return self.__item_param_list("fracturedMods")

    def crafteds(self) -> list[str]:
        return self.__item_param_list("craftedMods")

    def note(self) -> str:
        listing_price = self.listing_price()
        return (
            f"{listing_price["type"]} {listing_price["amount"]} {listing_price["currency"]}"
            if "type" in listing_price
            else ""
        )
        # return self.__item_param("note") or ""

    def listing_price(self) -> str:
        return self.data["listing"]["price"] if "price" in self.data["listing"] else ""

    def price(self) -> float:
        note = self.note()
        return float(note.split(" ")[1]) or 0 if note else 0


class Scraper:
    def __init__(
        self, logger: logging.Logger, league: str = "Standard", session: str = ""
    ):
        self.league: str = league
        self.session: str = session
        self.logger: logging.Logger = logger

    def headers(self):
        return {
            "Origin": "https://www.pathofexile.com",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Cookie": f"POESESSID={self.session}",
        }

    def print_stage(self, message: str):
        self.logger.info(message)

    def process_tokens(self, tokens: dict[str, str]) -> dict[str, list[Result]]:
        out: dict[str, list[Result]] = {}
        for name, token in tokens.items():
            self.print_stage(f"processing '{name}'")
            self.print_stage("fetching item ids")
            items = self.item_ids(token)
            self.print_stage("fetching items data")
            data = self.items_data(items)
            out[name] = data
            self.print_stage("done, waiting for 5 seconds")
            time.sleep(5)
        self.print_stage("finished processing tokens")
        return out

    def item_ids(self, token: str) -> list[str]:
        url = f"https://www.pathofexile.com/api/trade/search/{self.league}"

        with open(f"message/{token}.json") as message_file:
            mes_asc = message_file.read()
        mes_desc = mes_asc.replace('{"price":"asc"}', '{"price":"desc"}')

        asc = requests.post(url=url, headers=self.headers(), json=json.loads(mes_asc))
        desc = requests.post(url=url, headers=self.headers(), json=json.loads(mes_desc))

        if asc.status_code == 200 and desc.status_code == 200:
            ids: list[str] = asc.json()["result"] + desc.json()["result"]
            uniques = list(set(ids))
            self.print_stage(f"200 OK: {len(uniques)} ids")
            return uniques

        self.print_stage(f"failed: asc {asc.status_code}, desc {desc.status_code}")
        return []

    def items_data(self, items: list[str]) -> list[Result]:
        n = len(items)
        items_data: list[Result] = []

        def grouper(it: list[str], n: int):
            return zip_longest(*([iter(it)] * n))

        for index, batch in enumerate(grouper(items, 10)):
            items = [item for item in batch if item]
            url = f"https://www.pathofexile.com/api/trade/fetch/{','.join(items)}"

            res = requests.get(url=url, headers=self.headers())

            if res.status_code != 200:
                self.print_stage(f"batch {index} failed: {res.status_code}")
            else:
                self.print_stage(f"batch {index}: 200 OK")
                items_data.extend([Result(data) for data in res.json()["result"]])

            # ghetto rate limiting
            # 16:12:160
            # 6:4:10
            if n > 160:
                time.sleep(1)
            if n > 60:
                time.sleep(1)
            n -= 10

        return items_data
