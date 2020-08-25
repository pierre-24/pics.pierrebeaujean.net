# --- Base
temporary_build_directory = 'build'
destination_directory = 'html'

# --- Seeker
images_source = 'pictures'
images_extensions = ['jpg', 'JPG', 'jpeg', 'JPEG']

# Import custom settings, if any
try:
    from settings import *
except ImportError:
    pass
