import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar

output_path = ""
textures_path = os.getcwd()+"/textures/"
localpath = os.getcwd()
os.chdir(textures_path)
all_textures = sorted(os.listdir(textures_path))
texture_list = []
current_level = ""
filename_table = ""

dds_header_size = 128

if not os.path.exists(textures_path):
    print("textures folder doesn't exist")
    exit()


def get_output_dir():
    global output_path
    output_path = filedialog.askdirectory()
    if not os.path.exists(output_path+'/vincedata/'):
        messagebox.showwarning("Error", "Invalid folder")
        return
    else:
        pack_button["state"] = tk.ACTIVE
    output_path += "/vincedata/"
    pathtext.config(text=output_path)
    root.update()


def get_level_data(data):
    with open(localpath+'/level_data.json') as f:
        level_data = json.load(f)
        return level_data[current_level][data]


def get_level_list():
    with open(localpath+'/level_data.json') as f:
        return json.load(f).keys()


def construct_header():
    header = b'HOT \x01\x00\x00\x00'
    header += (36 + ((32 * len(texture_list)) - 8) + len(filename_table)).to_bytes(4, byteorder='little')  # headers offset
    header += (36 + ((32 * len(texture_list)) - 8) + len(filename_table) + (128 * len(texture_list))).to_bytes(4, byteorder='little')  # data offset
    return header + 20*b'\x00'


def construct_filemetadata(header_bytes):
    mystery_number_array = get_level_data('mystery_numbers')
    fileinfo_table = b''
    dynamic_offset = 0
    i = 0
    metadata_size = 32
    headers_offset = len(header_bytes) + ((metadata_size * len(texture_list)) - 8) + len(filename_table)
    data_offset = headers_offset + (dds_header_size * len(texture_list)) + get_level_data('padding')

    for texture in texture_list:
        if texture.startswith('lightmap'):
            path = textures_path+'lightmaps/'+current_level+'/'
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
            path = textures_path+'lightmaps/'+current_level+'/'
        else:
            path = textures_path
        with open(path+texture, "rb") as file:
            file_header_table += file.read(dds_header_size)
            i += 1
    return file_header_table


def construct_raw_data(padding):
    texture_byte_padding = 16*b'\x00'
    raw_data = padding*b'\x00'
    textureprogress.config(maximum=len(texture_list))
    textureprogress['value'] = 0
    for texture in texture_list:
        texturedetail.config(text=texture)
        root.update()
        if texture.startswith('lightmap'):
            texturepath = textures_path+'lightmaps/'+current_level+'/'+texture
        else:
            texturepath = textures_path+texture
        with open(texturepath, "rb") as file:
            file.seek(128)
            raw_data += file.read()
            raw_data += texture_byte_padding
        textureprogress['value'] += 1

    return raw_data


def pack_textures():
    global current_level
    global texture_list
    global filename_table

    pack_button['state'] = tk.DISABLED
    path_button['state'] = tk.DISABLED
    levelprogress.config(maximum=get_level_list().__len__())

    if not os.path.exists(textures_path):
        messagebox.showwarning("Error", "Textures folder not found!")
        return

    for area in get_level_list():
        current_level = area

        leveltext.config(text=area)
        root.update()

        with open(output_path+get_level_data('path')+"textures.hot", "w+b") as t:
            texture_list.clear()
            texture_list = get_level_data('textures')

            filename_table = construct_filenames()
            header_bytes = construct_header()
            t.write(header_bytes)  # writes header
            filemetadata = construct_filemetadata(header_bytes)
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
            levelprogress['value'] += 1

    pack_button['state'] = tk.ACTIVE
    path_button['state'] = tk.ACTIVE
    levelprogress['value'] = 0
    textureprogress['value'] = 0
    leveltext.config(text="Done!")
    texturedetail.config(text="")
    root.update()

root = tk.Tk()
width = 400
height = 220
root.geometry(str(width)+"x"+str(height))
root.title("Chameleon's Texture Repacker")

path_button = tk.Button(root, text="choose game folder..", command=get_output_dir)
pathtext = tk.Label(root, text=output_path)
pack_button = tk.Button(root, text="Repack", command=pack_textures)
pack_button['state'] = tk.DISABLED
leveltext = tk.Label(root, text="")
texturedetail = tk.Label(root, text="")
levelprogress = Progressbar(root, orient=tk.HORIZONTAL, length=width/2)
textureprogress = Progressbar(root, orient=tk.HORIZONTAL, length=width/2)
spacer = tk.Label(root, text="")


path_button.pack(pady=10)
pathtext.pack()
pack_button.pack(pady=10)
levelprogress.pack()
leveltext.pack()
spacer.pack()
textureprogress.pack()
texturedetail.pack()
root.mainloop()
