# epub2images
Converts `.epub` files to a series of `.png` images for use with custom e-readers.

## Requirements
Must have [Calibre](https://calibre-ebook.com/) installed, including having a development environment for it set up (see [Becoming a calibre developer](https://calibre-ebook.com/get-involved)). Test to see if your environment is properly set up by running the terminal command `ebook-convert`.

Download the necessary Python packages by running `pip install -r requirements.txt` in the base directory.

## Usage
Once all the necessary Python packages are installed and the Calibre environment is set up, the script can be used from the command line by typing

`python epub2images.py <path_to_epub>.epub`

Once the script is done running, the series of images are numbered sequentially and output to `./output/<name_of_epub>/`. The intermediate `.pdf` file is also generated and can be found under `./input/<name_of_epub>.pdf`. Enter `python epub2images.py -h` to see other possible command line arguments.

## Caveats
I developed the script for use with my homebrew e-reader that uses a [Waveshare 7.5" e-ink display](https://www.waveshare.com/product/7.5inch-e-paper.htm) with their [ESP32 platform](https://www.waveshare.com/e-paper-esp32-driver-board.htm). I added a microSD card to which I can upload these images, thereby allowing me to send an image display command to the e-ink display using the generated `.png`s. As such, the pipeline has been tailored to this 480x800 display. I made a custom Output Profile for Calibre called `waveshare_eink_large` by copying and editing the `GenericEinkLarge` class found in Calibre's [`profiles.py`](https://github.com/kovidgoyal/calibre/blob/master/src/calibre/customize/profiles.py) -- not forgetting to add it to the `output_profiles` list at the bottom of the file.

This is all to say, that particular part of the pipeline in [`epub2images.py`](https://github.com/mchartigan/epub2images/epub2images.py) won't work for you unless you do the same. I've provided my version of the file for convenience under `./calibre/customize/profiles.py`; just copy and paste it into the appropriate directory in your Calibre development environment, overwriting the old version. This can also be edited to fit different output resolutions if your screen is different; just make your own Output Profile and save the file, as once your Calibre development environment is set up it runs using the repository code rather than the compiled stuff you initially downloaded. Then, copy the `waveshare_opts()` function in `epub2images.py` and edit the `--output-profile=` argument to reference your own. 

Also, I use [Atkinson Hyperlegible](https://fonts.google.com/specimen/Atkinson+Hyperlegible) currently as the font, as well as Ubuntu Mono for monospaced text, so you'll need to download those to your system if you want to use them. Or just change `--pdf-serif-family=` and `--pdf-sans-family=` to Tahoma or something.
