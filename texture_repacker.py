import os
import json


output_path = os.getcwd()
textures_path = output_path+"\\textures\\"
os.chdir(textures_path)
all_textures = sorted(os.listdir(textures_path))
texture_list = []

dds_header_size = 128


def get_level_data(data):
    with open(output_path+'\\level_data.json') as f:
        level_data = json.load(f)
        return level_data[current_level][data]


def get_level_list():
    with open(output_path+'\\level_data.json') as f:
        return json.load(f).keys()


if not os.path.exists(textures_path):
    print("textures folder doesn't exist")
    exit()


def construct_header():
    header = b'HOT \x01\x00\x00\x00'
    header += (36 + ((32 * len(texture_list)) - 8) + len(filename_table)).to_bytes(4, byteorder='little')  # headers offset
    header += (36 + ((32 * len(texture_list)) - 8) + len(filename_table) + (128 * len(texture_list))).to_bytes(4, byteorder='little')  # data offset
    return header + 20*b'\x00'


def construct_filemetadata():
    mystery_number_array = get_level_data('mystery_numbers')
    fileinfo_table = b''
    dynamic_offset = 0
    i = 0
    metadata_size = 32
    headers_offset = len(header_bytes) + ((metadata_size * len(texture_list)) - 8) + len(filename_table)
    data_offset = headers_offset + (dds_header_size * len(texture_list)) + get_level_data('padding')

    for texture in texture_list:
        if texture.startswith('lightmap'):
            path = textures_path+'lightmaps\\'+current_level+'\\'
        else:
            path = textures_path
        fileinfo_table += dds_header_size.to_bytes(4, byteorder='little')  # header size
        fileinfo_table += (headers_offset + (dds_header_size * i)).to_bytes(4, byteorder='little')  # header offset
        fileinfo_table += os.path.getsize(path+texture).to_bytes(4, byteorder='little')  # file size
        fileinfo_table += b'\x00\x00\x00\x00'  # blank
        fileinfo_table += (data_offset + dynamic_offset).to_bytes(4, byteorder='little')  # file offset
        fileinfo_table += b'\x00\x00\x00\x00'  # blank
        if i < len(texture_list)-1:
            fileinfo_table += int(mystery_number_array[i]).to_bytes(4, byteorder='little')  # unknown number
            fileinfo_table += b'\x00\x00\x00\x00'  # blank
            dynamic_offset += (os.path.getsize(path+texture)-dds_header_size+16)
            i += 1
    return fileinfo_table


def construct_filenames():
    file_name_table = b''

    for texture in texture_list:
        texturename_byte_remainder = -len(bytes(texture, "utf-8")) % 4
        if texturename_byte_remainder == 0:
            byte_padding = 4
        else:
            byte_padding = texturename_byte_remainder
        file_name_table += bytes(texture, "utf-8")+(b'\x00'*byte_padding)

    return file_name_table


def construct_file_headers():
    file_header_table = b''
    i = 0
    for texture in texture_list:
        if texture.startswith('lightmap'):
            path = textures_path+'lightmaps\\'+current_level+'\\'
        else:
            path = textures_path
        with open(path+texture, "rb") as file:
            file_header_table += file.read(dds_header_size)
            i += 1
    return file_header_table


def construct_raw_data(padding):
    texture_byte_padding = 16*b'\x00'
    raw_data = padding*b'\x00'
    for texture in texture_list:
        if texture.startswith('lightmap'):
            texturepath = textures_path+'lightmaps\\'+current_level+'\\'+texture
        else:
            texturepath = textures_path+texture
        with open(texturepath, "rb") as file:
            file.seek(128)
            raw_data += file.read()
            raw_data += texture_byte_padding

    return raw_data


for area in get_level_list():
    current_level = area
    if not os.path.exists(output_path+get_level_data('path')):
        os.makedirs(output_path+get_level_data('path'))
    with open(output_path+get_level_data('path')+"textures.hot", "w+b") as t:
        texture_list.clear()
        texture_list = get_level_data('textures')

        filename_table = construct_filenames()
        header_bytes = construct_header()
        t.write(header_bytes)  # writes header
        filemetadata = construct_filemetadata()
        t.write(filemetadata)  # writes file info tables
        t.write(filename_table)  # writes filenames table
        fileheaders = construct_file_headers()
        t.write(fileheaders)  # writes fileinfo table
        raw_data_bytes = construct_raw_data(get_level_data('padding'))
        t.write(raw_data_bytes)

        totalsize = len(header_bytes + filemetadata + filename_table + fileheaders + raw_data_bytes)
        t.seek(16)
        t.write(totalsize.to_bytes(4, byteorder='little'))

        t.seek(20)
        t.write((len(header_bytes + filemetadata)).to_bytes(4, byteorder='little'))

        t.seek(24)
        t.write(len(texture_list).to_bytes(4, byteorder='little'))

        print(area+" textures created with "+str(texture_list.__len__())+" textures")
