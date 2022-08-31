import dat1lib.crc32 as crc32
import dat1lib.types.sections
import io
import struct

class LocatorsMapSection(dat1lib.types.sections.UintUintMapSection): # aka model_locator_lookup
	TAG = 0x731CBC2E
	TYPE = 'model'

	def __init__(self, data, container):
		dat1lib.types.sections.UintUintMapSection.__init__(self, data, container)

	def get_short_suffix(self):
		return "locators map ({})".format(len(self._map))

	def print_verbose(self, config):
		##### "{:08X} | ............ | {:6} ..."
		print "{:08X} | Locators Map | {:6} locators".format(self.TAG, len(self._map))

###

class LocatorDefinition(object):
	def __init__(self, data):
		self.hash, self.string_offset, self.joint, self.zero = struct.unpack("<IIiI", data[:16])
		# hash = crc32(name, normalize=False), that is, without lower() (which, however, is used for material names)
		# joint is -1 if none

		self.matrix = [
			struct.unpack("<fff", data[16:28]),
			struct.unpack("<fff", data[28:40]),
			struct.unpack("<fff", data[40:52]),
			struct.unpack("<fff", data[52:64])
		]
		"""
		1 0 0
		0 1 0
		0 0 1
		0 0 0, for example
		"""

class LocatorsSection(dat1lib.types.sections.Section): # aka model_locator
	TAG = 0x9F614FAB
	TYPE = 'model'

	def __init__(self, data, container):
		dat1lib.types.sections.Section.__init__(self, data, container)

		ENTRY_SIZE = 64
		count = len(data)//ENTRY_SIZE
		self.locators = [LocatorDefinition(data[i*ENTRY_SIZE:(i+1)*ENTRY_SIZE]) for i in xrange(count)]

	def get_short_suffix(self):
		return "locators ({})".format(len(self.locators))

	def print_verbose(self, config):
		##### "{:08X} | ............ | {:6} ..."
		print "{:08X} | Locator Defs | {:6} locators".format(self.TAG, len(self.locators))

		print ""
		#######........ | 123  12345678  12345678901234567890123456789012  1234  1234
		print "           #        hash  name                             joint  zero"
		print "         -------------------------------------------------------------"
		for i, l in enumerate(self.locators):
			name = self._dat1.get_string(l.string_offset)

			print "         - {:<3}  {:08X}  {}{}  {:4}  {:4}".format(i, l.hash, name[:32], " "*(32 - len(name[:32])), l.joint, l.zero)
			if config.get("section_warnings", True):
				nhsh = crc32.hash(name, False)
				if nhsh != l.hash:
					print "        [!] name real hash {:08X} is not equal to one written in the struct {:08X}".format(nhsh, l.hash)

		print ""

###

class LocatorRelatedSection(dat1lib.types.sections.Section):
	TAG = 0x9A434B29
	TYPE = 'model'

	def __init__(self, data, container):
		dat1lib.types.sections.Section.__init__(self, data, container)

		self.size, = struct.unpack("<I", data[:4]) # same as len(data)
		self.unknown1, = struct.unpack("<I", data[4:8]) # always 32?
		self.unknown2, = struct.unpack("<I", data[8:12]) # small
		self.unknown3, = struct.unpack("<I", data[12:16]) # small, approx. *2 of unknown2

		ENTRY_SIZE = 8
		count = (len(data) - 16)//ENTRY_SIZE
		pairs_data = data[16:]
		self.pairs = [struct.unpack("<II", pairs_data[i*ENTRY_SIZE:(i+1)*ENTRY_SIZE]) for i in xrange(count)]

	def get_short_suffix(self):
		return "locators info ({})".format(len(self.pairs))

	def print_verbose(self, config):
		##### "{:08X} | ............ | {:6} ..."
		print "{:08X} | Locator Info | {:6} pairs".format(self.TAG, len(self.pairs))