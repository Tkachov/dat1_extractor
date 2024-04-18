# ALERT: Amazing Luna Engine Research Tools
# This program is free software, and can be redistributed and/or modified by you. It is provided 'as-is', without any warranty.
# For more details, terms and conditions, see GNU General Public License.
# A copy of the that license should come with this program (LICENSE.txt). If not, see <http://www.gnu.org/licenses/>.

import dat1lib
import dat1lib.types.model
import dat1lib.types.sections.model.geo
import dat1lib.types.sections.model.look
import dat1lib.types.sections.model.meshes
import dat1lib.types.sections.model.unknowns
import dat1lib.utils as utils
import io
import server.mtl_writer

SECTION_INDEXES   = dat1lib.types.sections.model.geo.IndexesSection.TAG
SECTION_VERTEXES  = dat1lib.types.sections.model.geo.VertexesSection.TAG
SECTION_LOOK      = dat1lib.types.sections.model.look.ModelLookSection.TAG
SECTION_MESHES    = dat1lib.types.sections.model.meshes.MeshesSection.TAG
SECTION_BUILT     = dat1lib.types.sections.model.unknowns.ModelBuiltSection.TAG
SECTION_MATERIALS = dat1lib.types.sections.model.unknowns.ModelMaterialSection.TAG

class ObjHelper(object):
	def __init__(self):
		self.cur_vertex_offset = 1
		self.current_material = None
		self.mesh_vertexes = 0
		self.remembered_vertexes = []

		self.meshes_count = 0

		self.f = io.BytesIO(bytes())
		self.uv_scale = 1.0/16384.0

	#

	def write(self, s):
		self.f.write(s.encode('ascii'))

	def start_mesh(self, mesh_name):
		self.mesh_vertexes = 0
		self.write("o {:02}_{}\n".format(self.meshes_count, mesh_name))
		self.meshes_count += 1

	def end_mesh(self):
		self.cur_vertex_offset += self.mesh_vertexes

	def write_vertex(self, v, uv):
		def transform(x, y, z):
			return (x, y, z)

		x, y, z = v.x, v.y, v.z
		x, y, z = transform(x, y, z)
		self.write("v {} {} {}\n".format(x, y, z))
		self.mesh_vertexes += 1

		uu, vv = v.u * self.uv_scale, 1.0 - v.v * self.uv_scale
		if uv is not None:
			uu, vv = uv
			uu = uu * self.uv_scale
			vv = 1.0 - vv * self.uv_scale

		self.write("vt {} {}\n".format(uu, vv))

	def usemtl(self, mat):
		if mat != self.current_material:
			self.write("usemtl {}\n".format(mat))
			self.current_material = mat

	def write_poly(self, vs):
		self.write("f {}/{} {}/{} {}/{}\n".format(
			vs[2] + self.cur_vertex_offset, vs[2] + self.cur_vertex_offset,
			vs[1] + self.cur_vertex_offset, vs[1] + self.cur_vertex_offset,
			vs[0] + self.cur_vertex_offset, vs[0] + self.cur_vertex_offset
		))

	def get_output(self):
		self.f.seek(0)
		return self.f

	#

	def write_model(self, model, looks, lod):
		mode = dat1lib.VERSION_RCRA
		if not isinstance(model, dat1lib.types.model.ModelRcra):
			mode = dat1lib.VERSION_MSMR

		if mode != dat1lib.VERSION_RCRA: # TODO: test RCRA
			s = None if model is None else model.dat1.get_section(SECTION_BUILT)
			if s:
				uv_scale = s.get_uv_scale()

		#

		s = model.dat1.get_section(SECTION_MESHES)
		meshes = s.meshes

		s = model.dat1.get_section(SECTION_VERTEXES)
		vertexes = s.vertexes

		s = model.dat1.get_section(SECTION_INDEXES)
		indexes = s.values

		uvs = model.dat1.get_section(0x16F3BA18) # SO UVs

		materials_section = model.dat1.get_section(SECTION_MATERIALS)

		looks_section = model.dat1.get_section(SECTION_LOOK)

		def get_material_name(mesh):
			mat = mesh.get_material()
			return server.mtl_writer.get_material_name(mat, model.dat1, materials_section)

		#

		# pizza B3D0E63D7EA1F3E8
		# body 878B7EEABDC354A2

		meshes_to_display = set()
		for look in looks:
			look_lod = looks_section.looks[look].lods[lod]
			meshes_to_display |= set(range(look_lod.start, look_lod.start + look_lod.count))

		for i, mesh in enumerate(meshes):
			if i not in meshes_to_display:
				continue

			matname = get_material_name(mesh)
			self.start_mesh("mesh{:02}_{}".format(i, matname))
			self.usemtl(matname)

			for vi in range(mesh.vertexStart, mesh.vertexStart + mesh.vertexCount):
				v = vertexes[vi]
				uv = None if uvs is None else uvs.get_uv(vi)
				self.write_vertex(v, uv)

			#

			relative_indexes = ((mesh.get_flags() & 0x10) == 0)

			faces_count = mesh.indexCount // 3
			for j in range(faces_count):
				index_index = mesh.indexStart + j*3
				
				a, b, c = indexes[index_index+2], indexes[index_index+1], indexes[index_index]
				if relative_indexes:
					a -= mesh.vertexStart
					b -= mesh.vertexStart
					c -= mesh.vertexStart

				self.write_poly([a, b, c])

			self.end_mesh()

###

def write(model, looks, lod):
	helper = ObjHelper()
	helper.write_model(model, looks, lod)
	return helper.get_output()
