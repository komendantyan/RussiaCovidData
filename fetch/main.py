#!/usr/bin/env python3
# coding: utf-8

import requests_html
import re
import json
import logging
import sys

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


SITE = 'https://www.rospotrebnadzor.ru'
NEWS_PAGE = f"{SITE}/about/info/news/?PAGEN_1={{}}"


def smart_parse_int(string):
    return int(re.sub('[^0-9]', '', string))


class OneDay:
    def __init__(self, resp):
        self._resp = resp
        self._html = resp.html

    def _regions(self):
        regions = {}

        for item in self._html.find('div', containing='-'):
            text = item.text
            if len(text) > 100:
                continue
            match = re.search(r'([-\w ()]+) ?- ?([0-9]+)', text)
            if match:
                name, cases = match.groups()
                regions[name.strip()] = int(cases)
            else:
                print(text)

        assert len(regions) > 0, "Не удалось прочитать список регионов"

        return regions

    def _new(self):
        parsed = self._html.search('выявлен{new}нов{}случ{}в{new_regions}регио')

        new_cases = int(re.sub('[^0-9]', '', parsed['new']))
        new_regions = int(re.sub('[^0-9]', '', parsed['new_regions']))

        return new_cases, new_regions

    def _total(self):
        parsed = self._html.search("сегод{}выявлен{}случ{}в{} рег")
        total_cases = smart_parse_int(parsed[1])
        total_regions = smart_parse_int(parsed[3])
        return total_cases, total_regions

    def _total_healthy(self):
        parsed = self._html.search("выписан{} челов")
        total_healthy = smart_parse_int(parsed[0])
        return total_healthy

    def _date(self):
        parsed = self._html.search("{day:2d}.{month:2d}.{year:4d} г")
        return "{year:04d}-{month:02d}-{day:02d}".format(**parsed.named)

    def __call__(self):
        link = self._resp.request.url
        LOGGER.info(f"Parse link {link}")

        date = self._date()

        regions = self._regions()
        new_cases, new_regions = self._new()
        total_cases, total_regions = self._total()
        total_healthy = self._total_healthy()

        # assert len(regions) == new_regions, "Не сходится список регионов с общим числом регионов: %r != %r" % (len(regions), new_regions)
        assert sum(regions.values()) == new_cases, "Несовпадает число новых случаев всего с суммой по регионам: %r != %r" % (sum(regions.values()), new_cases)

        assert total_regions == 85, "Всего регионов меньше 85: %r" % total_regions

        return dict(
            date=date,
            link=link,
            new=new_cases,
            new_reg=new_regions,
            total=total_cases,
            total_healthy=total_healthy,
            total_reg=total_regions,
            **regions
        )


def main():
    session = requests_html.HTMLSession()

    daily = []

    for pagen in range(1, int(sys.argv[1]) + 1):
        resp = session.get(NEWS_PAGE.format(pagen))

        for link in resp.html.find('a', containing='О подтвержд'):
            page = link.absolute_links.pop()
            resp = session.get(page)
            resp.raise_for_status()

            try:
                daily.append(OneDay(resp)())
            except AssertionError:
                LOGGER.exception("")

    daily.sort(key=lambda x: x['date'], reverse=True)
    print(json.dumps(daily, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
