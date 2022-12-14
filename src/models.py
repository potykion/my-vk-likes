import dataclasses
import json
import os.path
import re
from json import JSONDecodeError
from typing import List, Iterable, TypeVar, Type, Union, Generic, Set

import httpx
from helium import find_all, S, go_to
from pydantic import BaseModel, Field
from selenium.webdriver.firefox.webelement import FirefoxWebElement

from src.cfg import DATA_DIR, IMAGES_DIR


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
    def from_links(cls, links: Iterable['PhotoLink']):
        return [
            cls(link.id)
            for link in links
        ]

    def find_src(self):
        go_to(self.photo_link)
        img = SimpleS(find_all(S('#pv_photo img'))[0])
        self.src = img.src
        return self

    @property
    def img_path(self):
        return IMAGES_DIR / f'{self.id}.jpg'

    def exists(self):
        return os.path.exists(self.img_path)

    def download(self):
        assert self.src, 'Не выставлен src'

        with open(self.img_path, 'wb') as f:
            with httpx.stream('GET', self.src) as resp:
                for chunk in resp.iter_bytes():
                    f.write(chunk)


class PhotoLink(BaseModel, frozen=True):
    link: str

    @property
    def id(self):
        return re.search(r'(photo[\d-]+_[\d-]+)', self.link).group()

    @classmethod
    def find_all(cls):
        links = find_all(S('a'))
        hrefs = [SimpleS(s).href for s in links]
        photo_hrefs = [href for href in hrefs if href and href.startswith('https://vk.com/photo')]
        return [cls(link=href) for href in photo_hrefs]

    @classmethod
    def from_images(cls, images: List[LikedImage]):
        return [
            cls(link=f'https://vk.com/{img.id}')
            for img in images
        ]


class PhotoLinkSet(BaseModel):
    links: List[PhotoLink] = Field(default_factory=list)

    def update(self, links):
        self.links = list({*self.links, *links})

    def lacks(self, links):
        return bool(set(links) - set(self.links))

    def __len__(self):
        return len(self.links)


T = TypeVar('T', bound=BaseModel)


class FS(Generic[T]):
    def __init__(self, wraps: T, suffix: str = ''):
        self.wraps = wraps
        self.suffix = suffix

    def __getattr__(self, item):

        return getattr(self.wraps, item)

    def __len__(self):
        """
        >>> len(FS(PhotoLinkSet()))
        0
        """
        return len(self.wraps)

    @property
    def type_(self) -> Type[T]:
        return type(self.wraps)

    @property
    def file(self):
        filename = self.type_.__name__
        if self.suffix:
            filename = f'{filename}_{self.suffix}'
        return DATA_DIR / f'{filename}.json'

    def load(self):
        if os.path.exists(self.file):
            with open(self.file, 'r') as f:
                try:
                    return FS(self.type_(**json.loads(f.read())))
                except JSONDecodeError:
                    return self
        else:
            return self

    def save(self):
        with open(self.file, 'w') as f:
            f.write(self.wraps.json())


@dataclasses.dataclass()
class SimpleS:
    s: S

    @property
    def elem(self) -> FirefoxWebElement:
        return self.s.web_element

    def attr(self, attr_name):
        # todo rewrite it using str(S) + re.search
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
