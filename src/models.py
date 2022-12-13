import dataclasses
import re
from typing import List, Iterable

import httpx
from helium import find_all, S, go_to
from selenium.webdriver.firefox.webelement import FirefoxWebElement


@dataclasses.dataclass(frozen=True)
class PhotoLink:
    link: str

    @property
    def id(self):
        return re.search(r'(photo[\d-]+_[\d-]+)', self.link).group()

    @classmethod
    def find_all(cls):
        links = find_all(S('a'))
        hrefs = [SimpleS(s).href for s in links]
        photo_hrefs = [href for href in hrefs if href and href.startswith('https://vk.com/photo')]
        return [cls(href) for href in photo_hrefs]


@dataclasses.dataclass()
class LikedImage:
    # photo-110973549_457270641
    id: str
    # https://sun9-23.userapi.com/impg/8Ul26H9-TH4tHvIU_4YTe_VUq32hywIuXTj7Tg/M2_fg8QLTtA.jpg?size=604x453&quality=95&sign=e66a8f8be539c7abe94345ef14025f74&type=album
    src: str = ''

    @property
    def photo_link(self):
        # https://vk.com/feed?section=likes&z=photo-110973549_457270641%2Fliked16231309
        # https://vk.com/feed?section=likes&z=photo-110973549_457270641
        return f'https://vk.com/feed?section=likes&z={self.id}'

    @classmethod
    def from_links(cls, links: Iterable[PhotoLink]):
        return [
            cls(link.id)
            for link in links
        ]

    def find_src(self):
        go_to(self.photo_link)
        img = SimpleS(find_all(S('#pv_photo img'))[0])
        self.src = img.src

    def download(self):
        assert self.src, 'Не выставлен src'

        with open(f'images/{self.id}.jpg', 'wb') as f:
            with httpx.stream('GET', self.src) as resp:
                for chunk in resp.iter_bytes():
                    f.write(chunk)


@dataclasses.dataclass()
class SimpleS:
    s: S

    @property
    def elem(self) -> FirefoxWebElement:
        return self.s.web_element

    def attr(self, attr_name):
        return self.elem.get_attribute(attr_name)

    @property
    def href(self):
        return self.attr('href')

    @property
    def src(self):
        return self.attr('src')


class LikePages:
    """
    go_to('https://vk.com/feed?section=likes')
    """

    @classmethod
    def images(cls, vk_id):
        return f'https://vk.com/feed?section=likes&z=album{vk_id}_0000000'
