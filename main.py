from helium import *

from src.models import PhotoLink, LikedImage, LikePages, PhotoLinkSet, FS


def main():
    links = load_links()
    auth()
    collect_links(links)
    images = create_images_from_links(links)
    save_existing_images_info(images)
    download_missing_images(images)


def load_links():
    """Грузит ссылки на понравившиеся картинки из файла"""
    return FS(PhotoLinkSet()).load()


def auth():
    """
    Открывает ВК и жмет на кнопку 'QR code'
    Авторизацию необходимо осуществить ВРУЧНУЮ
    """
    start_firefox('vk.com')
    click('QR code')


def collect_links(links: FS[PhotoLinkSet]):
    """
    Основа: скрепинг ссылок на картинки, сохранение в файл, скролл вниз и повтор цикцла.
    Остановить этот цикл нужно ВРУЧНУЮ
    """
    go_to(LikePages.images(vk_id='16231309'))
    while True:
        new_links = PhotoLink.find_all()
        links.update(new_links)
        links.save()
        press(ARROW_DOWN)
        print(f'Links scrapped: {len(links)}')


def create_images_from_links(links):
    """Создание картинок из ссылок (без src)"""
    return LikedImage.from_links(links.links)


def save_existing_images_info(images):
    """(Опционально) Сохраняем инфу о существующих картинках"""
    existing_images = [img for img in images if img.exists()]
    FS(
        PhotoLinkSet(links=PhotoLink.from_images(existing_images)),
        suffix='existing'
    ).save()


def download_missing_images(images):
    """
    Фильтруем картинки, которые качали ранее,
        начинаем скачивание, переходя по ссылкам
    Может быть ситуация когда картинка не скачалась: картинку скрыли/удалили
    """
    images = [img for img in images if not img.exists()]
    for index, img in enumerate(images):
        print(f'Downloading images: {index + 1} / {len(images)}')
        try:
            img.find_src()
        except IndexError:
            continue
        else:
            img.download()


if __name__ == '__main__':
    main()
