import glob
import os


def crop_center(pil_img, crop_width, crop_height):
    img_width, img_height = pil_img.size
    return pil_img.crop(((img_width - crop_width) // 2,
                         (img_height - crop_height) // 2,
                         (img_width + crop_width) // 2,
                         (img_height + crop_height) // 2))


def get_latest_file(dir_path, ext_fmt="*"):
    list_of_files = glob.glob(os.path.join(dir_path, ext_fmt))
    if len(list_of_files):
        return max(list_of_files, key=os.path.getctime)
    else:
        return None

