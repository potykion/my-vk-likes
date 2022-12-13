import time

from helium import *

from src.models import PhotoLink, LikedImage, LikePages


def main():
    start_firefox('vk.com')

    go_to(LikePages.images(vk_id='16231309'))

    # todo save/load links to disk
    links = set()
    while True:
        new_links = set(PhotoLink.find_all())
        if new_links - links:
            links |= new_links
            print(f'Links so far: {len(links)}')
            scroll_down(1000)
            time.sleep(3)
        else:
            break

    # todo filter existing images
    liked_images = LikedImage.from_links(links)
    for index, img in enumerate(liked_images):
        print(f'Downloading images: {index + 1} / {len(liked_images)}')
        img.find_src()
        img.download()


if __name__ == '__main__':
    main()
