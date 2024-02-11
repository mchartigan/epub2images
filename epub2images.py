import sys
from subprocess import run
from pathlib import Path
from argparse import ArgumentParser
from pdf2image import convert_from_path
from PIL import ImageOps
from math import floor


def waveshare_opts(fontsize: int=8, margins: int=5) -> str:
    '''
    Returns command line options string to input to ebook-convert, tailored to
    the Waveshare 7.5" e-ink display.

    :param fontsize: font size, in px
    :param margins: margin size, in pt
    :return:
        String of command line options
    '''

    opts = ('--input-profile=default --output-profile=waveshare_eink_large '
        '--use-profile-size --preserve-cover-aspect-ratio '
        '--pdf-serif-family="Atkinson Hyperlegible" --pdf-sans-family="Atkinson Hyperlegible" '
        '--pdf-mono-family="Ubuntu Mono" '
        f'--pdf-default-font-size={fontsize} --pdf-mono-font-size={fontsize} '
        f'--pdf-page-margin-top={margins} --pdf-page-margin-bottom={margins} '
        f'--pdf-page-margin-left={margins} --pdf-page-margin-right={margins}')
    return opts

def printProgressBar (iteration: int, total: int, prefix: str='Progress:', suffix: str='Complete',
                       decimals: int=1, length: int=100, fill: str='█', printEnd: str="\r") -> None:
    '''
    Call in a loop to create terminal progress bar

    :param iteration: current iteration
    :param total    : total iterations
    :param prefix   : prefix string
    :param suffix   : suffix string
    :param decimals : positive number of decimals in percent complete
    :param length   : character length of bar
    :param fill     : bar fill character
    :param printEnd : end character (e.g. "\r", "\r\n")
    '''

    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()

def main(args: list[str]=sys.argv) -> int:
    '''
    Main script called from command line to convert EPUB to series of images

    :param args: Command-line arguments; only accepts 1 for file path to EPUB
    :return:
        Error code for sys.exit()
    '''

    # create parser for dealing with command-line arguments
    parser = ArgumentParser(description=('Convert .epub files into a series of images '
        'formatted for display on e-readers.'))
    parser.add_argument('epub_path', type=str, nargs=1, help='path to .epub file')
    parser.add_argument('-f', '--fontsize', type=int, nargs='?', default='8', help='font size, in px')
    parser.add_argument('-m', '--margins', type=int, nargs='?', default='5', help='margin size, in pt')
    args = parser.parse_args(args[1:])
    
    fname_stem = Path(args.epub_path[0]).stem
    pdf_path = f'./input/{fname_stem}.pdf'
    opts = waveshare_opts(fontsize=args.fontsize, margins=args.margins)
    
    # Convert EPUB to PDF using Calibre CLI
    print('Converting EPUB to PDF using Calibre... ')
    run(f'ebook-convert "{args.epub_path[0]}" "{pdf_path}" {opts}')
    print('Done.')

    # Convert PDF to Image objects
    print('Converting PDF to images... ')
    images = convert_from_path(pdf_path, size=(480,800))
    print('Done.')

    # Save images to output/bookname/*.jpg
    dirname = f'./output/{fname_stem}/'
    Path(dirname).mkdir(parents=True, exist_ok=True)
    l = len(images)
    wid = 100

    print(f'Saving images to {dirname}... ')
    # Initial call to print 0% progress
    printProgressBar(0, wid, decimals=0, length=50)
    j = 0                                   # don't update bar every iteration
    for i, img in enumerate(images):
        img = img.crop((0,0,480,800))       # sometimes images are 481 x 800 or smth
        im_grey = ImageOps.grayscale(img)   # convert image to greyscale for e-ink
        im_grey.save(dirname + f'{i:06d}.png')
        # Update Progress Bar only after an appreciable time has passed
        if floor(i / l * wid) > j:
            j = floor(i / l * wid)
            printProgressBar(j, wid, decimals=0, length=50)

    print(f'PDF successfully converted. Output can be found in {dirname}.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
