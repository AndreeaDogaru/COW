# Contributing

Thank you for your interest in contributing to this project! 
Before you begin writing code, it is important that you share your intention to contribute:

* If you would like to propose and implement a new feature, post about it an [issue](https://github.com/AndreeaDogaru/COW/issues) so we can discuss the design and implementation.
* If you would like to implement a feature or solve a bug, choose one in the [issue](https://github.com/AndreeaDogaru/COW/issues) list and comment that you'd like to work on it.

## Issues

Issues are very valuable to this project.

* Ideas are a valuable source of contributions others can make
* Problems show where this project is lacking
* With a question you show where contributors can improve the user experience

## Development environment 

1. Prepare python environment using [Anaconda](https://www.anaconda.com/products/individual).
```
conda create -n cow python=3.7
conda activate cow
conda install -c conda-forge opencv 
pip install pyfakewebcam
```

2. Install  **v4l2loopback**.
```
sudo apt install v4l2loopback-dkms
```
