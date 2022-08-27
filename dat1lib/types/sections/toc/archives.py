import dat1lib.types.sections
import io
import struct

class ArchiveFileEntry(object):
	def __init__(self, data):
		self.install_bucket, self.chunkmap = struct.unpack("<II", data[:8])
		self.filename = data[8:]

	@classmethod
	def make(cls, bucket, chunk, filename):
		data = struct.pack("<II", bucket, chunk)
		f = io.BytesIO()
		f.write(data)
		f.write(filename)
		if len(filename) < 64:
			f.write('\0' * (64 - len(filename)))
		f.seek(0)
		return cls(f.read())

class ArchivesSection(dat1lib.types.sections.Section):
	TAG = 0x398ABFF0
	TYPE = 'toc'

	def __init__(self, data):
		dat1lib.types.sections.Section.__init__(self, data)

		ENTRY_SIZE = 72
		count = len(data)//ENTRY_SIZE
		self.archives = [ArchiveFileEntry(data[i*ENTRY_SIZE:(i+1)*ENTRY_SIZE]) for i in xrange(count)]

	def save(self):
		of = io.BytesIO(bytes())
		for e in self.archives:
			of.write(struct.pack("<II", e.install_bucket, e.chunkmap))
			of.write(e.filename)
		of.seek(0)
		return of.read()

	def get_short_suffix(self):
		return "archives ({})".format(len(self.archives))

	def print_verbose(self, config):
		##### "{:08X} | ............ | {:6} ..."
		print "{:08X} | Archives Map | {:6} entries".format(self.TAG, len(self.archives))
