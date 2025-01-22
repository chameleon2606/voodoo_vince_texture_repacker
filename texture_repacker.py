import struct
import os
from binascii import hexlify
from importlib.metadata import files
from tkinter import filedialog as fd


output_path = os.getcwd()
textures_path = output_path+"/textures/"
lines = [line.strip() for line in open('funnynumbers.txt', 'r')]
os.chdir(textures_path)
textures = sorted(os.listdir(textures_path))


if not os.path.exists(textures_path):
    print("textures folder doesn't exist")
    exit()


def construct_header():
    header_magic = b'HOT '
    header = header_magic
    header += b'\x01\x00\x00\x00'
    header += (36 + ((32 * len(textures)) - 8) + len(filename_table)).to_bytes(4, byteorder='little')  # headers offset
    header += (36 + ((32 * len(textures)) - 8) + len(filename_table) + (128*len(textures))).to_bytes(4, byteorder='little')  # data offset
    return header + 20*b'\x00'


def construct_filemetadata():
    fileinfo_table = b''
    dynamic_offset = 0
    funny_number = 16
    i = 0
    header_size = 128
    headers_offset = 36 + ((32 * len(textures)) - 8) + len(filename_table)
    data_offset = headers_offset + (128*len(textures))
    padding = -data_offset % 16
    if padding == 0:
        padding = 16
    padding = 96
    data_offset += padding
    # print(data_offset)
    for texture in textures:
        fileinfo_table += header_size.to_bytes(4, byteorder='little')  # header size
        fileinfo_table += (headers_offset + (header_size * i)).to_bytes(4, byteorder='little')  # header offset
        fileinfo_table += os.path.getsize(texture).to_bytes(4, byteorder='little')  # file size
        fileinfo_table += b'\x00\x00\x00\x00'  # blank
        fileinfo_table += (data_offset + dynamic_offset).to_bytes(4, byteorder='little')  # file offset
        fileinfo_table += b'\x00\x00\x00\x00'  # blank
        if i < len(textures)-1:
            # fileinfo_table += funny_number.to_bytes(4, byteorder='little')
            fileinfo_table += int(lines[i]).to_bytes(4, byteorder='little')
            fileinfo_table += b'\x00\x00\x00\x00'  # blank
            # funny_number += 20  # increase funny number
            dynamic_offset += (os.path.getsize(texture)-header_size+16)
            i += 1
    return fileinfo_table


def construct_filenames():
    file_name_table = b''

    for texture in textures:
        texturename_byte_remainder = -len(bytes(texture, "utf-8")) % 4
        if texturename_byte_remainder == 0:
            byte_padding = 4
        else:
            byte_padding = texturename_byte_remainder
        file_name_table += bytes(texture, "utf-8")+(b'\x00'*byte_padding)

    return file_name_table


def construct_file_headers():
    header_size = 128
    file_header_table = b''
    i = 0
    for texture in textures:
        with open(textures_path+texture, "rb") as file:
            file_header_table += file.read(header_size)
            i += 1
    return file_header_table


def construct_raw_data():
    byte_padding = 16*b'\x00'
    raw_data = byte_padding*6
    for texture in textures:
        with open(textures_path+texture, "rb") as file:
            file.seek(128)
            raw_data += file.read()
            raw_data += byte_padding

    return raw_data


with open(output_path+"/textures_new.hot/", "w+b") as t:
    filename_table = construct_filenames()
    header = construct_header()
    t.write(header)  # writes header
    filemetadata = construct_filemetadata()
    t.write(filemetadata)  # writes file info tables
    # t.seek(-8, 1)  # last fileinfo is short of 8 bytes
    t.write(filename_table)  # writes filenames table
    fileheaders = construct_file_headers()
    t.write(fileheaders)  # writes fileinfo table
    raw_data = construct_raw_data()
    t.write(raw_data)

    # totalsize = len(header+filemetadata+filename_table+fileheaders+raw_data)-8
    totalsize = len(header+filemetadata+filename_table+fileheaders+raw_data)
    print(totalsize)
    t.seek(16)
    t.write(totalsize.to_bytes(4, byteorder='little'))

    # filenametableoffset = (header+filemetadata)-8
    t.seek(20)
    # t.write((len(header+filemetadata)-8).to_bytes(4, byteorder='little'))
    t.write((len(header+filemetadata)).to_bytes(4, byteorder='little'))

    t.seek(24)
    t.write(len(textures).to_bytes(4, byteorder='little'))
