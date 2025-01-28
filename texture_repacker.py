import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox, Image, PhotoImage
from tkinter.ttk import Progressbar
from math import ceil

# todo file validation
# todo specific error messages

output_path = ""
textures_path = os.getcwd() + "/textures/"
sounds_path = os.getcwd() + "/sounds/"
source_files_path = textures_path
localpath = os.getcwd()
level_file_list = []
data_index = []
current_level = ""
filename_table = ""
filemetadata = b''
file_headers_size = 0
raw_data_size = 0
mystery_numbers = "mystery_dds_numbers"

hot_header_size = 36
metadata_size = 32
dds_header_size = 128
wav_header_size = 72
current_header_size = 0


def convert_wav(wav_file):
    with open(source_files_path + wav_file, "rb+") as w:
        w.seek(20)
        if not w.read(1) == b'\x01':  # if not PCM
            exit()
        w.seek(64)
        if w.read(4) == b'data':
            return
        else:
            w.seek(0)
            start_of_file = w.read(36)
            rest_of_file = w.read(os.path.getsize(source_files_path + wav_file) - w.tell())
            padding_text = b'PAAD\x14\x00\x00\x00' + (20 * b'\x00')
            with open(source_files_path + wav_file, "w+b") as new:
                new.write(start_of_file + padding_text + rest_of_file)


def get_output_dir():
    global output_path
    output_path = filedialog.askdirectory()
    if not os.path.exists(output_path + '/vincedata/'):
        messagebox.showwarning("Error", "Invalid folder")
        return
    else:
        pack_button["state"] = tk.ACTIVE
    output_path += "/vincedata/"
    pathtext.config(text=output_path)
    root.update()


def get_level_data(data):
    with open(localpath + '/level_data.json') as f:
        level_data = json.load(f)
        if level_data[current_level][data]:
            return level_data[current_level][data]
        else:
            pathtext.config(text=data + " does not exist")
            exit()


def get_level_list():
    with open(localpath + '/level_data.json') as f:
        return json.load(f).keys()


def construct_header():
    header = b'HOT \x01\x00\x00\x00'
    header += (hot_header_size + len(filemetadata) + len(filename_table)).to_bytes(4, byteorder='little')
    header += (hot_header_size + ((metadata_size * len(level_file_list)) - 8) + len(filename_table) + (
                dds_header_size * len(level_file_list))).to_bytes(4, byteorder='little')  # data offset
    header += (hot_header_size + len(filemetadata) + len(filename_table) + file_headers_size + raw_data_size).to_bytes(
        4, byteorder='little')  # total size
    header += (hot_header_size + len(filemetadata)).to_bytes(4,
                                                             byteorder='little')  # writes the offset of the filename table
    header += (len(level_file_list).to_bytes(4, byteorder='little'))  # writes the amount of textures or sounds
    return header


def construct_filemetadata():
    mystery_number_array = get_level_data(mystery_numbers)
    fileinfo_table = b''
    i = 0
    headers_offset = hot_header_size + ((metadata_size * len(level_file_list)) - 8) + len(filename_table)
    data_offset = headers_offset + (dds_header_size * len(level_file_list))

    for file in level_file_list:
        if file.startswith('lightmap'):
            path = source_files_path + 'lightmaps/' + current_level + '/'
        else:
            path = source_files_path
        fileinfo_table += dds_header_size.to_bytes(4, byteorder='little')  # header size
        fileinfo_table += (headers_offset + (dds_header_size * i)).to_bytes(4, byteorder='little')  # header offset
        fileinfo_table += os.path.getsize(path + file).to_bytes(4, byteorder='little')  # file size
        fileinfo_table += b'\x00\x00\x00\x00'  # blank
        fileinfo_table += (data_offset + data_index[i]).to_bytes(4, byteorder='little')  # file offset
        fileinfo_table += b'\x00\x00\x00\x00'  # blank
        if i < len(level_file_list) - 1:
            fileinfo_table += int(mystery_number_array[i]).to_bytes(4, byteorder='little')  # unknown number
            fileinfo_table += b'\x00\x00\x00\x00'  # blank
            i += 1
    return fileinfo_table


def construct_filenames():
    file_name_table = b''

    for file in level_file_list:
        filename_byte_remainder = -len(bytes(file, "utf-8")) % 4
        if filename_byte_remainder == 0:
            byte_padding = 4
        else:
            byte_padding = filename_byte_remainder
        file_name_table += bytes(file, "utf-8") + (b'\x00' * byte_padding)

    offset = hot_header_size + ((metadata_size * len(level_file_list)) - 8) + len(file_name_table)
    file_name_table += b'\x00' * ((ceil(offset / 128) * 128) - offset)
    return file_name_table


def construct_file_headers():
    file_header_table = b''
    i = 0
    for file in level_file_list:
        if file.startswith('lightmap'):
            path = source_files_path + 'lightmaps/' + current_level + '/'
        else:
            path = source_files_path
        with open(path + file, "rb") as src_file:
            file_header_table += src_file.read(dds_header_size)
            i += 1

    offset = len(file_header_table)
    file_header_table += b'\x00' * ((ceil(offset / 128) * 128) - offset)
    return file_header_table


def construct_raw_data():
    raw_data = b''
    fileprogress.config(maximum=len(level_file_list))
    fileprogress['value'] = 0
    for file in level_file_list:
        current_file_text.config(text=file)  # shows what texture or sound is being processed
        root.update()
        if file.startswith('lightmap'):
            src_file_path = source_files_path + 'lightmaps/' + current_level + '/' + file
        else:
            src_file_path = source_files_path + file
        with open(src_file_path, "rb") as src_file:
            src_file.seek(dds_header_size)
            data_index.append(len(raw_data))
            raw_data += src_file.read()
            offset = len(raw_data)
            raw_data += b'\x00' * ((ceil(offset / 128) * 128) - offset)
        fileprogress['value'] += 1
    return raw_data


def selection_changed():
    global current_header_size
    global source_files_path
    global mystery_numbers
    if radio_buttons.get() == 'textures':
        current_header_size = dds_header_size
        source_files_path = textures_path
        mystery_numbers = 'mystery_dds_numbers'
    else:
        current_header_size = wav_header_size
        source_files_path = sounds_path
        mystery_numbers = 'mystery_wav_numbers'


def pack_files():
    global current_level
    global level_file_list
    global filename_table
    global filemetadata
    global file_headers_size
    global raw_data_size

    pack_button['state'] = tk.DISABLED
    path_button['state'] = tk.DISABLED
    r1['state'] = tk.DISABLED
    r2['state'] = tk.DISABLED
    levelprogress.config(maximum=get_level_list().__len__())

    if not os.path.exists(textures_path) and radio_buttons.get() == 'textures':
        messagebox.showwarning("Error", "Textures folder not found!")
        return
    if not os.path.exists(sounds_path) and radio_buttons.get() == 'sounds':
        messagebox.showwarning("Error", "Sounds folder not found!")
        return

    for area in get_level_list():
        if radio_buttons.get() == 'textures':
            if not area.startswith('area'):
                continue
        current_level = area

        leveltext.config(text=area)
        root.update()

        # if not os.path.exists(output_path+get_level_data('path')):
        #     os.makedirs(output_path+get_level_data('path'))

        with open(output_path + get_level_data('path') + radio_buttons.get() + ".hot", "w+b") as t:

            level_file_list.clear()
            data_index.clear()
            level_file_list = get_level_data(radio_buttons.get())

            if radio_buttons.get() == 'sounds':
                for file in level_file_list:
                    convert_wav(file)

            raw_data_bytes = construct_raw_data()
            raw_data_size = len(raw_data_bytes)
            filename_table = construct_filenames()
            t.write(b'\x00' * hot_header_size)  # placeholder for main header
            filemetadata = construct_filemetadata()
            t.write(filemetadata)  # writes file info tables
            t.write(filename_table)  # writes filenames table
            fileheaders = construct_file_headers()
            file_headers_size = len(fileheaders)
            t.write(fileheaders)  # writes fileinfo table
            t.write(raw_data_bytes)  # writes texture data

            header_bytes = construct_header()
            t.seek(0)
            t.write(header_bytes)  # writes header

            print(area + " " + radio_buttons.get() + " created with " + str(
                len(level_file_list)) + " " + radio_buttons.get())
            levelprogress['value'] += 1

    pack_button['state'] = tk.ACTIVE
    path_button['state'] = tk.ACTIVE
    r1['state'] = tk.ACTIVE
    r2['state'] = tk.ACTIVE
    levelprogress['value'] = 0
    fileprogress['value'] = 0
    leveltext.config(text="Done!")
    current_file_text.config(text="")
    root.update()


root = tk.Tk()
width = 400
height = 300
root.geometry(str(width) + "x" + str(height))
root.title("Chameleon's textures and sounds Repacker")
photo = PhotoImage(file=textures_path+"zgcvinceheadicon.png")
root.wm_iconphoto(False, photo)

path_button = tk.Button(root, text="choose game folder..", command=get_output_dir)
radio_buttons = tk.StringVar(value='textures')
r1 = tk.Radiobutton(root, text="Repack textures", variable=radio_buttons, value='textures', command=selection_changed)
r2 = tk.Radiobutton(root, text="Repack sounds", variable=radio_buttons, value='sounds', command=selection_changed)
pathtext = tk.Label(root, text=output_path)
pack_button = tk.Button(root, text="Repack", command=pack_files)
pack_button['state'] = tk.DISABLED
leveltext = tk.Label(root, text="")
current_file_text = tk.Label(root, text="")
levelprogress = Progressbar(root, orient=tk.HORIZONTAL, length=width / 2)
fileprogress = Progressbar(root, orient=tk.HORIZONTAL, length=width / 2)
spacer = tk.Label(root, text="")

if not os.path.exists(textures_path) and radio_buttons.get() == 'textures':
    pack_button['state'] = tk.DISABLED
    leveltext.config(text="Textures folder not found!")
if not os.path.exists(sounds_path) and radio_buttons.get() == 'sounds':
    pack_button['state'] = tk.DISABLED
    leveltext.config(text="Sounds folder not found!")

path_button.pack(pady=10)
r1.pack()
r2.pack()
pathtext.pack()
pack_button.pack(pady=10)
levelprogress.pack()
leveltext.pack()
spacer.pack()
fileprogress.pack()
current_file_text.pack()
root.mainloop()
