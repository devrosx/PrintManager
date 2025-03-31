#!/usr/local/opt/python@3.13/bin/python3.13
import sys
import os
import fnmatch
import plistlib
import subprocess
import time
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPalette, QColor, QIcon, QPixmap
from PyQt6.QtCore import QThread, pyqtSignal, QSettings
# test threads
from unidecode import unidecode

from libs.colordetector import *
from libs.crop_module import processFile
from libs.pdf_preview_module import pdf_preview_generator
from libs.image_grabber_module import *
from libs.remove_cropmarks_module import *
from libs.gui_crop2 import *

# SMART CROP - BROKEN 
version = '0.6'
# -fixed preferences
# -rewrited preferences to QSettings
# -new debug options
# -support locked pdf (unlock on open)

start_time = time.time()
info, name, size, extension, file_size, pages, price, colors, filepath = [[] for _ in range(9)]
mm = '0.3527777778'
office_ext = ['csv', 'db', 'odt', 'doc', 'gif', 'pcx', 'docx', 'dotx', 'fodp', 'fods', 'fodt', 'odb', 'odf', 'odg', 'odm', 'odp', 'ods', 'otg', 'otp', 'ots', 'ott', 'oxt', 'pptx', 'psw', 'sda', 'sdc', 'sdd', 'sdp', 'sdw', 'slk', 'smf', 'stc', 'std', 'sti', 'stw', 'sxc', 'sxg', 'sxi', 'sxm', 'sxw', 'uof', 'uop', 'uos', 'uot', 'vsd', 'vsdx', 'wdb', 'wps', 'wri', 'xls', 'xlsx', 'ppt', 'cdr']
image_ext = ['jpg', 'jpeg', 'png', 'tif', 'bmp']
next_ext = ['pdf', 'dat']
user_path = os.path.expanduser("~")
# other os support
system = str(sys.platform)
os.environ['PATH'] += ':/usr/bin:/usr/local/bin'
# default values
user_path = Path.home()

# PRESET STUFF
def get_custom_presets_files():
    """Získání cesty k souborům s předvolbami tiskáren."""
    prefs_dir = os.path.expanduser('~/Library/Preferences/')
    pattern = 'com.apple.print.custompresets*'
    return [os.path.join(prefs_dir, filename) for filename in os.listdir(prefs_dir) if fnmatch.fnmatch(filename, pattern)]

def clean_presets_names(presets, preset_names):
    """Vytvoření slovníku s cestami k presetům a jejich názvy."""
    printer_presets_dict = {}
    for preset, names in zip(presets, preset_names):
        cleaned_path = os.path.basename(preset)  # Získání názvu souboru bez cesty
        if cleaned_path not in printer_presets_dict:
            printer_presets_dict[cleaned_path] = []
        # Přidání všech názvů do seznamu pro danou cestu
        printer_presets_dict[cleaned_path].extend(names)
    return printer_presets_dict

def read_preset_names_from_plist(plist_file):
    """Načtení názvů presetů z plist souboru."""
    try:
        with open(plist_file, 'rb') as f:
            plist_data = plistlib.load(f)
            # Vytvoření seznamu názvů presetů
            return [preset.get('PresetName') for preset in plist_data.get('com.apple.print.customPresetsInfo', []) if preset.get('PresetName')]
    except Exception as e:
        print(f"Nastala chyba při čtení souboru {plist_file}: {e}")
        return []

def get_printer_presets():
    """Hlavní funkce pro zpracování předvoleb tiskáren a vrátí slovník s předvolbami."""
    presets_files = get_custom_presets_files()
    all_printer_presets_dict = {}

    for preset_file in presets_files:
        preset_names = read_preset_names_from_plist(preset_file)
        cleaned_path = os.path.basename(preset_file)  # Získání názvu souboru bez cesty
        if preset_names:
            # Pokud je více názvů presetů, přidáme je do slovníku
            if cleaned_path not in all_printer_presets_dict:
                all_printer_presets_dict[cleaned_path] = []
            all_printer_presets_dict[cleaned_path].extend(preset_names)  # Přidání všech názvů presetů
        else:
            all_printer_presets_dict[cleaned_path] = []
    return all_printer_presets_dict  # Vrátí slovník s předvolbami

def is_arch_check():
    if system == 'darwin':
        sys_support = 'supported'
    else:
        sys_support = 'not supported'

def is_cups_running():
    try:
        subprocess.check_output(["pgrep", "-x", "cupsd"], stderr=subprocess.DEVNULL)
        return 1  # CUPS je spuštěn
    except subprocess.CalledProcessError:
        return 0  # CUPS není spuštěn

def load_printers():
    output = (subprocess.check_output(["lpstat", "-a"]))
    outputlist = (output.splitlines())
    tolist = []  # novy list
    for num in outputlist:  # prochazeni listem
        first, *middle, last = num.split()
        tiskarna = str(first.decode())
        tolist.append(tiskarna)
    return (tolist)

def handle_exception(e):
    if isinstance(e, FileNotFoundError):
        self.d_writer(f"Chyba: Soubor nebyl nalezen: {str(e)}", 1, 'red')
    else:
        self.d_writer(f"Nastala neočekávaná chyba: {str(e)}", 1, 'red')
    self.d_writer(warning_message, 1, 'red')

def fix_filename(item, _format=None, app=None):
    oldfilename = os.path.basename(item)
    dirname = os.path.dirname(item) + '/'
    
    if _format is not None:
        newfilename = _format + oldfilename
    else:
        newfilename = unidecode(oldfilename)
    
    # Kontrola, zda máme oprávnění k zápisu do souboru
    old_file_path = os.path.join(dirname, oldfilename)
    new_file_path = os.path.join(dirname, newfilename)

    # Zkontrolujeme, zda je soubor otevřený nebo zda máme oprávnění
    if not os.access(dirname, os.W_OK):
        self.d_writer("Není povolen zápis do adresáře.", 1, 'red')
        return None
    try:
        with open(old_file_path, 'a'):
            pass
    except IOError:
        self.d_writer("Není povolen zápis do souboru.", 1, 'red')
        return None
    try:
        # Pokusíme se přejmenovat soubor
        os.rename(old_file_path, new_file_path)
    except PermissionError:
        self.d_writer("Není povolen zápis do souboru.", 1, 'red')
        return None

    return new_file_path

def humansize(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{round(size)} {unit}"
        size /= 1024
    return f"{round(size)} GB"

def open_printer(file):
    file_path = '/private/etc/cups/ppd/' + file + '.ppd'
    if os.path.exists(file_path):
        print(['open', '-t', file_path])
        # Použijte plnou cestu k příkazu open
        subprocess.run(['open', '-t', file_path])
    else:
        print(f"Soubor {file_path} neexistuje.")

def revealfile(list_path, reveal):  # reveal and convert
    if isinstance(list_path, list):
        for items in list_path:
            subprocess.call(['open', reveal, items])
    else:
        subprocess.call(['open', reveal, list_path])

def previewimage(original_file):
    command = ["qlmanage", "-p", original_file]
    subprocess.run(command)
    return command

def add_suffix_to_filename(file_path: str, suffix: str) -> str:
    """Přidá suffix do názvu souboru před jeho příponu."""
    path = Path(file_path)  # Vytvoření objektu Path
    new_filename = f"{path}_{suffix}{path.suffix}"  # Přidání suffixu k názvu souboru
    return new_filename

def mergefiles(list_path, save_dir):
    """Spojí PDF soubory do jednoho PDF souboru."""
    base = Path(list_path[0])
    outputfile = add_suffix_to_filename(base, "m")
    writer = PdfWriter()
    for pdf in list_path:
        with open(pdf, 'rb') as f:
            reader = PdfReader(f)
            writer.append(reader)
    with open(outputfile, 'wb') as f:
        writer.write(f)
    return outputfile

def splitfiles(file):
    outputfiles = []
    with open(file, 'rb') as pdf_file:  # Oprava: použití with pro správu souborů
        pdf_reader = PdfReader(pdf_file)
        pageNumbers = len(pdf_reader.pages)
        outputfile = add_suffix_to_filename(file, "s")
        for i in range(pageNumbers):
            pdf_writer = PdfWriter()
            pdf_writer.add_page(pdf_reader.pages[i])
            outputpaths = outputfile + str(i + 1) + '.pdf'
            with open(outputpaths, 'wb') as split_motive:
                pdf_writer.write(split_motive)
            outputfiles.append(outputpaths)
    return outputfiles

def resize_this_image(original_file, percent):
    outputfiles = []
    for item in original_file:
        head, ext = os.path.splitext(item)
        outputfile = head + '_' + str(percent) + ext
        command = ["magick", item, "-resize", str(percent) + '%', outputfile]
        subprocess.run(command)
        outputfiles.append(outputfile)
    return command, outputfiles

def crop_image(original_file, coordinates):
    command = ["magick", original_file, "-crop", str(coordinates[2] - coordinates[0]) + 'x' + str(coordinates[3] - coordinates[1]) + '+' + str(coordinates[0]) + '+' + str(coordinates[1]), original_file]
    print(command)
    subprocess.run(command)
    return command

def pdf_cropper_x(pdf_input, coordinates, pages):
    print(coordinates)
    pdf = PdfReader(open(pdf_input, 'rb'))
    outPdf = PdfWriter()
    for i in range(pages):
        page = pdf.pages[i]
        page.mediabox.upper_left = (coordinates[0], int(page.trimbox[3]) - coordinates[1])
        page.mediabox.lower_right = (coordinates[2], int(page.trimbox[3]) - coordinates[3])
        page.trimbox.upper_left = (coordinates[0], int(page.trimbox[3]) - coordinates[1])
        page.trimbox.lower_right = (coordinates[2], int(page.trimbox[3]) - coordinates[3])
        outPdf.add_page(page)
    with open(pdf_input + '_temp', 'wb') as outStream:
        outPdf.write(outStream)
    os.rename(pdf_input + '_temp', pdf_input)

def rotate_this_image(original_file, angle):
    outputfiles = []
    for item in original_file:
        head, ext = os.path.splitext(item)
        outputfile = head + ext
        command = ["magick", item, "-rotate", str(angle), outputfile]
        subprocess.run(command)
        outputfiles.append(outputfile)
    return command, outputfiles

def invert_this_image(original_file):
    outputfiles = []
    for item in original_file:
        head, ext = os.path.splitext(item)
        outputfile = head + ext
        command = ["magick", item, "-channel", "RGB", "-negate", outputfile]
        subprocess.run(command)
        outputfiles.append(outputfile)
    return command, outputfiles

def gray_this_file(original_file, filetype):
    outputfiles = []
    for item in original_file:
        head, ext = os.path.splitext(item)
        outputfile = head + '_gray' + ext
        if filetype == 'pdf':
            command = ["gs", "-sDEVICE=pdfwrite", "-dProcessColorModel=/DeviceGray", "-dColorConversionStrategy=/Gray", "-dPDFUseOldCMS=false", "-dNOPAUSE", "-dQUIET", "-dBATCH", "-sOutputFile=" + outputfile, item]
        else:
            command = ["magick", item, "-colorspace", "Gray", outputfile]
        subprocess.run(command)
        outputfiles.append(outputfile)
    return command, outputfiles

def compres_this_file(original_file, *args):
    outputfiles = []
    for item in original_file:
        head, ext = os.path.splitext(item)
        outputfile = head + '_c' + ext
        command = ["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4", "-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dQUIET", "-dBATCH", "-sOutputFile=" + outputfile, item]
        subprocess.run(command)
        outputfiles.append(outputfile)
    return command, outputfiles

def raster_this_file(original_file, *args):
    outputfiles = []
    for item in original_file:
        head, ext = os.path.splitext(item)
        outputfile = head + '_raster' + ext
        command_gs = ["gs", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dNOCACHE", "-sDEVICE=pdfwrite", "-sColorConversionStrategy=/LeaveColorUnchanged", "-dAutoFilterColorImages=true", "-dAutoFilterGrayImages=true", "-dDownsampleMonoImages=true", "-dDownsampleGrayImages=true", "-dDownsampleColorImages=true", "-sOutputFile=" + outputfile, original_file]
        command = ["magick", "-density", str(resolution), "+antialias", str(item), str(outputfile)]
        subprocess.run(command)
        outputfiles.append(outputfile)
    return command, outputfiles

def flaten_transpare_pdf(original_file, *args):
    outputfiles = []
    for item in original_file:
        head, ext = os.path.splitext(item)
        outputfile = head + '_fl' + ext
        command_gs = ["gs", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dNOCACHE", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.3", "-sOutputFile=" + outputfile, item]
        subprocess.run(command_gs)
        outputfiles.append(outputfile)
    return command_gs, outputfiles

def fix_this_file(original_file, *args):
    outputfiles = []
    for item in original_file:
        head, ext = os.path.splitext(item)
        outputfile = head + '_fixed' + ext
        command_gs = ["gs", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dNOCACHE", "-sDEVICE=pdfwrite", "-dPDFSETTINGS=/prepress", "-sOutputFile=" + outputfile, item]
        subprocess.run(command_gs)
        outputfiles.append(outputfile)
    return command_gs, outputfiles

def convert_this_file(original_file, *args):
    outputfiles = []
    for item in original_file:
        head, ext = os.path.splitext(item)
        outputfile = head + '.pdf'
        command = ["magick", str(resolution), '-density', '300', str(item), str(outputfile)]
        subprocess.run(command)
        outputfiles.append(outputfile)
    return command, outputfiles


def smart_stitch_this_file(original_file, *args):
    outputfiles = []
    head, ext = os.path.splitext(original_file[0])
    outputfile = head +'_stitched' + '.jpg'
    script_directory = os.path.dirname(os.path.abspath(__file__))
    python_path = sys.executable
    command = [
    python_path,
    script_directory + '/libs/stitcher.py',
    '--mode', '1',
    *original_file,  # Přidá všechny prvky original_file jako samostatné argumenty
    '--output', outputfile]
    print (command)
    subprocess.run(command)
    outputfiles.append(outputfile)
    return command, outputfiles

def smart_stitch_this_file_adv(original_file, *args):
    outputfiles = []
    head, ext = os.path.splitext(original_file[0])
    outputfile = head +'_stitched' + '.jpg'
    script_directory = os.path.dirname(os.path.abspath(__file__))
    python_path = sys.executable
    command = [
    python_path,
    script_directory + '/libs/stitcher_detailed.py', *original_file,
    '--match_conf', '0.2',
    '--conf_thresh', '0.2',
    '--features', 'sift',
    ] 
        # '--warp', 'affine'

    print (command)
    subprocess.run(command)
    outputfiles.append(outputfile)
    return command, outputfiles


def smart_cut_this_file(original_file, *args):
    smartcut_files = []
    outputfiles = []
    dialog = InputDialog_SmartCut()
    if dialog.exec():
        n_images, tresh = dialog.getInputs()
        for items in original_file:
            outputfiles = processFile(items, n_images, tresh)
            smartcut_files.append(outputfiles)
        # merge lists inside lists 
        smartcut_files = [j for i in smartcut_files for j in i]
        command = 'OK'
    else:
        dialog.close()
    return command, smartcut_files

def get_boxes(input_file):
    pdf_reader = PdfReader(input_file)
    page = pdf_reader.pages[0]
    pageNumbers = len(pdf_reader.pages)
    return pageNumbers

def find_fonts(obj, fnt):
    if '/BaseFont' in obj:
        fnt.add(obj['/BaseFont'])
    for k in obj:
        if hasattr(obj[k], 'keys'):
            find_fonts(obj[k], fnt)
    return fnt

def get_fonts(pdf_input):
    font_ = []
    fonts = set()
    for page in pdf_input.pages:
        obj = page.getObject()
        f = find_fonts(obj['/Resources'], fonts)
    for items in f:
        head, sep, tail = items.partition('+')
        font_.append(tail)
    return font_

def file_info_new(inputs, file, *args):
    _info = []
    if file == 'pdf':
        for item in inputs:
            pdf_toread = PdfReader(open(item, "rb"))
            pdf_ = pdf_toread.metadata
            pdf_fixed = {key.strip('/'): item.strip() for key, item in pdf_.items()}
            pdf_fixed.update({'Filesize': humansize(os.path.getsize(item))})
            pdf_fixed.update({'Pages': str(len(pdf_toread.pages))})
            pdf_fixed.update({'MediaBox': get_pdf_size(pdf_toread.pages[0].mediabox)})
            pdf_fixed.update({'CropBox': get_pdf_size(pdf_toread.pages[0].cropbox)})
            pdf_fixed.update({'TrimBox': get_pdf_size(pdf_toread.pages[0].trimbox)})
            # pdf_fixed.update({'Fonts': "\n".join(get_fonts(pdf_toread))})
            html_info = tablemaker(pdf_fixed)
            _info.append(html_info)
    else:
        name_ = []
        val_ = []
        for item in inputs:
            output = (subprocess.check_output(["mdls", item]))
            pdf_info = (output.splitlines())
            name_.append('Filesize')
            val_.append(humansize(os.path.getsize(item)))
            for num in pdf_info:
                num = num.decode("utf-8")
                name, *value = num.split('=')
                value = ', '.join(value)
                name = name.rstrip()
                value = value.replace('"', '')
                value = value.lstrip()
                name = name.replace('kMD', '')
                name = name.replace('FS', '')
                name = name[:24] + (name[24:] and '..')
                name_.append(name)
                val_.append(value)
        tolist = dict(zip(name_, val_))
        unwanted = ['', [], '(', '0', '(null)']
        img_ = {k: v for k, v in tolist.items() if v not in unwanted}
        _info = tablemaker(img_)
    return _info

def tablemaker(inputs):
    html = "<table width=100% table cellspacing=0 style='border-collapse: collapse' border = \"0\" >"
    html += '<style>table, td, th {font-size: 9px;border: none;padding-left: 2px;padding-right: 2px;ppadding-bottom: 4px;}</style>'
    # fix this
    inputs = {k.replace(u'D:', ' '): v.replace(u'D:', ' ') for k, v in inputs.items()}
    inputs = {k.replace(u"+01'00'", ' '): v.replace(u"+01'00'", ' ') for k, v in inputs.items()}
    inputs = {k.replace(u" +0000", ' '): v.replace(u" +0000", ' ') for k, v in inputs.items()}
    inputs = {k.replace(u"Item", ' '): v.replace(u"Item", ' ') for k, v in inputs.items()}
    inputs = {k.replace(u" 00:00:00", ' '): v.replace(u" 00:00:00", ' ') for k, v in inputs.items()}
    for dict_item in inputs:
        html += '<tr>'
        key_values = dict_item.split(',')
        html += '<th><p style="text-align:right;color: #7e7e7e;">' + str(key_values[0]) + '</p></th>'
        html += '<th><p style="text-align:left;font-weight: normal">' + inputs[dict_item] + '</p></th>'
        html += '</tr>'
    html += '</table>'
    return html

def print_this_file(self, outputfiles, tiskarna_ok, lp_two_sided, orientation, copies, fit_to_size, collate, colors, printer_presets):
    # https://www.cups.org/doc/options.html
    # COLATE
    print (printer_presets)
    if printer_presets == "Default Setting":
        p_presets = ''
    else:
        p_presets = ('-o preset="' + printer_presets +  '"')
    if collate == 1:
        collate = ('-o collate=true')
    else: 
        collate = ('')
    # COLORS 
    if colors == 'Auto':
        colors = ('')
    if colors == 'Color':
        colors = ('-o ColorMode=Color')
    if colors == 'Gray':
        colors = ('-o ColorMode=GrayScale')
    # PAPER SHRINK
    if fit_to_size == 1:
        fit_to_size = ('-o fit-to-page')
    else: 
        fit_to_size = ('')
    # na canonu nefunguje pocet kopii... vyhodit -o sides=one-sided
    if lp_two_sided == 1:
        lp_two_sided_ = ('-o sides=two-sided')
        if orientation == 1:
            lp_two_sided_ = ('-o sides=two-sided-long-edge')
        else:
            lp_two_sided_ = ('-o sides=two-sided-short-edge')
    else:
        lp_two_sided_ = ('-o sides=one-sided')
    for printitems in outputfiles:
        command = ["lp", "-d", tiskarna_ok, printitems, "-n" + copies, p_presets, lp_two_sided_, fit_to_size, collate, colors]
        # remove blank strings
        command = [x for x in command if x]
        subprocess.run(command)
    try:
        subprocess.run(["/usr/bin/open", user_path + "/Library/Printers/" + str(tiskarna_ok) + ".app"])
    except:
        print('printer not found')
        self.d_writer('Printer not found', 0, 'red')
    return command

def get_pdf_size(pdf_input):
    qsizedoc = (pdf_input)
    width = (float(qsizedoc[2]) * float(mm))
    height = (float(qsizedoc[3]) * float(mm))
    page_size = (str(round(width)) + 'x' + str(round(height)) + ' mm')
    return page_size

def getimageinfo(filename):
    try:
        output = (subprocess.check_output(["identify", '-format', '%wx%hpx %m', filename]))
        outputlist = (output.splitlines())
        getimageinfo = []
        for num in outputlist:  # prochazeni listem
            first, middle = num.split()
            getimageinfo.append(str(first.decode()))
            getimageinfo.append(str(middle.decode()))
        error = 0
    except Exception as e:
        error = str(e)
        getimageinfo = 0
    return getimageinfo, error

def append_blankpage(inputs, *args):
    outputfiles = []
    if isinstance(inputs, str):  # Použijte isinstance pro kontrolu typu
        inputs = [inputs]
    for item in inputs:
        with open(item, 'rb') as input_file:
            pdf = PdfReader(input_file)
            numPages = len(pdf.pages)  # Získání počtu stránek pomocí len(pdf.pages)
            if numPages % 2 == 1:
                print('licha')
                outPdf = PdfWriter()  # Použijte PdfWriter
                # Přidejte všechny stránky jednu po druhé
                for page_number in range(numPages):
                    page = pdf.pages[page_number]  # Získání stránky pomocí indexu
                    outPdf.add_page(page)  # Přidání jednotlivé stránky
                outPdf.add_blank_page()  # Přidejte prázdnou stránku
                outStream = open(item + '_temp', 'wb')
                outPdf.write(outStream)
                outStream.close()
                os.rename(item + '_temp', item)
            else:
                print('suda all ok')
    command = ['ok']
    return command, outputfiles

def pdf_parse(self, inputs, *args):
    rows = []
    if isinstance(inputs, str):
        inputs = [inputs]
        print(inputs)
    
    for item in inputs:
        print(item)
        oldfilename = os.path.basename(item)
        ext_file = os.path.splitext(oldfilename)
        dirname = os.path.dirname(item) + '/'
        try:
            with open(item, mode='rb') as f:
                pdf_input = PdfReader(f, strict=False)
                
                if pdf_input.is_encrypted:
                    print(f"{oldfilename} is encrypted.")
                    try:
                        pdf_input.decrypt('')
                    except Exception as e:
                        print(f"Cannot unlock PDF {oldfilename}: {e}")
                        continue
                
                # Opraveno na mediaBox
                page_size = get_pdf_size(pdf_input.pages[0].mediabox)
                pdf_pages = len(pdf_input.pages)
                velikost = size_check(page_size)
                print (velikost)
                
                name.append(ext_file[0])
                size.append(size_check(page_size))
                print (size)
                price.append(price_check(pdf_pages, velikost))
                file_size.append(humansize(os.path.getsize(item)))
                pages.append(int(pdf_pages))
                filepath.append(item)
                info.append('')
                colors.append('')
                extension.append(ext_file[1][1:].lower())
        
        except Exception as e:
            print(e)
            err = QMessageBox()
            err.setWindowTitle("Error")
            err.setIcon(QMessageBox.Icon.Critical)
            err.setText("Error")
            err.setInformativeText(str(e))
            err.exec()
            self.d_writer('Import error: ' + str(e), 1, 'red')
    
    merged_list = list(zip(info, name, size, extension, file_size, pages, price, colors, filepath))
    return merged_list

def pdf_update(self, inputs, index, *args):
    rows = []
    if isinstance(inputs, str):  # Použijte isinstance pro kontrolu typu
        inputs = [inputs]
    
    for item in inputs:
        oldfilename = os.path.basename(item)
        ext_file = os.path.splitext(oldfilename)
        dirname = os.path.dirname(item) + '/'
        
        with open(item, mode='rb') as f:
            pdf_input = PdfReader(f, strict=False)
            if pdf_input.is_encrypted:
                self.d_writer('File is encrypted...', 0, 'red')
                break  # Ukončete cyklus, pokud je soubor zašifrovaný
            else:
                try:
                    # Získání velikosti stránky a počtu stránek
                    page_size = get_pdf_size(pdf_input.pages[0].mediabox)  # Použijte pdf_input.pages[0]
                    pdf_pages = len(pdf_input.pages)  # Použijte len(pdf_input.pages)
                    velikost = size_check(page_size)
                    
                    # Aktualizace informací
                    name[index] = ext_file[0]
                    size[index] = size_check(page_size)
                    price[index] = price_check(pdf_pages, velikost)
                    file_size[index] = humansize(os.path.getsize(item))
                    pages[index] = int(pdf_pages)
                    filepath[index] = item
                    info[index] = ''
                    colors[index] = ''
                    extension[index] = ext_file[1][1:].lower()
                
                except Exception as e:
                    print(e)
                    err = QMessageBox()
                    err.setWindowTitle("Error")
                    err.setIcon(QMessageBox.Icon.Critical)
                    err.setText("Error")
                    err.setInformativeText(str(e))
                    err.exec()
                    self.d_writer('Import error:' + str(e), 1, 'red')
        f.close()
    
    merged_list = list(zip(info, name, size, extension, file_size, pages, price, colors, filepath))
    return merged_list

def img_parse(self, inputs, *args):
    rows = []
    for item in inputs:
        oldfilename = (os.path.basename(item))
        filesize = humansize(os.path.getsize(item))
        ext_file = os.path.splitext(oldfilename)
        dirname = (os.path.dirname(item) + '/')
        info.append('')
        image_info, error = getimageinfo(item)
        if image_info == 0:
            self.d_writer('Import file failed...', 0, 'red')
            self.d_writer(error, 1, 'white')
            break
        name.append(ext_file[0])
        size.append(str(image_info[0]))
        extension.append(ext_file[1][1:].lower())
        file_size.append(humansize(os.path.getsize(item)))
        pages.append(1)
        price.append('')
        colors.append(str(image_info[1]))
        filepath.append(item)
    
    merged_list = list(zip(info, name, size, extension, file_size, pages, price, colors, filepath))
    return merged_list

def update_img(self, inputs, index, *args):
    rows = []
    for item in inputs:
        oldfilename = (os.path.basename(item))
        filesize = humansize(os.path.getsize(item))
        ext_file = os.path.splitext(oldfilename)
        dirname = (os.path.dirname(item) + '/')
        info[index] = ('')
        image_info, error = getimageinfo(item)
        if image_info == 0:
            self.d_writer('Import file failed...', 0, 'red')
            self.d_writer(error, 1, 'white')
            break
        name[index] = ext_file[0]
        size[index] = str(image_info[0])
        extension[index] = ext_file[1][1:].lower()
        file_size[index] = humansize(os.path.getsize(item))
        pages[index] = 1
        price[index] = ''
        colors[index] = str(image_info[1])
        filepath[index] = item
    
    merged_list = list(zip(info, name, size, extension, file_size, pages, price, colors, filepath))
    return merged_list

def clear_table(self):
    """Vymaže všechny řádky v tabulce."""
    self.table.setRowCount(0)  # Nastaví počet řádků na 0

def remove_from_list(self, index, *args):
    del info[index]
    del name[index]
    del size[index]
    del extension[index]
    del file_size[index]
    del pages[index]
    del price[index]
    del colors[index]
    del filepath[index]
    merged_list = list(zip(info, name, size, extension, file_size, pages, price, colors, filepath))
    return merged_list

def size_check(page_size):
    velikost = 0
    if page_size == '210x297 mm':
        velikost = 'A4'
    elif page_size == '420x297 mm':
        velikost = 'A3'
    elif page_size == '105x148 mm':
        velikost = 'A6'
    elif page_size == '148x210 mm':
        velikost = 'A5'
    elif page_size == '420x594 mm':
        velikost = 'A2'
    elif page_size == '594x841 mm':
        velikost = 'A1'
    elif page_size == '841x1188 mm':
        velikost = 'A0'
    else:
        velikost = page_size
    return velikost

def price_check(pages, velikost):
    price = []
    if velikost == 'A4':
        if pages >= 50:
            pricesum = (str(pages * 2) + ' Kč')
        elif pages >= 20:
            pricesum = (str(pages * 2.5) + ' Kč')
        elif pages >= 0:
            pricesum = (str(pages * 3) + ' Kč')
    elif velikost == 'A3':
        if pages >= 50:
            pricesum = (str(pages * 4) + ' Kč')
        elif pages >= 20:
            pricesum = (str(pages * 4.8) + ' Kč')
        elif pages >= 0:
            pricesum = (str(pages * 6) + ' Kč')
    else:
        pricesum = '/'
    return pricesum

def darkmode():
    app.setStyle("Fusion")  # Use Fusion style for consistent cross-platform appearance

    # Create a dark palette
    palette = QPalette()

    # Set colors for the palette
    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))  # Background color for windows
    palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)  # Text color for windows
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))  # Background color for input widgets
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))  # Alternate background color for views
    palette.setColor(QPalette.ColorRole.ToolTipBase, Qt.GlobalColor.white)  # Background color for tooltips
    palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)  # Text color for tooltips
    palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)  # Text color for input widgets
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))  # Background color for buttons
    palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)  # Text color for buttons
    palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)  # Bright text color (e.g., for errors)
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))  # Color for hyperlinks
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))  # Color for selected items
    palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)  # Text color for selected items

    # Apply the palette to the application
    app.setPalette(palette)

    # Additional style sheet for better button appearance
    app.setStyleSheet('''
        QPushButton {
            color: #ffffff;
            background-color: #2c2c2c;
            border: 1px solid #444;
            padding: 5px;
            border-radius: 4px;
        }
        QPushButton:disabled {
            color: #696969;
            background-color: #272727;
            border: 1px solid #444;
        }
        QPushButton:hover {
            background-color: #3c3c3c;
        }
        QPushButton:pressed {
            background-color: #1c1c1c;
        }
    ''')

class TableWidgetDragRows(QTableWidget):
    openFileDialogRequested = pyqtSignal()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropOverwriteMode(False)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setSortingEnabled(True)

    def mousePressEvent(self, event):
        if self.rowCount() == 0:
            self.openFileDialogRequested.emit()
        else:
            super().mousePressEvent(event)

    def dragLeaveEvent(self, event):
        event.accept()

# for icons
class IconDelegate(QStyledItemDelegate):
    def initStyleOption(self, option: QStyleOptionViewItem, index):
        super().initStyleOption(option, index)
        if option.features & QStyleOptionViewItem.ViewItemFeature.HasDecoration:
            s = option.decorationSize
            s.setWidth(option.rect.width())
            option.decorationSize = s

class InputDialog_SmartCut(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.first = QSpinBox(self)
        self.first.setRange(1, 50)
        self.first.setValue(1)
        self.second = QSpinBox(self)
        self.second.setRange(1, 255)
        self.second.setValue(220)
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        layout = QFormLayout(self)
        layout.addRow("Number of images", self.first)
        layout.addRow("Treshold", self.second)
        layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return (self.first.value(), self.second.value())

    def getInputs(self):
        if self.imagetype.currentText() == "photo":
            self.image_type = 'p'
        else:
            self.image_type = 'a'
        return (self.image_type, self.scale.value(), self.denoise.value())  # Oprava: vrátí hodnoty jako int

class InputDialog_PDFcut(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.multipage = QCheckBox(self)
        self.multipage.setChecked(True)
        self.multipage.toggled.connect(self.hide)
        self.croppage_l = QLabel()
        self.croppage_l.setText("Page used as cropbox for all pages")
        self.croppage = QSpinBox(self)
        self.croppage.setRange(1, 1000)
        self.croppage.setValue(1)
        self.croppage.setVisible(False)
        self.croppage_l.setVisible(False)
        self.margin = QSpinBox(self)
        self.margin.setRange(-200, 200)
        # self.margin.setValue(1)
        buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.layout = QFormLayout(self)
        self.layout.addRow("Detect all pages cropboxes", self.multipage)
        self.layout.addRow(self.croppage_l, self.croppage)
        self.layout.addRow("Margin", self.margin)
        self.layout.addWidget(buttonBox)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

    def getInputs(self):
        return (self.multipage.isChecked(), self.croppage.value(), self.margin.value())

    def hide(self):
        if self.multipage.isChecked():
            self.croppage.setEnabled(False)
            self.croppage.setVisible(False)
            self.croppage_l.setVisible(False)
        else:
            self.croppage.setEnabled(True)
            self.croppage.setVisible(True)
            self.croppage_l.setVisible(True)

class PrefDialog(QDialog):
    def __init__(self, localization, resolution, convertor, ontop, parent=None):
        super().__init__(parent)
        self.setObjectName("Preferences")
        # Uložení předaných hodnot do instančních proměnných
        self.localization = localization
        self.resolution = resolution
        self.convertor = convertor
        self.ontop = ontop

        self.layout = QFormLayout(self)
        self.text_link = QLineEdit(self.localization)
        self.text_link.setMaxLength(3)
        # resolution raster
        self.res_box = QSpinBox(self)
        self.res_box.setRange(50, 1200)
        self.res_box.setValue(self.resolution)
        # file parser
        self.btn_convertor = QComboBox(self)
        self.btn_convertor.addItem('OpenOffice')
        self.btn_convertor.addItem('CloudConvert')
        self.btn_convertor.addItem('Google')
        self.btn_convertor.setCurrentText(self.convertor)
        # ontop
        self.ontop_checkbox = QCheckBox(self)
        self.ontop_checkbox.setChecked(self.ontop)
        # self.ontop.setChecked(self.ontop)
        # self.btn_convertor.setObjectName("btn_conv")
        # self.btn_convertor.activated[str].connect(self.color_box_change) 
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        self.layout.addRow("OCR language", self.text_link)
        self.layout.addRow("File convertor", self.btn_convertor)
        self.layout.addRow("Rastering resolution (DPI)", self.res_box)
        self.layout.addRow("Window always on top",self.ontop_checkbox)
        self.layout.addWidget(self.buttonBox)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.resize(50, 200)

    def getInputs(self):
        self.destroy()
        return self.text_link.text(), self.res_box.value(), self.btn_convertor.currentText(), self.ontop_checkbox.isChecked()    

class Window(QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.preferences = {}
        self.load_settings()
        self.preview_widget_open = False
        self.drag_position = QPoint()  # Pro sledování pozice myši
        self.widget = None  # Inicializace widgetu jako None
        if self.preferences.get("on_top"):
            self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint) 
        self.setWindowTitle("PrintManager " + version)
        self.setAcceptDrops(True)
        menubar = self.menuBar()
        menubar.setNativeMenuBar(True)
        file_menu = QMenu('File', self)
        edit_menu = QMenu('Edit', self)
        win_menu = QMenu('Windows', self)
        about_menu = QMenu('About', self)
        open_action = QAction("Open file", self) 
        self.printing_setting_menu  = QAction("Printers", self)
        self.printing_setting_menu.setShortcut('Ctrl+P')
        self.printing_setting_menu.setCheckable(True)
        self.printing_setting_menu.setChecked(self.preferences['printer_panel'])
        self.printing_setting_menu.triggered.connect(self.togglePrintWidget)
        win_menu.addAction(self.printing_setting_menu)
        # DEBUG PANEL
        self.debug_setting_menu  = QAction("Debug", self)
        self.debug_setting_menu.setShortcut('Ctrl+D')
        self.debug_setting_menu.setCheckable(True)
        self.debug_setting_menu.setChecked(self.preferences['debug_panel'])
        self.debug_setting_menu.triggered.connect(self.toggleDebugWidget)
        win_menu.addAction(self.debug_setting_menu)
        # PREVIEW PANEL
        self.preview_setting_menu  = QAction("Preview panel", self)
        self.preview_setting_menu.setShortcut('Ctrl+I')
        self.preview_setting_menu.setCheckable(True)
        self.preview_setting_menu.setChecked(self.preferences['preview_panel'])
        self.preview_setting_menu.triggered.connect(self.togglePreviewWidget)
        win_menu.addAction(self.preview_setting_menu)

        # EDIT PAGE
        select_all = QAction("Select all", self)
        select_all.setShortcut('Ctrl+A')
        select_all.triggered.connect(self.select_all_action)
        edit_menu.addAction(select_all)

        rotate_90cw = QAction("Rotate 90cw", self)
        rotate_90cw.setShortcut('Ctrl+R')
        rotate_90cw.triggered.connect(lambda: self.rotator(angle=90))
        edit_menu.addAction(rotate_90cw)

        rotate_180 = QAction("Rotate 180", self)
        rotate_180.setShortcut('Ctrl+Alt+Shift+R')
        rotate_180.triggered.connect(lambda: self.rotator(angle=180))
        edit_menu.addAction(rotate_180)

        clear_all = QAction("Clear all files", self)
        clear_all.setShortcut('Ctrl+X')
        clear_all.triggered.connect(self.clear_table)
        edit_menu.addAction(clear_all)

        # PREVIEW
        preview_menu  = QAction("Preview", self)
        preview_menu.setShortcut('ALT')
        preview_menu.triggered.connect(self.preview_window)
        win_menu.addAction(preview_menu)
        # PREFERENCES
        pref_action = QAction("Preferences", self)
        pref_action.triggered.connect(self.open_dialog)
        pref_action.setShortcut('Ctrl+W')
        file_menu.addAction(pref_action)
        # GITHUB PAGE
        url_action = QAction("PrintManager Github", self)
        url_action.triggered.connect(self.open_url)
        about_menu.addAction(url_action)
        # OPEN
        open_action.triggered.connect(self.openFileNamesDialog)
        open_action.setShortcut('Ctrl+O')
        file_menu.addAction(open_action)
        close_action = QAction(' &Exit', self)
        close_action.triggered.connect(self.close)
        file_menu.addAction(close_action)
        menubar.addMenu(file_menu)
        menubar.addMenu(edit_menu)
        menubar.addMenu(win_menu)
        menubar.addMenu(about_menu)

        self.files = []
        """Core Layouts"""
        self.mainLayout = QGridLayout()
        self.table_reload(self.files)
        self.createPrinter_layout()
        self.createDebug_layout()  # Zajištění, že je volána
        self.createButtons_layout()
        # pref_preview_state = self.createPreview_layout()
        self.createPreview_layout()
        # HACK to window size on boot
        if self.pref_preview_state == 0:
            self.setFixedSize(617, 650)
            self.resize(617, 650)
        else:
            self.setFixedSize(875, 650)
            self.resize(875, 650)
        self.mainLayout.addLayout(self.printer_layout, 0, 0, 1, 2)
        self.mainLayout.addLayout(self.debug_layout, 2, 0, 1, 2)
        self.mainLayout.addLayout(self.preview_layout, 0, 3, 0, 3)
        self.mainLayout.addLayout(self.buttons_layout, 3, 0, 1, 2)

        """Initiating  mainLayout """
        self.window = QWidget()
        self.window.setLayout(self.mainLayout)
        self.setCentralWidget(self.window)
        # new code load setting  

    def createDebug_layout(self):
        self.debug_layout = QHBoxLayout()
        self.gb_debug = QGroupBox("Debug")
        self.gb_debug.setVisible(self.preferences['debug_panel'])
        self.gb_debug.setChecked(True)
        self.gb_debug.setTitle('')
        self.gb_debug.setFixedHeight(90)
        self.gb_debug.setFixedWidth(600)
        self.gb_debug.setContentsMargins(0, 0, 0, 0)
        self.gb_debug.setStyleSheet("border: 0px; border-radius: 0px; padding: 0px 0px 0px 0px;")
        dbox = QVBoxLayout()
        dbox.setContentsMargins(0, 0, 0, 0);
        self.gb_debug.setLayout(dbox)
        # debug
        self.debuglist = QTextEdit(self)
        self.debuglist.acceptRichText()
        self.debuglist.setReadOnly(True)
        self.debuglist.setFixedHeight(80)
        self.debuglist.setFixedWidth(597)
        dbox.addWidget(self.debuglist)
        self.gb_debug.toggled.connect(self.toggleDebugWidget)
        self.debug_layout.addWidget(self.gb_debug)

    def save_settings(self):
        preferences = {
            "language": self.localization,
            "resolution": self.resolution,
            "convertor": self.convertor,
            "on_top": self.ontop,
            "printer_panel": self.printing_setting_menu.isChecked(),
            "debug_panel": self.debug_setting_menu.isChecked(),
            "preview_panel": self.preview_setting_menu.isChecked(),
            "printers": load_printers(),
            "cups_running": is_cups_running(),
            "arch_check": is_arch_check(),
            "printer_presets": get_printer_presets()
        }
        settings = QSettings("Devrosx", "PrintManager_2")  # Zadejte vaše názvy
        settings.setValue("data", preferences)  # Uložení dat jako hodnoty
        # print('saving...')
        self.load_settings()

    def load_settings(self):
        settings = QSettings("Devrosx", "PrintManager_2")  # Zadejte vaše názvy
        preferences = settings.value("data", None)  # Načtení dat
        # print('loading...')

        if preferences is not None:
            self.preferences = preferences  # Uložení preferences jako atribut instance
            self.convertor = self.preferences['convertor']
            self.resolution = self.preferences['resolution']
            self.ontop = self.preferences['on_top']
            self.localization = self.preferences['language']
            if self.preferences['preview_panel'] == True:
                self.pref_preview_state = 1
            else:
                self.pref_preview_state = 0

    def open_url(self):
        url = 'http://github.com/devrosx/PrintManager/'
        subprocess.run(['open', url])  # Pouze pro macOS
  

    def open_dialog(self):
        # load setting first
        # default_pref = load_preferences()
        form = PrefDialog(self.localization, self.resolution, self.convertor, self.ontop)
        form.setFixedSize(400, 180)
        try:
            if form.exec():
                self.localization, self.resolution, self.convertor, self.ontop = form.getInputs()
        except Exception as e:
            print(e)

    def check_menu_items(self):
        # Zkontrolujte stav akcí a vraťte jejich hodnoty
        return self.printing_setting_menu.isChecked(), self.debug_setting_menu.isChecked()

    def closeEvent(self, event):
        close = QMessageBox()
        close.setText("Are you sure?")
        close.setIcon(QMessageBox.Icon.Warning)
        close.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        close.setDefaultButton(QMessageBox.StandardButton.Yes)
        close_result = close.exec()

        if close_result == QMessageBox.StandardButton.Yes:
            printer_checked, debug_checked = self.check_menu_items()
            # print(f"Printers checked: {printer_checked}, Debug checked: {debug_checked}")
            self.save_settings()
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.accept()

    def dragLeaveEvent(self, event):
        event.accept()
        self.table.setStyleSheet("QTableView {background-image:none}" )

    def dragEnterEvent(self, event):
        event.setDropAction(Qt.DropAction.MoveAction)
        if event.mimeData().hasUrls():
            # self.d_writer(event.mimeData().text(), 0)
            self.table.setStyleSheet("QTableView {border: 2px solid #00aeff;background-image: url(icons/drop.png);background-repeat: no-repeat;background-position: center center;background-color: #2c2c2c; }")
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        # self.d_writer("Loading files - please wait...", 0, 'green')
        image_files = []
        office_files = []
        unknown_files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            extension = os.path.splitext(path)[1][1:].strip().lower()
            # handle file
            if os.path.isfile(path):
                if extension == 'pdf':
                    self.files = pdf_parse(self, path)
                    # self.d_writer(path, 0, 'green')
                    Window.table_reload(self, self.files)
                # handle images to list
                if extension in image_ext:
                    image_files.append(path)
                    # print ('Image path:' + path)
                # handle offices files to list
                if extension in office_ext:
                    office_files.append(path)
                    # print ('Office path:' + path)
                if extension not in office_ext and extension not in image_ext and extension not in next_ext:
                    unknown_files.append(path)
                if extension == 'dat':
                    dirname_ = (os.path.dirname(path) + '/')
                    dirname = str(QFileDialog.getExistingDirectory(self, "Save file", dirname_))
                    if dirname:
                        with open(path, "rb") as tneffile:
                            t = TNEF(tneffile.read())
                            for a in t.attachments:
                                with open(os.path.join(dirname, a.name.decode("utf-8")), "wb") as afp:
                                    afp.write(a.data)
                            self.d_writer("Successfully wrote %i files" % len(t.attachments) + ' to: ' + dirname, 0)

        if image_files:
            if len(image_files) > 1:
                items = ["Convert to PDF " + (self.convertor), "Combine to PDF " + (self.convertor), "Import"]
                text, okPressed = QInputDialog.getItem(self, "Image import", "Action", items, 0, False)
                if not okPressed:
                    return
                if text == "Combine to PDF " + (self.convertor):
                    files = self.external_convert(extension, image_files, 'combine')
                if text == 'Import':
                    self.files = img_parse(self, image_files)
                    Window.table_reload(self, self.files)
            else:
                items = ["Convert to PDF", "Import"]
                text, okPressed = QInputDialog.getItem(self, "Image import", "Action", items, 0, False)                    
                if not okPressed:
                    return
                if text == 'Convert to PDF':
                    files = self.external_convert(extension, image_files, 'convert')
                if text == 'Import':
                    # parse_files = []
                    self.files = img_parse(self, image_files)
                    Window.table_reload(self, self.files)

        # fix long names
        if office_files:
            if len(office_files) > 1:
                items = ["Convert to PDF", "Combine to PDF", "Combine to PDF (add blank page to odd documents"]
                text, okPressed = QInputDialog.getItem(self, "Action", "Action", items, 0, False)
                if not okPressed:
                    return
                if text == 'Convert to PDF':
                    self.d_writer("Converting to PDF (" + self.convertor + '): ' + extension, 0)
                    files = self.external_convert(extension, office_files, 'convert')
                if text == 'Combine to PDF':
                    files = self.external_convert(extension, office_files, 'combine')
                if text == 'Combine to PDF (add blank page to odd documents':
                    files = self.external_convert(extension, office_files, 'combinefix')
            else:
                self.d_writer("Converting to PDF (" + self.convertor + '): ' + extension, 0)
                files = self.external_convert(extension, office_files, 'convert')
        # handle images
        if unknown_files:
            conv = QMessageBox()
            conv.setText("Warning One of files isnt propably supported. Do you still want to try import to PDF? (Clouconvert importer recomended)")
            conv.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
            conv = conv.exec()
            if conv == QMessageBox.StandardButton.Yes:
                self.external_convert(extension, unknown_files, 'convert')
            else:
                event.ignore()
        self.table.setStyleSheet("QTableView {background-image:none}")

    def d_writer(self, message, append, color='white'):
        # Pokud je message seznam, spojíme ho pomocí '\n'
        if isinstance(message, list):
            message = '\n'.join(message)
        # Pokud message obsahuje '\n', rozdělíme ho a použijeme HTML pro každý řádek
        message_lines = message.split('\n')
        formatted_message = ' '.join(f'<font color={color}><b>{line}</b></font>' for line in message_lines)
        
        if append:
            # Přidání formátovaného textu do debuglist
            current_text = self.debuglist.document().toHtml()
            self.debuglist.setHtml(current_text + formatted_message)
            # Posuňte kurzor na konec textu
            self.debuglist.moveCursor(QTextCursor.MoveOperation.End)
        else:
            # Smazání obsahu debuglistu
            self.debuglist.clear()  # Čistíme obsah
            # Přidání nového formátovaného textu
            self.debuglist.setHtml(formatted_message)
            
            # Posuňte kurzor na konec textu
            self.debuglist.moveCursor(QTextCursor.MoveOperation.End)

    def external_convert(self, ext, inputfile, setting):
        print ('external conv:' +str(self.convertor))
        converts = []
        if setting == 'convert':
            outputdir = os.path.dirname(inputfile[0]) + '/'
        else:
            outputdir = "/tmp/"
            savedir = os.path.dirname(inputfile[0]) + '/'
    
        if self.convertor == 'OpenOffice':
            print('OpenOffice convert')
            
            # Příprava příkazu pro konverzi
            command = ["/Applications/LibreOffice.app/Contents/MacOS/soffice", "--headless", "--convert-to", "pdf"]
        
            # Přidání všech souborů do příkazového řetězce
            command.extend(inputfile)
            command.append("--outdir")
            command.append(outputdir)
        
            try:
                # Spuštění příkazu
                p = subprocess.Popen(command, stderr=subprocess.PIPE)
                output, err = p.communicate()
        
                # Zkontrolujte, zda došlo k chybě při konverzi
                if p.returncode != 0:
                    raise RuntimeError(f"Chyba při konverzi: {err.decode('utf-8')}")
                # Generování seznamu konvertovaných souborů
                for items in inputfile:
                    base = os.path.basename(items)
                    base = os.path.splitext(base)[0]
                    new_file = os.path.join(outputdir, base + '.pdf')
                    converts.append(new_file)
            except Exception as e:
                handle_exception(e)  # Zavolání funkce pro zpracování výjimek
    
            # Zpracování podle nastavení
            if setting in ['combine', 'combinefix']:
                print('converts: ' + str(converts))
                merged_pdf = mergefiles(converts, savedir)
                print('this is merged_pdf: ' + str(merged_pdf))
                self.files = pdf_parse(self, merged_pdf)
                self.d_writer('OpenOffice combining files to:', 0, 'green')
                self.d_writer(merged_pdf[0], 1)
                Window.table_reload(self, self.files)
            else:
                self.d_writer('OpenOffice converted files:', 0, 'green')
                self.d_writer(converts, 1)
                self.files = pdf_parse(self, converts)
                Window.table_reload(self, self.files)
    
        elif self.convertor == 'CloudConvert':
            print('CloudConvert')
            from libs.cc_module import cc_convert
            for items in inputfile:
                try:
                    # Oprava diakritiky (zkontrolujte lepší opravu později)
                    items = fix_filename(items)
                    new_file, warning = cc_convert(items)
        
                    if warning == "'NoneType' object is not subscriptable" or warning == "[Errno 2] No such file or directory: 'cc.json'":
                        self.d_writer('missing API_KEY', 0, 'red')
                        API_KEY, okPressed = QInputDialog.getText(self, "Warning ", "Cloudconvert API key error, enter API key", QLineEdit.Normal, "")
                        with open("cc.json", "w") as text_file:
                            text_file.write(API_KEY)
                        self.d_writer('API_KEY saved - Try import again', 0, 'red')
                    elif new_file is None:
                        self.d_writer(warning, 0, 'red')
                        # print(warning)
                        # QMessageBox.about(self, "Warning", warning)
                    else:
                        print('converting...')
                        self.d_writer('converting...', 0, 'green')
                        converts.append(new_file)
        
                except Exception as e:
                    handle_exception(e)  # Zavolání funkce pro zpracování výjimek

        elif self.convertor == 'Google':
            print('Google convert')
            from libs.google_module import convert_doc_to_pdf
            for items in inputfile:
                try:
                    # Oprava diakritiky (zkontrolujte lepší opravu později)
                    items = fix_filename(items)
                    new_file = convert_doc_to_pdf(items)
        
                    if new_file is None:
                        self.d_writer(warning, 0, 'red')
                        # QMessageBox.about(self, "Warning", warning)
                    else:
                        print('converting...')
                        converts.append(new_file)
        
                except Exception as e:
                    handle_exception(e)  # Zavolání funkce pro zpracování výjimek
    
            if setting == 'combine':
                merged_pdf = mergefiles(converts, savedir)
                merged_pdf = [merged_pdf]  # Oprava pro pozdější použití
                self.files = pdf_parse(self, merged_pdf)
                self.d_writer('CloudConvert combining files to:', 0, 'green')
                self.d_writer(merged_pdf[0], 1)
                Window.table_reload(self, self.files)
            else:
                self.files = pdf_parse(self, converts)
                Window.table_reload(self, self.files)

    def table_reload(self, inputfile):
        self.table = TableWidgetDragRows()
        headers = ["", "File", "Size", "Kind", "File size", "Pages", "Price", "Colors", "Path"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setFocus()  

        # Připojíme signál pro otevření dialogu
        self.table.openFileDialogRequested.connect(self.openFileNamesDialog)
    
        # better is preview (printig etc) , 'File path'
        self.table.itemSelectionChanged.connect(self.get_page_size)
        self.table.verticalHeader().setDefaultSectionSize(35)
        self.table.setFixedWidth(598)
        self.table.setColumnWidth(0, 35)
        self.table.setColumnWidth(1, 228)
        self.table.setColumnWidth(3, 34)
        self.table.setColumnWidth(4, 65)
        self.table.setColumnWidth(5, 37)
        self.table.setColumnWidth(6, 50)
        self.table.setColumnWidth(7, 50)
        # Skrytí horizontálního scrollbaru
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # Lepší zobrazení hlaviček
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.table.verticalHeader().setDefaultSectionSize(35)
        self.table.verticalHeader().setVisible(False)
        # ICONS
        self.table.setIconSize(QSize(32, 32))
        delegate = IconDelegate(self.table) 
        self.table.setItemDelegate(delegate)
        pdf_file = "icons/pdf.png"
        pdf_item = QTableWidgetItem()
        pdf_icon = QIcon()
        pdf_icon.addPixmap(QPixmap(pdf_file))
        # pixmap = pdf_icon.pixmap(QSize(50, 50))
        pdf_item.setIcon(pdf_icon)
        jpg_file = "icons/jpg.png"
        jpg_item = QTableWidgetItem()
        jpg_icon = QIcon()
        jpg_icon.addPixmap(QPixmap(jpg_file))
        jpg_item.setIcon(jpg_icon)

        self.table.setRowCount(len(inputfile))
        for i, (Info, File, Size, Kind, Filesize, Pages, Price, Colors, Filepath) in enumerate(inputfile):
            self.table.setItem(i, 1, QTableWidgetItem(File))
            self.table.setItem(i, 2, QTableWidgetItem(Size))
            self.table.setItem(i, 3, QTableWidgetItem(Kind))
            self.table.setItem(i, 4, QTableWidgetItem(Filesize))
            self.table.setItem(i, 5, QTableWidgetItem(str(Pages)))
            self.table.setItem(i, 6, QTableWidgetItem(Price))
            self.table.setItem(i, 7, QTableWidgetItem(Colors))
            self.table.setItem(i, 8, QTableWidgetItem(Filepath))
            # self.table.setColumnHidden(8, True)
        # print ('rowcount je:' + str(self.table.rowCount()))
        if self.table.rowCount() == 0:
            self.table.setStyleSheet("background-image: url(icons/drop.png);background-repeat: no-repeat;background-position: center center;background-color: #191919;")
        # icons 
        for row in range(0, self.table.rowCount()):
            item = self.table.item(row, 3)
            if item.text() == 'pdf':
                self.table.item(row, 2).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.item(row, 3).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.item(row, 4).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.item(row, 5).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.item(row, 6).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, QTableWidgetItem(pdf_item))
            else:
                self.table.item(row, 2).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.item(row, 3).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.item(row, 4).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.item(row, 5).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.item(row, 6).setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row, 0, QTableWidgetItem(jpg_item))

        self.table.selectionModel().selectionChanged.connect(
            self.on_selection_changed)
        # RIGHT CLICK MENU
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.contextMenuEvent)     
        self.mainLayout.addWidget(self.table, 1, 0, 1, 2)
        self.update()

    @pyqtSlot()
    def on_selection_changed(self):
        self.my_info_label.setText(str(self.count_pages()) + ' pages selected')
        # self.debuglist.clear()
        if self.selected_file_check() == 'pdf':
            self.pdf_button.show()
            self.img_button.hide()
            self.print_b.show()
            self.color_b.show()
            self.crop_b.show()
            print(self.count_pages())
            self.my_info_label.show()
            if len(self.table.selectionModel().selectedRows()) > 1:
                self.merge_pdf_b.show()
            if int(self.count_pages()) > 1:
                self.split_pdf_b.show()
            self.Convert_b.hide()
        elif self.selected_file_check() == 'image':
            self.pdf_button.hide()
            self.img_button.show()
            self.print_b.show()
            self.crop_b.show()
            self.color_b.hide()
            self.my_info_label.setText("Image files selected")
            self.my_info_label.show()
            self.split_pdf_b.hide()
            self.merge_pdf_b.hide()
            self.Convert_b.show()
        else:
            self.split_pdf_b.hide()
            self.color_b.hide()
            self.merge_pdf_b.hide()
            self.crop_b.hide()
            self.pdf_button.hide()
            self.img_button.hide()
            self.print_b.hide()
            self.my_info_label.hide()
            self.Convert_b.hide()
            self.move_page.hide()
            for items in sorted(self.table.selectionModel().selectedRows()):
                # index=(self.table.selectionModel().currentIndex())
                row = items.row()
                # filetype=index.sibling(items.row(),3).data()
                # if filetype == 'pdf':
                # print(row)
                remove_from_list(self, row)
                del(self.files[row])

    def contextMenuEvent(self, pos):
        file_paths = []
        # if not self.table.selectionModel().selectedRows():
        #     print('mic')
        #     return  # Oprava: přidání návratu, pokud nejsou vybrány žádné řádky
        # else:
        for items in sorted(self.table.selectionModel().selectedRows()):
            index = (self.table.selectionModel().currentIndex())
            row = items.row()
            file_path = index.sibling(row, 8).data()
            file_paths.append(file_path)
        menu = QMenu()
        openAction = menu.addAction('Open')
        revealAction = menu.addAction('Reveal in finder')
        printAction = menu.addAction('Print')
        previewAction = menu.addAction('Preview')
        fix_nameAction = menu.addAction('Remove special characters from filename')
        sort_images = menu.addAction('Sort portrait and landscape')
        action = menu.exec(self.mapToGlobal(pos))
        menu.hide()
        if action == openAction:
            revealfile(file_paths, '')
        if action == revealAction:
            revealfile(file_path, '-R')
        if action == fix_nameAction:
            self.deleteClicked()
            for items in file_paths:
                newname = fix_filename(items)
                if newname.lower().endswith == '.pdf':
                    self.files = pdf_parse(self, [newname])
                    Window.table_reload(self, self.files)
                else:
                    self.files = img_parse(self, [newname])
                    Window.table_reload(self, self.files)
                    self.d_writer('Renamed: ' + str(newname), 1, 'green')
        if action == sort_images:
            self.indetify_orientation(items)
        if action == printAction:
            index = (self.table.selectionModel().currentIndex())
            row = self.table.currentRow()
            file_path = index.sibling(row, 8).data()
            self.table_print()
        if action == previewAction:
            self.preview_window()

    # def keyPressEvent(self, event):
    #     if event.key() == 32:
    #         print ('space')
    #         file_paths = []
    #         if not self.table.selectionModel().selectedRows():
    #             print ('mic')
    #             pass
    #         else:
    #             for items in sorted(self.table.selectionModel().selectedRows()):
    #                 index = (self.table.selectionModel().currentIndex())
    #                 row = items.row()
    #                 file_path = index.sibling(row, 8).data()
    #                 file_paths.append(file_path)
    #         print ('space')
    #     event.accept()

    def indetify_orientation(self, items):
        outputfiles = []
        outputimgfiles = []
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            file_path = index.sibling(items.row(), 8).data()
            file_format = index.sibling(items.row(), 2).data()
            type_ = index.sibling(items.row(), 3).data()
            if type_ == 'pdf':
                file_format_l = file_format.split('x')
                file_format_l = ' '.join(file_format_l).replace(' mm', '').split()
                file_format_l = list(map(int, file_format_l))
                if file_format_l[0] > file_format_l[1]:
                    format_ = 'l_'
                elif file_format_l[0] < file_format_l[1]:
                    format_ = 'p_'
                elif file_format_l[0] == file_format_l[1]:
                    format_ = 's_'
                self.d_writer(str(file_path) + str(format_), 1, 'green')
                newname = fix_filename(file_path, _format=format_)
                outputfiles.append(newname)
            else:
                file_format_l = file_format.split('x', 1)
                file_format_l = ' '.join(file_format_l).replace('px', '').split()
                file_format_l = list(map(int, file_format_l))
                if file_format_l[0] > file_format_l[1]:
                    format_ = 'l_'
                elif file_format_l[0] < file_format_l[1]:
                    format_ = 'p_'
                elif file_format_l[0] == file_format_l[1]:
                    format_ = 's_'
                self.d_writer(str(file_path) + str(format_), 1, 'green')
                newname = fix_filename(file_path, _format=format_)
                outputimgfiles.append(newname)
        self.deleteClicked()
        self.files = pdf_parse(self, outputfiles)
        self.files = img_parse(self, outputimgfiles)
        Window.table_reload(self, self.files)

    def toggleDebugWidget(self):
        if hasattr(self, 'gb_debug'):
            self.gb_debug.setHidden(not self.gb_debug.isHidden())
        else:
            print("gb_debug not found")

    def togglePrintWidget(self):
        self.gb_printers.setHidden(not self.gb_printers.isHidden())
        self.gb_setting.setHidden(not self.gb_setting.isHidden())

    def togglePreviewWidget(self):
        PreviewWidget = 1
        # self.setFixedSize(875, 650)
        # self.resize(875, 650)
        self.gb_preview.setHidden(not self.gb_preview.isHidden())
        # print(self.gb_preview.isHidden())
        if self.gb_preview.isHidden() == 1:
            self.setFixedSize(617, 650)
            self.resize(617, 650)
        else:
            self.setFixedSize(875, 650)
            self.resize(875, 650)
            try:
                self.get_page_size()
            except:
                pass

    def preview_window(self):
        if not self.table.selectionModel().selectedRows():
            print("No rows selected")  # Debug: Žádné řádky nejsou vybrány
            return
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = self.table.selectionModel().currentIndex()
            size = index.sibling(items.row(), 2).data()
            filename = index.sibling(items.row(), 1).data()
            filetype = index.sibling(items.row(), 3).data()
            filepath = index.sibling(items.row(), 8).data()
            pages = index.sibling(items.row(), 5).data()

        # Vytvoření widgetu pouze pokud ještě neexistuje
        if self.widget is None:
            self.widget = QDialog()
            self.widget.setWindowTitle(f"{filepath} / {size}")

            layout = QVBoxLayout(self.widget)

            self.im_p = QLabel('Image_P', self.widget)
            self.im_p.setText('PREVIEW')
            self.im_pixmap = QPixmap('')

            if filetype.upper() in (name.upper() for name in image_ext):
                self.im_pixmap = QPixmap(filepath)
                self.im_p.setPixmap(self.im_pixmap)

            if filetype == 'pdf':
                filebytes = pdf_preview_generator(filepath, generate_marks=1, page=self.move_page.value())
                self.im_pixmap.loadFromData(filebytes)
                self.im_p.setPixmap(self.im_pixmap)

            screen = QApplication.primaryScreen()
            sizeObject = screen.size()
            res = [sizeObject.width() * 0.92, sizeObject.height() * 0.92]

            w, h = self.im_pixmap.width(), self.im_pixmap.height()
            # self.widget.resize(w, h)

            if w > res[0]:
                wpercent = res[0] / float(w)
                self.widget.resize(int(w * wpercent), int(h * wpercent))

            if h > res[1]:
                hpercent = res[1] / float(h)
                self.widget.resize(int(w * hpercent), int(h * hpercent))

            # self.im_p.setPixmap(self.im_pixmap.scaled(self.widget.size(), Qt.AspectRatioMode.KeepAspectRatio))
            # self.im_p.setMinimumSize(1, 1)
            # self.widget.resize(self.im_pixmap.size())
            self.labl_name = QLabel('Image_name', self.widget)
            self.labl_name.setStyleSheet("QLabel { background-color: '#2c2c2c'; font-size: 11px; height: 16px; padding: 5px;}")
            self.labl_name.setText(f"{filename} / page: {self.move_page.value()}")

            layout.addWidget(self.im_p)
            layout.addWidget(self.labl_name)

            # Přidání události klávesnice
            self.widget.keyPressEvent = self.keyPressEvent

            # Přidání slotu pro zavření okna
            self.widget.finished.connect(self.on_widget_closed)

            # Přidání událostí myši pro přetahování
            self.im_p.mousePressEvent = self.start_drag
            self.im_p.mouseMoveEvent = self.drag_move
            self.im_p.mouseReleaseEvent = self.stop_drag
            self.widget.resizeEvent = self.on_resize
            self.widget.show()  # Otevření widgetu
            self.widget.setFocus()  # Nastavení fokusu na widget
            self.preview_widget_open = True  # Nastavení stavu na otevřené
        else:
            self.widget.raise_()  # Přivedení okna na popředí, pokud už je otevřené

    def on_resize(self, event):
        print ('TODO')
        # Změna velikosti obrázku podle velikosti okna
        # if self.im_pixmap:
        #     scaled_pixmap = self.im_pixmap.scaled(self.widget.size(), Qt.AspectRatioMode.KeepAspectRatio)
        #     self.im_p.setPixmap(scaled_pixmap)
        # event.accept()


    def start_drag(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.widget.frameGeometry().topLeft()
            event.accept()

    def drag_move(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.widget.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def stop_drag(self, event):
        pass  # Můžete zde přidat další logiku, pokud je potřeba

    def close_preview_window(self):
        if self.widget:
            self.widget.close()  # Zavření widgetu

    def on_widget_closed(self):
        self.widget = None  # Nastavení widgetu na None
        self.preview_widget_open = False  # Nastavení stavu na zavřené


    class ExtendedQLabel(QLabel):
        def __init__(self, parent):
            super().__init__(parent)
        
        clicked = pyqtSignal()
        rightClicked = pyqtSignal()

        def mousePressEvent(self, ev):
            if ev.button() == Qt.MouseButton.RightButton:
                self.rightClicked.emit()
            else:
                self.clicked.emit()

    def createPreview_layout(self):
        self.preview_layout = QHBoxLayout()
        # PREVIEW GROUPBOX
        self.gb_preview = QGroupBox("Preview file")
        self.gb_preview.setVisible(self.preferences['preview_panel'])
        pbox = QVBoxLayout()
        # image
        self.image_label = self.ExtendedQLabel(self)
        self.image_label_pixmap = QPixmap('')
        self.image_label.setPixmap(self.image_label_pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.clicked.connect(self.preview_window)
        self.labl_name = QLabel()
        self.labl_name.setStyleSheet("QLabel { background-color : '#2c2c2c'; border-radius: 5px; font-size: 12px;}")
        self.labl_name.setText('No file selected')
        self.labl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.labl_name.setFixedHeight(30)
        self.labl_name.setWordWrap(True)
        self.move_page = QSpinBox()
        self.move_page.setValue(1)
        self.move_page.setMinimum(1)
        self.move_page.setFixedWidth(70)
        self.move_page.setFixedHeight(30)
        self.move_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.move_page.setStyleSheet("QSpinBox{background-color:#343434;selection-background-color: '#343434';selection-color: white;}QSpinBox::down-button{subcontrol-origin:margin;subcontrol-position:center left;width:19px;border-width:1px}QSpinBox::down-arrow{image:url(icons/down.png);min-width:19px;min-height:14px;max-width:19px;max-height:14px;height:19px;width:14px}QSpinBox::down-button:pressed{top:1px}QSpinBox::up-button{subcontrol-origin:margin;subcontrol-position:center right;width:19px;border-width:1px}QSpinBox::up-arrow{image:url(icons/up.png);min-width:19px;min-height:14px;max-width:19px;max-height:14px;height:19px;width:14px}QSpinBox::up-button:pressed{top:1px}")
        self.move_page.hide()
        # infotable
        self.infotable = QTextEdit()
        self.infotable.setStyleSheet("QTextEdit { background-color : '#2c2c2c'; border-radius: 5px; font-size: 12px;}")
        self.infotable.acceptRichText()
        self.infotable.setText('Info')
        self.infotable.setReadOnly(True)
        self.infotable.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.infotable.setFixedHeight(210 - 30)
        self.gb_preview.setLayout(pbox)
        self.gb_preview.setFixedWidth(250)
        pbox.addWidget(self.image_label)
        pbox.addWidget(self.move_page, alignment=Qt.AlignmentFlag.AlignCenter)
        pbox.addWidget(self.labl_name)
        pbox.addWidget(self.infotable)
        self.preview_layout.addWidget(self.gb_preview)
        self.setFixedWidth(self.sizeHint().width() + 300)
        pref_preview_state = self.preferences['preview_panel']
        return pref_preview_state

    def createButtons_layout(self):
        self.buttons_layout = QHBoxLayout()
        self.color_b = QPushButton('Colors', self)
        self.color_b.setFixedWidth(55)  # Nastavení šířky na 100 pixelů
        self.color_b.clicked.connect(self.loadcolors)
        self.buttons_layout.addWidget(self.color_b)
        # self.color_b.setDisabled(True)
        self.color_b.hide()

        # # COMPRES PDF
        # self.compres_pdf_b = QPushButton('Compres', self)
        # self.compres_pdf_b.clicked.connect(self.compres_pdf)
        # self.buttons_layout.addWidget(self.compres_pdf_b)
        # self.compres_pdf_b.setDisabled(True)
        # # GRAY PDF
        # self.gray_pdf_b = QPushButton('To Gray', self)
        # self.gray_pdf_b.clicked.connect(self.gray_pdf)
        # self.buttons_layout.addWidget(self.gray_pdf_b)
        # self.gray_pdf_b.setDisabled(True)
        # # RASTROVANI PDF
        # self.raster_b = QPushButton('Rasterize', self)
        # self.raster_b.clicked.connect(self.rasterize_pdf)
        # self.buttons_layout.addWidget(self.raster_b)
        # self.raster_b.setDisabled(True)
        # CROP PDF WIP
        # self.crop_b = QPushButton('SmartCrop', self)
        # self.crop_b.clicked.connect(self.crop_pdf)
        # # self.crop_b.clicked.connect(self.InputDialog_PDFcut)
        # # InputDialog_PDFcut
        # self.buttons_layout.addWidget(self.crop_b)
        # self.crop_b.setDisabled(True)
        # # EXTRACT IMAGES
        # self.extract_b = QPushButton('Extract', self)
        # self.extract_b.clicked.connect(self.extract_pdf)
        # self.buttons_layout.addWidget(self.extract_b)
        # self.extract_b.setDisabled(True)
        # OCR
        # self.OCR_b = QPushButton('OCR', self)
        # self.OCR_b.clicked.connect(self.ocr_maker)
        # self.buttons_layout.addWidget(self.OCR_b)
        # self.OCR_b.setDisabled(True)
        # CONVERT (only for image files)
        self.Convert_b = QPushButton('Convert to PDF', self)
        self.Convert_b.clicked.connect(self.convert_image)
        self.buttons_layout.addWidget(self.Convert_b)
        self.Convert_b.hide()

        self.pdf_button = QPushButton('PDF Actions')
        menu = QMenu()
        colors_menu = QMenu('Colors', self)
        menu.addMenu(colors_menu)
        convert_menu = QMenu('Convert and crop', self)
        menu.addMenu(convert_menu)
        other_menu = QMenu('Other', self)
        menu.addMenu(other_menu)
        convert_menu.addAction('Extract images from PDF', self.extract_pdf)
        convert_menu.addAction('Rasterize PDF (300dpi)', self.convert_image)
        convert_menu.addAction('SmartCrop', self.crop_pdf)
        convert_menu.addAction('Remove Cropmarks', self.remove_cropmarks_pdf)
        colors_menu.addAction('To CMYK')
        colors_menu.addAction('To Grayscale', self.gray_pdf)
        other_menu.addAction('Fix PDF', lambda: self.operate_file(fix_this_file, 'File(s) fixed:'))
        other_menu.addAction('Rasterize PDF', lambda: self.operate_file(raster_this_file, 'File(s) rasterized:', resolution))
        other_menu.addAction('Flaten transparency PDF', lambda: self.operate_file(flaten_transpare_pdf, 'File(s) converted:'))
        other_menu.addAction('Compress PDF', lambda: self.operate_file(compres_this_file, 'File(s) compressed:'))
        other_menu.addAction('OCR', self.ocr_maker)
        other_menu.addAction('Add page to odd documents', self.add_pager)
        self.pdf_button.setMenu(menu)
        self.buttons_layout.addWidget(self.pdf_button)
        self.pdf_button.hide()

        self.img_button = QPushButton('Image Actions')
        menu = QMenu()
        colors_menu = QMenu('Colors', self)
        menu.addMenu(colors_menu)
        convert_menu = QMenu('Convert and crop', self)
        menu.addMenu(convert_menu)
        other_menu = QMenu('Other', self)
        menu.addMenu(other_menu)
        convert_menu.addAction('SmartCrop', lambda: self.operate_file(smart_cut_this_file, 'Images(s) croped', default_pref[1]))
        convert_menu.addAction('StitchImages', lambda: self.operate_file(smart_stitch_this_file, 'Images(s) Stitched'))
        convert_menu.addAction('StitchImages_advanced', lambda: self.operate_file(smart_stitch_this_file_adv, 'Images(s) Stitched'))

        colors_menu.addAction('To CMYK')
        colors_menu.addAction('To Grayscale', self.gray_pdf)
        colors_menu.addAction('Invert colors', self.invertor)
        other_menu.addAction('OCR', self.ocr_maker)
        other_menu.addAction('Resize', self.resize_image)
        other_menu.addAction('Find similar image on google', lambda: self.operate_file(find_this_file, 'Images(s) found', default_pref[1]))

        self.img_button.setMenu(menu)
        self.buttons_layout.addWidget(self.img_button)
        self.img_button.hide()

        # SPOJ PDF
        self.merge_pdf_b = QPushButton('Merge files', self)
        self.merge_pdf_b.clicked.connect(self.merge_pdf)
        self.buttons_layout.addWidget(self.merge_pdf_b)
        # self.merge_pdf_b.setDisabled(True)
        self.merge_pdf_b.hide()

        # ROZDEL PDF
        self.split_pdf_b = QPushButton('Split pages', self)
        self.split_pdf_b.clicked.connect(self.split_pdf)
        self.buttons_layout.addWidget(self.split_pdf_b)
        # self.split_pdf_b.setDisabled(True)
        self.split_pdf_b.hide()

        self.print_b = QPushButton('Print selected', self)
        self.print_b.setDefault(True)  # Nastavení tlačítka jako výchozí
        self.print_b.clicked.connect(self.table_print)
        # self.print_b.setDisabled(True)
        self.print_b.hide()
        self.print_b.setFocus()
        self.buttons_layout.addWidget(self.print_b)

        self.crop_b = QPushButton('', self)
        self._icon = QIcon()
        self._icon.addPixmap(QPixmap('icons/crop.png'))
        self.crop_b.setIcon(self._icon)
        self.crop_b.setMaximumWidth(22)
        self.crop_b.setIconSize(QSize(14, 14))
        # self.crop_b.clicked.connect(lambda: live_crop_window('/Users/jandevera/Desktop/1.png'))
        self.crop_b.clicked.connect(self.create_crop_window)
        self.crop_b.hide()
        self.buttons_layout.addWidget(self.crop_b)

        self.my_info_label = QLabel()
        self.my_info_label.setText("Files selected")
        self.my_info_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.buttons_layout.addWidget(self.my_info_label)
        self.my_info_label.hide()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Delete:
            self.deleteClicked()
        elif e.key() == 16777251:  # Kód pro F1
            if self.preview_widget_open:
                self.close_preview_window()
            else:
                self.preview_window()
        else:
            super().keyPressEvent(e)


    def create_crop_window(self):
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            file_path = index.sibling(items.row(), 8).data()
            filetype = index.sibling(items.row(), 3).data()
            pages = int(index.sibling(items.row(), 5).data())
            if filetype == 'pdf':
                print('conversion')
                file_path_preview = pdf_preview_generator(file_path, generate_marks=1, page=0)
                self.live_crop_window = LiveCropWindow(file_path_preview)
                self.live_crop_window.show()
            else:
                self.live_crop_window = LiveCropWindow(file_path)
                self.live_crop_window.show()
            if self.live_crop_window.exec():
                cropcoordinates = self.live_crop_window.get_value()
                if filetype != 'pdf':
                    crop_image(file_path, cropcoordinates)
                    self.live_crop_window.destroy()
                    self.files = update_img(self, file_path, row)
                    self.reload(row)
                    Window.table_reload(self, self.files)
                    self.table.selectRow(row)
                    self.d_writer(f'File croped: {file_path}', 1, 'green')
                else:
                    pdf_cropper_x(file_path, cropcoordinates, pages)
                    self.live_crop_window.destroy()
                    self.files = update_img(self, file_path, row)
                    self.reload(row)
                    Window.table_reload(self, self.files)
                    self.table.selectRow(row)
                    self.d_writer(f'File croped: {file_path}', 1, 'green')


# GET FILE PATH////////////////////FIX TODP
    def operate_file(self, action, debug_text, parameter=None):
        outputfiles = []
        
        # Kontrola, zda jsou vybrány soubory
        if self.table.currentItem() is None:
            self.d_writer('Error - No files selected', 1, 'red')
            return
        
        # Získání vybraných souborů
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = self.table.selectionModel().currentIndex()
            file_path = index.sibling(items.row(), 8).data()
            outputfiles.append(file_path)
        
        # Kontrola typu souboru
        if self.selected_file_check() == 'pdf':
            try:
                debugstring, outputfiles = action(outputfiles, parameter)
                self.d_writer(debug_text, 1, 'green')
                self.d_writer(', '.join(debugstring), 1)
                
                if outputfiles is not None:
                    self.files = pdf_parse(self, outputfiles)
                    Window.table_reload(self, self.files)
            except Exception as e:
                self.d_writer(f'Chyba při zpracování PDF: {e}', 1, 'red')
        else:
            try:
                debugstring, outputfiles = action(outputfiles, parameter)
                self.d_writer(debug_text, 1, 'green')
                
                if outputfiles is not None:
                    self.d_writer(', '.join(debugstring), 1)
                    self.files = img_parse(self, outputfiles)
                    Window.table_reload(self, self.files)
                else:
                    self.d_writer(', '.join(debugstring), 1)
            except Exception as e:
                self.d_writer(f'Chyba při zpracování obrázků: {e}', 1, 'red')
# GET FILE PATH////////////////////FIX TODP

    def gray_pdf(self):
        outputfiles = []
        if self.table.currentItem() == None:
            self.d_writer('Error - No files selected', 1, 'red')
            return
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            file_path = index.sibling(items.row(), 8).data()
            outputfiles.append(file_path)
        if self.selected_file_check() == 'pdf':
            debugstring, outputfiles = gray_this_file(outputfiles, 'pdf')
            self.files = pdf_parse(self, outputfiles)
        else:
            debugstring, outputfiles = gray_this_file(outputfiles, 'jpg')
            self.files = img_parse(self, outputfiles)
        Window.table_reload(self, self.files)
        self.d_writer('Converted ' + str(len(outputfiles)) + ' pdf files to grayscale:', 0, 'green')
        self.d_writer(', '.join(debugstring), 1)

    def ocr_maker(self):
        from libs.ocr_module import ocr_core
        outputfiles = []
        if self.table.currentItem() == None:
            self.d_writer('Error - No files selected', 1, 'red')
            return
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            file_path = index.sibling(items.row(), 8).data()
            pages = index.sibling(items.row(), 5).data()
            outputfiles.append(file_path)
        if self.selected_file_check() == 'pdf':
            file, outputpdf = raster_this_file_(', '.join(outputfiles), 300, 0, True, int(pages))
            for items in file:
                ocr = ocr_core(items, self.localization)
                self.d_writer(str(ocr), 1)
        else:
            for items in outputfiles:
                ocr = ocr_core(items, self.localization)
                self.d_writer(str(ocr), 1)

    def convert_image(self):
        outputfiles = []
        if self.table.currentItem() == None:
            self.d_writer('Error - No files selected', 1, 'red')
            return
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            file_path = index.sibling(items.row(), 8).data()
            outputfiles.append(file_path)
        debugstring, outputfiles = convert_this_file(outputfiles, default_pref[1])
        self.files = pdf_parse(self, outputfiles)
        Window.table_reload(self, self.files)
        self.d_writer('File(s) converted:', 1, 'green')
        self.d_writer(', '.join(debugstring), 1)

    def resize_image(self):
        outputfiles = []
        percent, ok = QInputDialog.getInt(self, "Resize image", "Enter a percent", 50, 1, 5000)
        if ok:
            if self.table.currentItem() == None:
                self.d_writer('Error - No files selected', 1, 'red')
                return
            for items in sorted(self.table.selectionModel().selectedRows()):
                row = items.row()
                index = (self.table.selectionModel().currentIndex())
                file_path = index.sibling(items.row(), 8).data()
                outputfiles.append(file_path)
            command, outputfiles = resize_this_image(outputfiles, percent)
            self.files = img_parse(self, outputfiles)
            Window.table_reload(self, self.files)
            self.d_writer('File(s)' + str(outputfiles) + ' resized', 1, 'green')

    def crop_pdf(self):
        from libs.super_crop_module import super_crop
        outputfiles = []
        if self.table.currentItem() == None:
            self.d_writer('Error - No files selected', 1, 'red')
            return
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            file_path = index.sibling(items.row(), 8).data()
            outputfiles.append(file_path)
            desktop_icon = QIcon(QApplication.style().standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))
        pdf_dialog = InputDialog_PDFcut()
        if pdf_dialog.exec():
            multipage, croppage, margin = pdf_dialog.getInputs()
            debugstring, outputfile = super_crop(file_path, 72, croppage=croppage - 1, multipage=multipage, margin=margin)
            outputfiles.append(outputfile)
            self.files = pdf_parse(self, outputfiles)
            Window.table_reload(self, self.files)
            self.d_writer(debugstring, 1, 'green')
        else:
            pdf_dialog.close()

    def remove_cropmarks_pdf(self):
        outputfiles = []
        if self.table.currentItem() == None:
            self.d_writer('Error - No files selected', 1, 'red')
            return
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            file_path = index.sibling(items.row(), 8).data()
            debugstring, outputfile = remove_cropmarks_mod(file_path, multipage=True)
            outputfiles.append(outputfile)
        self.files = pdf_parse(self, outputfiles)
        Window.table_reload(self, self.files)
        self.d_writer(debugstring, 1, 'green')

    def extract_pdf(self):
        from libs.pdfextract_module import extractfiles
        outputfiles = []
        if self.table.currentItem() == None:
            self.d_writer('Error - No files selected', 1, 'red')
            return
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            file_path = index.sibling(items.row(), 8).data()
            outputfiles.append(file_path)

        try:
            outputfiles = extractfiles(file_path, cmyk=0)
        except Exception as e:
            self.d_writer('Error - Importing error' + str(e), 1, 'red')
            return
        self.files = img_parse(self, outputfiles)
        Window.table_reload(self, self.files)
        self.d_writer('Extracted images:', 1, 'green')
        self.d_writer(str(outputfiles), 1)

    def selected_file_check(self):
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            ftype = index.sibling(items.row(), 3).data()
            if ftype == 'pdf':
                return 'pdf'
            if ftype == '':
                pass
            else:
                return 'image'

    def count_pages(self):
        soucet = []
        pages_count = []
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            soucet.append(row)
            index = (self.table.selectionModel().currentIndex())
            info = index.sibling(items.row(), 5).data()
            f_path = index.sibling(items.row(), 8).data()
            ftype = index.sibling(items.row(), 3).data()
            pages_count.append(int(info))
        return sum(pages_count)

    def info_tb(self):
        soucet = []
        stranky = []
        _files = []
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            soucet.append(row)
            index = (self.table.selectionModel().currentIndex())
            info = index.sibling(items.row(), 5).data()
            f_path = index.sibling(items.row(), 8).data()
            ftype = index.sibling(items.row(), 3).data()
            stranky.append(int(info))
            _files.append(f_path)
        if ftype == 'pdf':
            pdf_info = file_info(_files, 'pdf')
            celkem = (str(len(soucet)) + '  PDF files, ' + str(sum(stranky)) + ' pages')
            self.d_writer(str(celkem), 0, 'green')
            self.d_writer(pdf_info, 1)
        else:
            jpg_info = file_info(_files, 'image')
            self.d_writer(' '.join(_files), 0, 'green')
            self.d_writer(jpg_info, 1)

    def split_pdf(self):
        green_ = (QColor(10, 200, 50))
        for items in sorted(self.table.selectionModel().selectedRows()):
            index = (self.table.selectionModel().currentIndex())
            row = items.row()
            if int(index.sibling(items.row(), 5).data()) < 2:
                self.d_writer('Error - Not enough files to split', 1, 'red')
            else:
                index = (self.table.selectionModel().currentIndex())
                file_path = index.sibling(items.row(), 8).data()
                split_pdf = splitfiles(file_path)
                self.files = pdf_parse(self, split_pdf)
                self.d_writer('Created ' + str(len(split_pdf)) + ' pdf files:', 0, 'green')
                self.d_writer(split_pdf, 1)
                Window.table_reload(self, self.files)

    def merge_pdf(self):
        green_ = (QColor(10, 200, 50))
        combinefiles = []
        table = sorted(self.table.selectionModel().selectedRows())
        if len(table) <= 1:
            self.d_writer("Error - Choose two or more files to combine PDFs. At least two files...", 1, 'red')
        else:
            for items in table:
                row = items.row()
                index = (self.table.selectionModel().currentIndex())
                file_path = index.sibling(items.row(), 8).data()
                combinefiles.append(file_path)
            merged_pdf = mergefiles(combinefiles, 0)
            self.d_writer('New combined PDF created:', 1, 'green')
            self.d_writer(merged_pdf, 1)
            self.files = pdf_parse(self, merged_pdf)
            Window.table_reload(self, self.files)

    def loadcolors(self):
        green_ = (QColor(10, 200, 50))
        black_ = (QBrush(QColor(200, 200, 200)))
        outputfiles = []
        font = QFont()
        font.setBold(True)
        if self.table.currentItem() == None:
            QMessageBox.information(self, 'Error', 'Choose files to convert', QMessageBox.StandardButton.Ok)
            return
        indexes = self.table.selectionModel().selectedRows()
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            druh = index.sibling(items.row(), 3).data()
        if druh == 'pdf':
            for items in sorted(self.table.selectionModel().selectedRows()):
                row = items.row()
                index = (self.table.selectionModel().currentIndex())
                file_path = index.sibling(items.row(), 8).data()
                outputfiles.append(file_path)
                for items in outputfiles:
                    nc = count_page_types(items)
                    if not nc:
                        self.table.item(row, 7).setText('BLACK')
                        self.table.item(row, 7).setForeground(black_)
                        self.d_writer("Document is all grayscale", 1, 'red')
                        self.table.item(row, 7).setFont(font)
                    else:
                        self.table.item(row, 7).setText('CMYK')
                        self.table.item(row, 7).setForeground(green_)
                        self.table.item(row, 7).setFont(font)
                        self.d_writer("Color pages:", 0, 'green')
                        self.d_writer(' ' + ', '.join(map(str, nc)), 1)
        else:
            for items in sorted(self.table.selectionModel().selectedRows()):
                row = items.row()
                index = (self.table.selectionModel().currentIndex())
                file_path = index.sibling(items.row(), 8).data()
                outputfiles.append(file_path)
                for items in outputfiles:
                    image_info = getimageinfo(items)
                    self.d_writer(str(image_info[1]), 0, 'green')
                    return

    def createPrinter_layout(self):
        self.printer_layout = QHBoxLayout()
        try:
            print (self.preferences)
            # pref_l_printer = json_pref[0]['printers']
            pref_l_printer = self.preferences.get('printers', [])
            # pref_l_printer_presets = json_pref[0]['printer_presets']
            pref_l_printer_presets = self.preferences.get("printer_presets")
            # pref_printers_state = json_pref[0]['preferences']['printer_panel']
            pref_printers_state = self.preferences.get("printer_panel")

        except Exception as e:
            pref_l_printer = []
            pref_l_printer_presets = {}
            pref_printers_state = False
    
        # PRINTERS GROUPBOX
        self.gb_printers = QGroupBox("Printers")
        vbox = QVBoxLayout()
        self.gb_printers.setLayout(vbox)
        self.gb_printers.setFixedHeight(120)
        self.gb_printers.setFixedWidth(202)
        self.gb_printers.setVisible(self.preferences['printer_panel'])
        self.printer_tb = QComboBox(self)
        self.printer_tb.addItems(pref_l_printer)
        self.printer_tb.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        # PRINTERS PRESETS
        self.printer_presets = QComboBox(self)
        # Naplnění printer_presets podle první tiskárny
        if pref_l_printer:
            first_printer = pref_l_printer[0]
            self.update_printer_presets(first_printer, pref_l_printer_presets)
        # Připojení signálu pro změnu výběru v printer_tb
        self.printer_tb.currentIndexChanged.connect(self.on_printer_changed)
    
        vbox.addWidget(self.printer_tb)
        vbox.addWidget(self.printer_presets)
        
        hbox_buttons = QHBoxLayout()        
        self.ppd_file = QPushButton('Printer PPD', self)
        self.ppd_file.clicked.connect(self.open_printer_tb)
        self.cups_page = QPushButton('CUPS info', self)
        self.cups_page.clicked.connect(self.open_cups_page)
        hbox_buttons.addWidget(self.ppd_file)
        hbox_buttons.addWidget(self.cups_page)
        # vbox.addWidget(self.ppd_file)
        # vbox.addWidget(self.cups_page)
        vbox.addLayout(hbox_buttons)
        self.printer_layout.addWidget(self.gb_printers)
        self.printer_layout.addStretch()

        # SETTINGS GROUPBOX
        self.gb_setting = QGroupBox("Printer setting")
        self.vbox2 = QGridLayout()
        self.gb_setting.setFixedHeight(120)
        self.gb_setting.setFixedWidth(391)
        self.gb_setting.setVisible(pref_printers_state)
        # # POČET KOPII
        copies_Label = QLabel("Copies:")
        self.copies = QSpinBox()
        self.copies.setValue(1)
        self.copies.setMinimum(1)
        self.copies.setMaximum(999)
        self.copies.setFixedSize(60, 25)
        self.copies.setEnabled(True)
        self.gb_setting.setLayout(self.vbox2)
        # PAPERFORMAT
        paper_Label = QLabel("Paper size:")
        # FIT
        fit_to_size_Label = QLabel("Paper size:")
        self.fit_to_size = QCheckBox('Fit to page', self)
        # # SIDES
        self.lp_two_sided = QCheckBox('two-sided', self)
        self.lp_two_sided.toggled.connect(self.togle_btn)
        self.lp_two_sided.move(20, 20)
        # ORIENTATION L/T
        self.btn_orientation = QPushButton()
        self._icon = QIcon()
        self._icon.addPixmap(QPixmap('icons/long.png'))
        self.btn_orientation.setCheckable(True)
        self.btn_orientation.setIcon(self._icon)
        self.btn_orientation.setIconSize(QSize(23, 38))
        self.btn_orientation.setChecked(True)
        self.btn_orientation.setVisible(False)
        self.btn_orientation.toggled.connect(lambda: self.icon_change('icons/long.png', 'icons/short.png', self.btn_orientation))
        # COLLATE
        self.btn_collate = QPushButton()
        self._icon_collate = QIcon()
        self._icon_collate.addPixmap(QPixmap('icons/collate_on.png'))
        self.btn_collate.setIcon(self._icon_collate)
        self.btn_collate.setCheckable(True)
        self.btn_collate.setIconSize(QSize(23, 38))
        self.btn_collate.setChecked(True)
        self.btn_collate.toggled.connect(lambda: self.icon_change('icons/collate_on.png', 'icons/collate_off.png', self.btn_collate))
        # # COLORS
        btn_colors_Label = QLabel("Color:")
        self.btn_colors = QComboBox(self)
        self.btn_colors.addItem('Auto')
        self.btn_colors.addItem('Color')
        self.btn_colors.addItem('Gray')
        self.vbox2.addWidget(copies_Label, 0, 0)
        self.vbox2.addWidget(self.copies, 0, 1)
        self.vbox2.addWidget(btn_colors_Label, 0, 2)
        self.vbox2.addWidget(self.btn_colors, 0, 3)
        self.vbox2.addWidget(self.btn_collate, 0, 5)
        self.vbox2.addWidget(self.lp_two_sided, 1,0)
        self.vbox2.addWidget(self.btn_orientation, 1, 1)
        self.vbox2.addWidget(self.fit_to_size, 1, 3)
        self.printer_layout.addWidget(self.gb_setting)

    def open_cups_page(self):
        printer_name = self.printer_tb.currentText()  # Získání aktuálně vybrané tiskárny
        printer_presets = self.printer_presets.currentText()  # Získání aktuálně vybrané tiskárny
        url = f"http://localhost:631/printers/{printer_name}"
        
        # Zkontrolujte, zda je klávesa Alt stisknuta
        if QApplication.keyboardModifiers() == Qt.KeyboardModifier.AltModifier:
            webbrowser.open(url)  # Otevření URL ve výchozím webovém prohlížeči
    
        try:
            # Získání podrobností o tiskárně
            command = f"lpoptions -p {printer_name} -l -o  {printer_presets} "
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.d_writer(result.stdout, 1, 'white')
            else:
                self.d_writer(result.stderr, 1, 'white')  # Opraveno na stderr pro chybové zprávy
        except Exception as e:
            print(f"An error occurred: {e}")
            self.d_writer(str(e), 1, 'white')  # Zpracování výjimek
        except Exception as e:
            print(f"An error occurred: {e}")

    def on_printer_changed(self, index):
        printer_name = self.printer_tb.itemText(index)  # Získání názvu tiskárny podle indexu
        self.update_printer_presets(printer_name, self.preferences.get("printer_presets"))
    
    def update_printer_presets(self, printer_name, pref_l_printer_presets):
        # Získání seznamu presetů pro vybranou tiskárnu
        presets = pref_l_printer_presets.get(f'com.apple.print.custompresets.forprinter.{printer_name}.plist', [])
        self.printer_presets.clear()
    
        if presets:
            # Pokud existují presetů, přidejte "Default Setting" jako první položku
            self.printer_presets.addItem("Default Setting")  # Přidání "Default Setting"
            self.printer_presets.addItems(presets)  # Přidání ostatních presetů
        else:
            # Pokud nejsou žádné presetů, přidejte pouze "Default Setting"
            self.printer_presets.addItem("Default Setting")

    def color_box_change(self, text):
        self.d_writer(text, 0)
        return text

    def togle_btn(self):
        if self.lp_two_sided.isChecked():
            self.btn_orientation.setVisible(True)
        else:
            self.btn_orientation.setVisible(False)

    def icon_change(self, _on, _off, name):
        # print (name.isChecked())
        if name.isChecked():
            self._icon = QIcon()
            self._icon.addPixmap(QPixmap(_on))
            name.setIcon(self._icon)
        else:
            self._icon = QIcon()
            self._icon.addPixmap(QPixmap(_off))
            name.setIcon(self._icon)

# TOD UPDATE PDF
    def rotator(self, angle):
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            filename = index.sibling(items.row(), 1).data()
            filetype = index.sibling(items.row(), 3).data()
            filepath = index.sibling(items.row(), 8).data()
            pages = int(index.sibling(items.row(), 5).data())
            if filetype == 'pdf':
                pdf_in = open(filepath, 'rb')
                pdf_reader = PdfReader(pdf_in)
                pdf_writer = PdfWriter()
                for pagenum in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[pagenum]
                    page.rotate_clockwise(angle)
                    pdf_writer.add_page(page)
                pdf_out = open(filepath + '_temp', 'wb')
                pdf_writer.write(pdf_out)
                pdf_out.close()
                pdf_in.close()
                os.rename(filepath + '_temp', filepath)
                self.files = pdf_update(self, filepath, row)
                self.reload(row)
            else:
                command, outputfiles = rotate_this_image([filepath], angle)
                self.files = update_img(self, outputfiles, row)
                self.reload(row)
            self.d_writer(filename + ' / angle: ' + str(angle), 1, 'green')

    def table_print(self):
        green_ = (QColor(80, 80, 80))
        black_ = (QBrush(QColor(0, 0, 0)))
        outputfiles = []
        if self.table.currentItem() == None:
            QMessageBox.information(self, 'Error', 'Choose file to print', QMessageBox.StandardButton.Ok)
            return
        if self.printer_tb.currentText() == None:
            QMessageBox.information(self, 'Error', 'Choose printer!', QMessageBox.StandardButton.Ok)
            return 
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            file_path = index.sibling(items.row(), 8).data()
            outputfiles.append(file_path)
            tiskarna_ok = self.printer_tb.currentText()
        debugstring = print_this_file(self, outputfiles, tiskarna_ok, self.lp_two_sided.isChecked(), self.btn_orientation.isChecked(), str(self.copies.value()), self.fit_to_size.isChecked(), self.btn_collate.isChecked(), self.btn_colors.currentText(), self.printer_presets.currentText())
        self.d_writer('Printing setting: ', 0, 'green')
        self.d_writer(debugstring, 1, 'white')

# def print_this_file(outputfiles, printer, lp_two_sided, orientation, copies, p_size, fit_to_size, collate, colors):



    def open_tb(self):
        green_ = (QColor(80, 80, 80))
        black_ = (QBrush(QColor(0, 0, 0)))
        outputfiles = []
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            file_path = index.sibling(items.row(), 8).data()
            outputfiles.append(file_path)
        revealfile(outputfiles, '')
        self.d_writer('Opened: ' + str(outputfiles), 0, 'green')

    def open_printer_tb(self):
        printer_ = self.printer_tb.currentText()
        open_printer(printer_)
        self.d_writer('Printing setting: ' + printer_, 0, 'green')

    def invertor(self):
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            filename = index.sibling(items.row(), 1).data()
            filetype = index.sibling(items.row(), 3).data()
            filepath = index.sibling(items.row(), 8).data()
            pages = int(index.sibling(items.row(), 5).data())
            command, outputfiles = invert_this_image([filepath])
            self.files = update_img(self, outputfiles, row)
            self.reload(row)
            self.d_writer(filename + '.' + filetype + ' / colors inverted', 'green')

    def add_pager(self):
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            filename = index.sibling(items.row(), 1).data()
            filepath = index.sibling(items.row(), 8).data()
            if self.selected_file_check() == 'pdf':
                debugstring, outputfiles = append_blankpage(filepath)
                self.files = pdf_update(self, filepath, row)
                self.reload(row)
                self.d_writer('fixed pages on:' + str(outputfiles), 1, 'green')
            else:
                print('not pdf')

    def get_page_size(self):
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            size = index.sibling(items.row(), 2).data()
            filename = index.sibling(items.row(), 1).data()
            filetype = index.sibling(items.row(), 3).data()
            filepath = index.sibling(items.row(), 8).data()
            pages = int(index.sibling(items.row(), 5).data())
        try:
            if not self.gb_preview.isHidden():
                self.image_label.show()
                self.labl_name.setText(filename + '.' + filetype)
                if filetype.upper() in (name.upper() for name in image_ext):
                    image_info = file_info_new(filepath.split(','), 'image')
                    self.infotable.setText(image_info)
                    self.image_label_pixmap = QPixmap(filepath)
                    self.image_label.setPixmap(self.image_label_pixmap)
                if filetype == 'pdf':
                    # print ('xxx')
                    # print (type(pages))
                    # print (pages)
                    if pages > 1:
                        self.move_page.show()
                        self.move_page.setMaximum(pages)
                        self.connect_signal()
                    pdf_info = file_info_new(filepath.split(','), 'pdf')
                    self.infotable.setText(' '.join(pdf_info))
                    filebytes = pdf_preview_generator(filepath, generate_marks=1, page=0)
                    self.image_label_pixmap.loadFromData(filebytes)
                    self.image_label.setPixmap(self.image_label_pixmap)
                w, h = self.image_label_pixmap.width(), self.image_label_pixmap.height()
                w_l, h_l = self.image_label.width(), self.image_label.height()
                # Change box according to aspect ratio...
                self.image_label.setFixedHeight(325)
                self.image_label.setPixmap(self.image_label_pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio))
                height_ = self.image_label_pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio).height() - 325
                self.infotable.setFixedHeight(210 - height_ - 30)
                self.image_label.setMinimumSize(1, 1)
                # change with of info
                self.labl_name.setText(filename + '.' + filetype)
                # if size[-2:] == 'px':
                #     papers[5] = 'not supported'
                # else: 
                #     papers[5] = size[:-3]
                #     self.papersize.clear()
                # for items in papers:
                #     self.papersize.addItem(items)
                # self.papersize.update()
        except Exception as e:
            print (e)
            self.infotable.clear()
            self.image_label.clear()
            self.labl_name.setText('No file selected')

    # make simpler later
    @pyqtSlot(int)
    def move_page_changed(self, value):
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            index = (self.table.selectionModel().currentIndex())
            size = index.sibling(items.row(), 2).data()
            filename = index.sibling(items.row(), 1).data()
            filepath = index.sibling(items.row(), 8).data()
        pdf_info = file_info_new(filepath.split(','), 'pdf')
        self.infotable.setText(' '.join(pdf_info))
        filebytes = pdf_preview_generator(filepath, generate_marks=1, page=value)
        self.image_label_pixmap.loadFromData(filebytes)
        self.image_label.setPixmap(self.image_label_pixmap)
        w, h = self.image_label_pixmap.width(), self.image_label_pixmap.height()
        w_l, h_l = self.image_label.width(), self.image_label.height()
        self.image_label.setPixmap(self.image_label_pixmap.scaled(self.image_label.size(), Qt.AspectRatioMode.KeepAspectRatio))

    def connect_signal(self):
        self.move_page.valueChanged.connect(self.move_page_changed)

    def deleteClicked(self):
        rows_ = [] 
        for items in sorted(self.table.selectionModel().selectedRows()):
            row = items.row()
            rows_.append(row)
        rows_.reverse()
        for items in rows_:
            remove_from_list(self, items)
            del(self.files[items])
        Window.table_reload(self, self.files)

    def openFileNamesDialog(self):
        options = QFileDialog.Option.DontUseNativeDialog  # Přidání této možnosti pro platformní nezávislost
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        soubory, _ = QFileDialog.getOpenFileNames(self, "Vyberte soubory", desktop_path,"Všechny soubory (*)", options=options)
        if soubory:
            self.files = pdf_parse(self, soubory)
            self.table_reload(self.files)

    def select_all_action(self):
        self.table.clearSelection()
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        for row in range(self.table.rowCount()):
            self.table.selectRow(row)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

    def clear_table(self):
        """Vymaže všechny řádky v tabulce."""
        self.table.setRowCount(0)  # Nastaví počet řádků na 0

    def reload(self, row):
        self.table_reload(self.files)
        self.table.clearSelection()
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.table.selectRow(row)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setApplicationName("PrintManager") 
    app.setApplicationDisplayName("PrintManager")
    path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'icons/printer.png')
    app.setWindowIcon(QIcon(path))
    w = Window()
    darkmode()
    w.d_writer('DEBUG:', 0, 'green')
    log = ('boot time: ' + str((time.time() - start_time))[:5] + ' seconds' + '\n' + ' CUPS: ' + "yes" if is_cups_running() == 1 else "no")
    w.d_writer(log, 1)
    w.showNormal()
    sys.exit(app.exec())