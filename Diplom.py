from pprint import pprint
import requests
from tqdm import tqdm
import json
from time import sleep


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.token = token
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}
        self.user_id = None
        self.album_info = dict()

    def get_id_user(self, login):
        if login.isdigit():
            self.user_id = int(login)
        else:
            user_params = {'screen_name': login}
            res = requests.get(self.url + 'utils.resolveScreenName', params={**self.params, **user_params})
            self.user_id = res.json()['response']['object_id']
        print(self.user_id)

    def all_albums(self):
        album_params = {'owner_id': self.user_id}
        res = requests.get(self.url + 'photos.getAlbums', params={**self.params, **album_params})
        self.album_info.update({"стена": 'wall', "аватар": 'profile'})

        if "error" not in res.json():
            res = res.json()['response']['items']
            for album in res[0:]:
                self.album_info.update({album['title']: album['id']})
        print("\nСписок фотоальбомов пользователя: ")
        pprint(list(self.album_info.keys()))

    def get_photos(self, album, number):
        data = dict()
        photos_list = []

        if album in self.album_info.keys():
            photos_params = {
                'user_id': self.user_id,
                'album_id': self.album_info[album],
                'count': number,
                'extended': '1'
            }
            res = requests.get(self.url + 'photos.get', params={**self.params, **photos_params})
            res = res.json()['response']['items']

            for photo in res[0:]:
                info_photos = dict(
                    file_name=f"{photo['likes']['count']}_{photo['date']}.jpg",
                    size=photo['sizes'][-1]['type'],
                    URL_photo=photo['sizes'][-1]['url'])
                photos_list.append(info_photos)

            json_list = []
            for photos in photos_list:
                json_list.append({"file_name": photos['file_name'], "size": photos['size']})
            data[album] = json_list

            with open("info_photos.json", 'w', encoding='utf-8')as f:
                json.dump(data, f, ensure_ascii=False)
            return photos_list
        else:
            print(f'Альбома {album} не существует')


class YaDiscUser:
    def __init__(self, token):
        self.token = token
        self.headers = {'Authorization': f'OAuth {self.token}'}

    def create_folder(self, folder_name):
        url = 'https://cloud-api.yandex.net/v1/disk/resources'
        res = requests.put(url, headers=self.headers, params={'path': folder_name})

        if res.status_code == 201:
            print(f'\nПапка "{folder_name}" успешно создана')
            return True
        elif res.status_code == 409:
            print(f'\nПапка {folder_name} уже существует')
            return True
        return False

    def get_upload_link(self, file_path):
        upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        params = {'path': file_path, 'overwrite': 'true'}
        response = requests.get(upload_url, headers=self.headers, params=params)
        return response.json()

    def upload_photos(self, path: str, photos: list):
        res = None
        for photo in tqdm(photos):
            res = requests.post('https://cloud-api.yandex.net/v1/disk/resources/upload',
                                params={'path': f"{path}/{photo['file_name']}", 'url': photo['URL_photo']},
                                headers=self.headers)
            sleep(0.1)

        if res.status_code == 202:
            print("Фото успешно загружены на ЯндексДиск")
        else:
            print("Ошибка загрузки")


def execute_upload():
    vk_token = input("Введите токен пользователя Vk: ")
    vk_client = VkUser(vk_token, '5.130')

    vk_user_id = input("Введите id или логин пользователя Vk: ")
    vk_client.get_id_user(vk_user_id)

    vk_client.all_albums()

    folder = input("\nВыберите фотоальбом для загрузки: ")
    max_photos_number = int(input("Введите колличество фотографий: "))
    photos = vk_client.get_photos(folder, max_photos_number)

    if photos:
        ya_disc_client = YaDiscUser(input("\nВведите токен пользователя YandexDisc: "))
        ya_folder = input('ВВедите название новой папки на ЯндексДиске: ')
        create_folder_status = ya_disc_client.create_folder(ya_folder)

        if create_folder_status:
            ya_disc_client.upload_photos(path=ya_folder, photos=photos)


if __name__ == '__main__':
    execute_upload()