# LEAGUE = "Affliction"
# POESESSID = ""

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

    def __hash__(self) -> int:
        return hash(f"{self.name()}{self.base()}{self.implicits()}")

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

    def id(self) -> str:
        return self.data["id"]

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
        return self.__item_param("note") or ""


class Scraper:
    def __init__(self, league: str = "Standard", session: str = ""):
        self.league = league
        self.session = session

    def headers(self):
        return {
            "Origin": "https://www.pathofexile.com",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Cookie": f"POESESSID={self.session}",
        }

    def process_tokens(self, tokens: dict[str, str]) -> dict[str, list[Result]]:
        out = {}
        for name, token in tokens.items():
            print(f"processing '{name}'", flush=True)
            print("fetching item ids...", end=" ", flush=True)
            items = self.item_ids(token)
            print("OK", flush=True)
            print("fetching items data...", end=" ", flush=True)
            data = self.items_data(items)
            print("OK", flush=True)
            out[name] = data
        print("tokens processing finished", flush=True)
        return out

    def item_ids(self, token: str) -> list[str]:
        url = f"https://www.pathofexile.com/api/trade/search/{self.league}"

        with open(f"message/{token}.json") as message_file:
            mes_asc = message_file.read()
        mes_desc = mes_asc.replace('{"price":"asc"}', '{"price":"desc"}')

        asc = requests.post(url=url, headers=self.headers(), json=json.loads(mes_asc))
        desc = requests.post(url=url, headers=self.headers(), json=json.loads(mes_desc))

        if asc.status_code == 200 and desc.status_code == 200:
            ids = asc.json()["result"] + desc.json()["result"]
            return list(set(ids))

        return []

    def items_data(self, items: list[str]) -> list[Result]:
        n = len(items)
        items_data = []

        def grouper(it: list[str], n: int):
            return zip_longest(*([iter(it)] * n))

        for chunk in grouper(items, 10):
            items = [item for item in chunk if item]
            url = f"https://www.pathofexile.com/api/trade/fetch/{','.join(items)}"

            res = requests.get(url=url, headers=self.headers())

            if res.status_code != 200:
                print(res.status_code, end=" ", flush=True)
            else:
                print("+", end=" ", flush=True)
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
