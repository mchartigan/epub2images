import sys
from subprocess import run
from pathlib import Path
from argparse import ArgumentParser
from pdf2image import convert_from_path
from PIL import Image
import numpy as np
from math import floor

floyd_steinberg = 1/16 * np.array([[0,0,7],[3,5,1]])
stucki = 1/42 * np.array([[0,0,0,8,4],[2,4,8,4,2],[1,2,4,2,1]])
atkinson = 1/8 * np.array([[0,0,0,1,1],[0,1,1,1,0],[0,0,1,0,0]])

def waveshare_opts(fontsize: int=8, margins: int=5) -> str:
    '''
    Returns command line options string to input to ebook-convert, tailored to
    the Waveshare 7.5" e-ink display.

    :param fontsize: font size, in px
    :param margins: margin size, in pt
    :return:
        String of command line options
    '''

    opts = ('-d --input-profile=default --output-profile=waveshare_eink_large '
        '--use-profile-size --preserve-cover-aspect-ratio '
        '--pdf-serif-family="Atkinson Hyperlegible" --pdf-sans-family="Atkinson Hyperlegible" '
        '--pdf-mono-family="Ubuntu Mono" '
        f'--pdf-default-font-size={fontsize} --pdf-mono-font-size={fontsize} '
        f'--pdf-page-margin-top={margins} --pdf-page-margin-bottom={margins} '
        f'--pdf-page-margin-left={margins} --pdf-page-margin-right={margins}')
    return opts

def dither(px: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    '''
    Uses an error diffusion algorithm defined by matrix to dither px.

    :param px: numpy array of greyscale image pixel values
    :param matrix: error diffusion matrix (odd number of cols)
    :return:
        black-and-white dithered version of px
    '''

    px = px / 255
    mid = int(matrix.shape[1] / 2)  # middle index of matrix
    
    for i in range(0,px.shape[0]):
        for j in range(0,px.shape[1]):
            old = px[i,j]
            px[i,j] = round(old)
            err = old - px[i,j]
            loj = max(0, j - mid)    # low index of matrices
            hij = min(px.shape[1], j + mid + 1)
            hii = min(px.shape[0], i + matrix.shape[0])
            px[i:hii,loj:hij] += err * matrix[0:hii-i,mid+loj-j:mid+hij-j]

    return px * 255

          
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
    parser.add_argument('-d', '--dither', action='store_true', help='dither images in EPUB (must provide EPUB)')
    parser.add_argument('--png', action='store_true', help='save images as PNG instead of binary')
    args = parser.parse_args(args[1:])
    
    # catch if string is not file
    if not Path(args.epub_path[0]).is_file():
        print('Path to file provided is not accessible.')
        return 1
    
    epub_path = args.epub_path[0]
    fname_stem = Path(epub_path).stem
    
    # check file extension
    if args.epub_path[0].endswith("epub"):  # if epub, convert to pdf
        pdf_path = f'./input/{fname_stem}.pdf'
        opts = waveshare_opts(fontsize=args.fontsize, margins=args.margins)
        
        # Convert EPUB to PDF using Calibre CLI
        print('Converting EPUB to PDF using Calibre... ')
        run(f'ebook-convert "{epub_path}" "{pdf_path}" {opts}')
        print('Done.')
    elif epub_path.endswith("pdf"):         # if pdf, move on
        print('PDF provided.')
        pdf_path = epub_path
    else:                                   # if neither, error
        print('Invalid filetype provided!')
        return 1

    # Convert PDF to Image objects
    print('Converting PDF to images... ')
    images = convert_from_path(pdf_path, size=(480,800), grayscale=True)
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
        # rotate for display, then crop -- sometimes images are 481 x 800 or smth
        img = img.rotate(90, expand=True).crop((0,0,800,480))
        # convert image to b/w (w/ dithering) for e-ink
        # if args.dither:
        #     data = np.array(img)
        #     img = Image.fromarray(dither(data, atkinson))
        im_bw = img.convert('1', dither=1 if args.dither else 0)

        if args.png:                        # write to PNG if desired
            im_bw.save(dirname + f'{i:06d}.png')
        else:                               # write to byte stream
            with open(dirname + f'{i:06d}', 'wb') as file:
                file.write(im_bw.tobytes())
        # Update Progress Bar only after an appreciable time has passed
        if floor(i / l * wid) > j:
            j = floor(i / l * wid)
            printProgressBar(j, wid, decimals=0, length=50)

    if not args.png:
        with open(dirname + 'HEAD', 'w') as file:
            file.write(f'{0:06d} {i:06d}')

    print(f'PDF successfully converted. Output can be found in {dirname}.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
