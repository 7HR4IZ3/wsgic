try:
	from PIL import Image
except ImportError:
	Image = None

from .storage import *

class ImageFile(File):
	def _image(self):
		if Image:
			return Image.open(self.path)
		raise ImportError("Imagefile requires 'pillow' library to use.")
