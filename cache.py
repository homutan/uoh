import os
import json

from scrape import Result
from datetime import datetime


FILENAME_TIMESTAMP_FORMAT = "%Y%m%d%H%M%S"  # 20240309213217


class ResultsCache:
    def __init__(self, dir="cache"):
        if not os.path.exists(dir):
            os.mkdir(dir)
        self.dir = dir

    def __token_dir(self, token: str) -> str:
        token_dir = f"{self.dir}/{token}"
        if not os.path.exists(token_dir):
            os.mkdir(token_dir)
        return token_dir

    def __token_file(self, token: str, file: str | None = None) -> str:
        filename = file or datetime.strftime(datetime.now(), FILENAME_TIMESTAMP_FORMAT)
        return f"{self.__token_dir(token)}/{filename}"

    def has_snapshot(self, token: str, name: str) -> bool:
        for file in os.listdir(self.__token_dir(token)):
            if file == name:
                return True
        return False

    def snapshots(self, token: str) -> list[str]:
        return list(reversed(os.listdir(self.__token_dir(token))))

    def write(self, token: str, items_data: list[Result]):
        with open(self.__token_file(token=token), mode="w") as cache:
            cache.write(json.dumps([r.data for r in items_data], sort_keys=True))

    def at(self, token: str, file: str) -> list[Result]:
        if not os.path.exists(self.__token_file(token=token, file=file)):
            return []
        with open(self.__token_file(token=token, file=file)) as cache:
            return [Result(data) for data in json.loads(cache.read())]

    def __token_files(self, token: str) -> list[tuple[datetime, str]]:
        files: list[tuple[datetime, str]] = []
        for file in os.listdir(self.__token_dir(token)):
            timestamp = datetime.strptime(file, FILENAME_TIMESTAMP_FORMAT)
            files.append((timestamp, file))
        return files

    def between(self, token: str, file: str) -> list[Result]:
        files = self.__token_files(token)
        if not files or not os.path.exists(self.__token_file(token=token, file=file)):
            return []

        files.sort(reverse=True)
        begin = files.index((datetime.strptime(file, FILENAME_TIMESTAMP_FORMAT), file))
        out = []
        for _, ifile in files[begin:]:
            with open(self.__token_file(token=token, file=ifile)) as cache:
                out.append([Result(data) for data in json.loads(cache.read())])

        return list(set([i for sub in out for i in sub]))

    def latest(self, token: str) -> list[Result]:
        files = self.__token_files(token)
        if not files:
            return []

        files.sort(reverse=True)

        _, file = files[0]
        with open(self.__token_file(token=token, file=file)) as cache:
            return [Result(data) for data in json.loads(cache.read())]
