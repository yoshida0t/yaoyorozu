import numpy as np
import sys 
import pyvista as pv
import argparse

atomic_number_to_symbol = {
    1: "H",   2: "He",
    3: "Li",  4: "Be",  5: "B",   6: "C",   7: "N",   8: "O",   9: "F",   10: "Ne",
    11: "Na", 12: "Mg", 13: "Al", 14: "Si", 15: "P",  16: "S",  17: "Cl", 18: "Ar",
    19: "K",  20: "Ca", 21: "Sc", 22: "Ti", 23: "V",  24: "Cr", 25: "Mn",
    26: "Fe", 27: "Co", 28: "Ni", 29: "Cu", 30: "Zn",
    31: "Ga", 32: "Ge", 33: "As", 34: "Se", 35: "Br", 36: "Kr",
    37: "Rb", 38: "Sr", 39: "Y",  40: "Zr", 41: "Nb", 42: "Mo",
    43: "Tc", 44: "Ru", 45: "Rh", 46: "Pd", 47: "Ag", 48: "Cd",
    49: "In", 50: "Sn", 51: "Sb", 52: "Te", 53: "I",  54: "Xe",
    55: "Cs", 56: "Ba",
    57: "La", 58: "Ce", 59: "Pr", 60: "Nd", 61: "Pm", 62: "Sm",
    63: "Eu", 64: "Gd", 65: "Tb", 66: "Dy", 67: "Ho", 68: "Er",
    69: "Tm", 70: "Yb", 71: "Lu",
    72: "Hf", 73: "Ta", 74: "W",  75: "Re", 76: "Os", 77: "Ir",
    78: "Pt", 79: "Au", 80: "Hg",
    81: "Tl", 82: "Pb", 83: "Bi", 84: "Po", 85: "At", 86: "Rn",
    87: "Fr", 88: "Ra",
    89: "Ac", 90: "Th", 91: "Pa", 92: "U",  93: "Np", 94: "Pu",
    95: "Am", 96: "Cm", 97: "Bk", 98: "Cf", 99: "Es", 100: "Fm",
    101: "Md", 102: "No", 103: "Lr"
}

### args
def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Convert cube to png")

    p.add_argument(
        "-f", "--file",
        required=True,
        metavar="CUBE",
        help="cube file path"
    )
    p.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="show interactive 3D viewer instead of saving PNG"
    )
    p.add_argument(
        "--iso",
        type=float,
        default=0.02,
        metavar="VALUE",
        help="isosurface value for molecular orbital visualization (default: 0.02)"
    )
    
    p.add_argument(
        "-o","--out",
        default="cube_pyvista.png",
        metavar="VALUE",
        help="output name"
    )

    return p.parse_args(argv)

### cube
class Cube:
    def __init__(self,lines):
        self._lines   = lines
        self.comment  = None
        self.atom     = None
        self.center   = None
        self.grid     = None
        self.point    = None
        self.parse()

    @classmethod
    def from_file(cls, path, encoding="utf-8"):
        with open(path, encoding=encoding) as f:
            return cls.from_line(f)

    @classmethod
    def from_line(cls, lines):
        obj = cls(list(lines))
        obj.parse()
        return obj


    def parse(self):
        ft            = self._lines
        self.comment  = ft[:2]

        is_orca = False
        if any("ORCA" in s for s in self.comment):
            is_orca = True

        setting       = ft[2:6]
        bohr2ang      = 0.5291772109
        parts = setting[0].split()
        atom_num = np.abs(int(setting[0].split()[0]))
        self.center = np.array([float(x) for x in parts[1:]]) * bohr2ang
        self.grid = []
        for i in range(3):
            parts = setting[i+1].split()
            gridi = (int(parts[0]), np.array([float(x) for x in parts[1:]])*bohr2ang )
            (self.grid).append(gridi)

        data      = ft[6:atom_num+6] 

        if is_orca:
            pointdata = ft[atom_num+7:] 
        else:
            pointdata = ft[atom_num+6:] 

        #print(pointdata)        
        atoms = []
        coords = []
       
        #print(data)
        for line in data:
            parts = line.split()
            atoms.append(int(parts[0]))
            coords.append([float(parts[2]), float(parts[3]), float(parts[4])])
        
        atoms = [atomic_number_to_symbol[n] for n in atoms]
        coords = np.array(coords)*bohr2ang
        self.atom = (atoms, coords)
        
        self.point = np.array( [float(x) for s in pointdata for x in s.split()],dtype=float)
        

args             = parse_args()
input_file       = args.file 
interactive_mode = args.interactive
iso_value        = args.iso
png_name         = args.out

#surface1 = Cube.from_line(lines)
surface1 = Cube.from_file(input_file)






p = pv.Plotter(off_screen=(not interactive_mode), window_size=(1000, 1000))

# -=-=-=-=-=-=-=-=-=-=-=-=-
#   Visualize orbital 
#

(nx, vx), (ny, vy), (nz, vz) = surface1.grid

coo = (
    np.arange(nx)[:, None, None, None] * vx[None, None, None, :] +
    np.arange(ny)[None, :, None, None] * vy[None, None, None, :] +
    np.arange(nz)[None, None, :, None] * vz[None, None, None, :]
).reshape(-1, vx.shape[0])
coo = coo + surface1.center 



xyz = np.asarray(coo, dtype=np.float64)
val = np.asarray(surface1.point, dtype=np.float64)

x = np.unique(xyz[:, 0])
y = np.unique(xyz[:, 1])
z = np.unique(xyz[:, 2])

nx, ny, nz = len(x), len(y), len(z)
N = xyz.shape[0]
if N != nx * ny * nz:
    raise ValueError("N != nx * ny * nz")

ix = np.searchsorted(x, xyz[:, 0])
iy = np.searchsorted(y, xyz[:, 1])
iz = np.searchsorted(z, xyz[:, 2])


V = np.empty((nx, ny, nz), dtype=np.float64)
V[ix, iy, iz] = val

grid = pv.RectilinearGrid(x, y, z)
grid.point_data["value"] = V.ravel(order="F")


v0 = iso_value 
iso1 = grid.contour(isosurfaces=[v0], scalars="value")
iso2 = grid.contour(isosurfaces=[-1*v0], scalars="value")



p.add_mesh(iso1, opacity=1.0,show_scalar_bar=False,color="yellow")
p.add_mesh(iso2, opacity=1.0,show_scalar_bar=False,color="purple")

#
#
# -=-=-=-=-=-=-=-=-=-=-=-=-




# -=-=-=-=-=-=-=-=-=-=-=-=-
#   Visualize molecule 
#

elems   = surface1.atom[0] 
mol_xyz = surface1.atom[1]
vdw_radius = {
    "H": 1.20, "C": 1.70, "N": 1.55, "O": 1.52, "F": 1.47,
    "P": 1.80, "S": 1.80, "Fe": 1.75, "Br": 1.85, "I": 1.98,
}
default_r = 1.6

atom_scale  = 0.15  # Atomic object scale 
bond_radius = 0.08  # Bond object thickness


# atom 
atom_meshes = []
for elem, pos in zip(elems, mol_xyz):
    r = vdw_radius.get(str(elem), default_r) * atom_scale 
    atom_meshes.append(pv.Sphere(radius=r, center=pos, theta_resolution=24, phi_resolution=24))
for am in atom_meshes:
    p.add_mesh(am)                 




# bond 
### Bond estimation (rough implementation) 
def guess_bond(atom_taple):
    atoms = atom_taple[0]
    coord = atom_taple[1]
    n     = len(atoms)

    bond_rad = {"H": 0.5, "C": 0.8, "N": 0.8, "O": 0.8, "Fe": 1.6}

    bonds = []
    for i in range(n):
        for j in range(i+1, n):
            
            maxlength = bond_rad.get(atoms[i],1.6) + bond_rad.get(atoms[j],1.6) 
            d = np.linalg.norm(coord[i] - coord[j])
            if d <= maxlength:
                bonds.append((i, j))
    return bonds
bonds = guess_bond(surface1.atom)

bond_meshes = []
for i, j in bonds:
    p0, p1 = mol_xyz[i], mol_xyz[j]
    cyl = pv.Cylinder(center=(p0+p1)/2, direction=(p1-p0), radius=bond_radius, height=np.linalg.norm(p1-p0))
    bond_meshes.append(cyl)

for bm in bond_meshes:
    p.add_mesh(bm)                   

#
#
# -=-=-=-=-=-=-=-=-=-=-=-=-







# -=-=-=-=-=-=-=-=-=-=-=-=-
#   Show object 
#

center=np.mean(surface1.atom[1],axis=0)
p.set_focus(center) 


if interactive_mode:
#    p.enable_parallel_projection()
    p.enable_trackball_style()
    p.show()
    print("\ncamera_position at the end of execution.\nYou can fix the camera angle by editing p.camera_position\n")
    print(p.camera_position)
else:
    p.camera_position=[(7.986073289910527, -14.543055869470093, 19.166499945446773),
 (0.00018573121655040894, -0.00027024980315908136, 0.0001476104884140852),
 (-0.29058282751787123, 0.7000761674294138, 0.6522691010227777)]
#    p.camera_position=[(-4.533216685923364, 21.282165428088174, 10.589070801496442),
# (6.249703742776024, 0.5354171287882736, 7.577675870548906),
# (-0.09882152212615747, 0.09245345526433764, -0.9908010220898819)]
    p.show(screenshot=png_name)

#
#
# -=-=-=-=-=-=-=-=-=-=-=-=-
