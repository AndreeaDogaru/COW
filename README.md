# Customizable Open Webcam

Take control of your webcam with a selection of user-friendly customizable features.

![Demo](demo.gif)

## Features
The features are built to work in a plugin format, so new features can effortlessly be incorporated.
Customizable Open Webcam plugins:

- [x] Virtual Background
- [x] Image Adjustments
- [x] FPS Display
- [x] Reactions
- [x] Screen Share
- [x] Record
- [ ] Video Filters

## Installation
1. Clone this repository.
    ```
    git clone https://github.com/AndreeaDogaru/COW.git
    cd COW
    ```

2. Prepare python environment using [Anaconda](https://www.anaconda.com/products/individual).
   A ready to use [environment](environment.yml) is provided.
    ```
    conda env create -f environment.yml
    conda activate cow
    ```

3. Install  **v4l2loopback**.
    ```
    sudo apt install v4l2loopback-dkms
    sudo apt install v4l-utils
    ```
4. Download resources.
    ```
    cd source
    bash download.sh
    ```
5. Run the application.
    ```
    python gui.py
    ```

## Compatibility
The Customizable Open Webcam can be used on Linux-based systems (tested on Ubuntu 20.04+) by:
- Zoom
- Mozilla Firefox
- Chromium
- Google Chrome
- Other software
