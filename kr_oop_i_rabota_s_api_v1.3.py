import requests
import json
import os
from tqdm import tqdm
from time import sleep

from pprint import pprint
vk_token="{сюда помещаем VK-токен}"
ya_token="{сюда помещаем Yandeх-токен}"
vk_id = {сюда помещем ID-номер пользователя VK (без префикса "id"), чьи фото копируем}


class VK_Connector:
    def __init__(self, access_token, version="5.199"):
        self.access_token = access_token
        self.version = version
#       self.base_url = "https://api.vk.com/method/"
        self.base_url = "https://api.vk.ru/method/"
        self.params = {
            "access_token": self.access_token,
            "v": self.version
        }


    def photos_get(self, user_id, count=1, album_id="profile"):
        url = f'{self.base_url}photos.get'
        params = {**self.params, 
                  "owner_id":user_id,
                  "album_id": album_id,
                  "extended": 1,
                  "count": count
                  }
        response = requests.get(url, params = params)
        return response.json()

class YAD_connector:
    def __init__(self, access_token):
        self.access_token = access_token
        self.log = []
        self.headers = {
            "Authorization": self.access_token
        }
        self.create_folder_url = 'https://cloud-api.yandex.net/v1/disk/resources'
        self.upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'

    def create_dir(self, dst_dir="VK_PHOTO"):
        self.params = {
            "path": dst_dir
        }
        response = requests.put(self.create_folder_url,
                                headers=self.headers,
                                params=self.params)

    

    def write_file(self,  dst_f_name, src_f_name="tmp", dst_dir="VK_PHOTO"):
 

        self.params = {
             'path': f'{dst_dir}/{str(dst_f_name) + ".jpg"}'
            }
        
        while True:
            response = requests.get(self.upload_url,
                                params=self.params,
                                headers=self.headers)
        
            if response.status_code == 409:
                file_name = dst_f_name.split(".")[-1]
                file_version = int(dst_f_name.split("_")[-1])
                if str(file_version) == dst_f_name:
                    dst_f_name = dst_f_name + "_1"
                else:
                    file_version += 1
                    dst_f_name = str(dst_f_name.split("_")[0:-1]) + "_" + str(file_version)
                

                self.params = {
                         'path': f'{dst_dir}/{str(dst_f_name)+ ".jpg"}'
                        }
            else:
                break
        

        
        upload_link = response.json()['href']

        with open(src_f_name, 'rb') as f:
            response = requests.put(upload_link, files={'file': f})

        return dst_f_name
    
    def save_upload_info_to_logjson(self, f_name, f_size):
        data = {
            "file_name": str(f_name) + ".jpg",
            "size": str(f_size)
            }
        with open(f".\{str(f_name)}.json", 'w') as file:
            json.dump(data, file)

    
class Internet_Media_object:
    def __init__(self):
        pass

    def save_picture_to_file (self, url, tmp_f_name='tmp'):
        self.url = url
        response = requests.get(self.url)
        with open(tmp_f_name, 'wb') as f:
            f.write(response.content)

        file_size = os.path.getsize(f".\{tmp_f_name}")

        return file_size
    
class VK_Yandex_Brige(VK_Connector, YAD_connector, Internet_Media_object):
    def __init__(self, vk_token, ya_token):
        self.photos = {}
        self.vk = VK_Connector(vk_token)
        self.yd = YAD_connector(ya_token)
        self.imo = Internet_Media_object()


    def copy_photo_to_yandex_disk(self, vk_id, count_photo = 5, vk_album_id="profile"):
        self.src_res = self.vk.photos_get(vk_id, 1, vk_album_id)
        self.tot_photos = self.src_res["response"]["count"]
        self.src_res = self.vk.photos_get(vk_id, self.tot_photos )

        self.dst_res = self.yd.create_dir()

        for item in self.src_res["response"]["items"]:
            src_likes = str(item["likes"]["count"])
            src_url = item["orig_photo"]["url"]
            src_height = item["orig_photo"]["height"]
            src_width = item["orig_photo"]["width"]
            self.photos[src_height*src_width] = {"url":src_url,  "likes":src_likes}


            self.photos = list(sorted(self.photos.items()))[0:count_photo]
            self.photos = dict(self.photos)

        for item in tqdm(list (self.photos.keys())):
            f_size = self.imo.save_picture_to_file(self.photos[item]["url"])
            f_name = self.yd.write_file(self.photos[item]["likes"])
            self.yd.save_upload_info_to_logjson (f_name, f_size)
            print(item)



vk_ya = VK_Yandex_Brige(vk_token, ya_token)
vk_ya.copy_photo_to_yandex_disk(vk_id)

pass



