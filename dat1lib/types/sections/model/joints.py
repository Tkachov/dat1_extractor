import dat1lib.crc32 as crc32
import dat1lib.types.sections
import io
import struct

class JointsMapSection(dat1lib.types.sections.UintUintMapSection):
	TAG = 0xEE31971C # Model Joint Lookup
	TYPE = 'model'

	def __init__(self, data, container):
		dat1lib.types.sections.UintUintMapSection.__init__(self, data, container)

		# MSMR
		# 2311 occurrences in 38298 files
		# size = 16..25416 (avg = 458.6)
		#
		# examples: 800804287BB19C92 (min size), BBCAFC4308D39DEC (max size)

		# MM
		# 2004 occurrences in 37147 files
		# size = 16..25072 (avg = 384.9)
		#
		# examples: 800B08BE9B0E1249 (min size), B699EAFFCD4834D0 (max size)

	def get_short_suffix(self):
		return "joints map ({})".format(len(self._map))

	def print_verbose(self, config):
		##### "{:08X} | ............ | {:6} ..."
		print("{:08X} | Joints Map   | {:6} joints".format(self.TAG, len(self._map)))

	def web_repr(self):
		return {"name": "Model Joint Lookup", "type": "text", "readonly": True, "content": "(see 15DF9D3B for index/hash mapping)"}

###

class JointDefinition(object):
	def __init__(self, data):
		self.parent, self.index, self.unknown1, self.unknown2, self.hash, self.string_offset = struct.unpack("<hHHHII", data)
		# hash = crc32(name, normalize=False), that is, without lower() (which, however, is used for material names)
		# parent is -1 if none
		# unknown1 is amount of "children" (not only direct, but all in hierarchy) of this joint?
		# unknown2 some flags? type of joint?

class JointsSection(dat1lib.types.sections.Section):
	TAG = 0x15DF9D3B # Model Joint
	TYPE = 'model'

	def __init__(self, data, container):
		dat1lib.types.sections.Section.__init__(self, data, container)

		# MSMR
		# 2311 occurrences in 38298 files
		# size = 16..50816 (avg = 901.2)
		#
		# examples: 800804287BB19C92 (min size), BBCAFC4308D39DEC (max size)

		# MM
		# 2004 occurrences in 37147 files
		# size = 16..50128 (avg = 753.9)
		#
		# examples: 800B08BE9B0E1249 (min size), B699EAFFCD4834D0 (max size)

		ENTRY_SIZE = 16
		count = len(data)//ENTRY_SIZE
		self.joints = [JointDefinition(data[i*ENTRY_SIZE:(i+1)*ENTRY_SIZE]) for i in range(count)]

	def get_short_suffix(self):
		return "joints ({})".format(len(self.joints))

	def print_verbose(self, config):
		##### "{:08X} | ............ | {:6} ..."
		print("{:08X} | Joint Defs   | {:6} joints".format(self.TAG, len(self.joints)))

		print("")
		#######........ | 123  12345678  12345678901234567890123456789012  1234  1234  1234  1234
		print("           #        hash  name                            parent   ndx     ?     ?")
		print("         -------------------------------------------------------------------------")
		for i, l in enumerate(self.joints):
			name = self._dat1.get_string(l.string_offset)

			print("         - {:<3}  {:08X}  {}{}  {:4}  {:4}  {:4}  {:4}".format(i, l.hash, name[:32], " "*(32 - len(name[:32])), l.parent, l.index, l.unknown1, l.unknown2))
			if config.get("section_warnings", True):
				nhsh = crc32.hash(name, False)
				if nhsh != l.hash:
					print("        [!] name real hash {:08X} is not equal to one written in the struct {:08X}".format(nhsh, l.hash))

		print("")
