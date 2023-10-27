from concurrent.futures import ProcessPoolExecutor
from tqdm import tqdm
import numpy as np
import subprocess
import os

feff_dir = "./jfeff_feff10.0.0_linux_install/JFEFF/feff10/linux/"
fdmnes_bin = "./fdmnes_Linux/fdmnes_linux64"
feff_bin = [
    "rdinp",
    "dmdw",
    "atomic",
    "pot",
    "ldos",
    "screen",
    "crpa",
    "opconsat",
    "xsph",
    "fms",
    "mkgtr",
    "path",
    "genfmt",
    "ff2x",
    "sfconv",
    "compton",
    "eels",
    "rhorrp",
]

element_to_Z = {
    "H": 1,
    "He": 2,
    "Li": 3,
    "Be": 4,
    "B": 5,
    "C": 6,
    "N": 7,
    "O": 8,
    "F": 9,
    "Ne": 10,
    "Na": 11,
    "Mg": 12,
    "Al": 13,
    "Si": 14,
    "P": 15,
    "S": 16,
    "Cl": 17,
    "Ar": 18,
    "K": 19,
    "Ca": 20,
    "Sc": 21,
    "Ti": 22,
    "V": 23,
    "Cr": 24,
    "Mn": 25,
    "Fe": 26,
    "Co": 27,
    "Ni": 28,
    "Cu": 29,
    "Zn": 30,
    "Ga": 31,
    "Ge": 32,
    "As": 33,
    "Se": 34,
    "Br": 35,
    "Kr": 36,
    "Rb": 37,
    "Sr": 38,
    "Y": 39,
    "Zr": 40,
    "Nb": 41,
    "Mo": 42,
    "Tc": 43,
    "Ru": 44,
    "Rh": 45,
    "Pd": 46,
    "Ag": 47,
    "Cd": 48,
    "In": 49,
    "Sn": 50,
    "Sb": 51,
    "Te": 52,
    "I": 53,
    "Xe": 54,
    "Cs": 55,
    "Ba": 56,
    "La": 57,
    "Ce": 58,
    "Pr": 59,
    "Nd": 60,
    "Pm": 61,
    "Sm": 62,
    "Eu": 63,
    "Gd": 64,
    "Tb": 65,
    "Dy": 66,
    "Ho": 67,
    "Er": 68,
    "Tm": 69,
    "Yb": 70,
    "Lu": 71,
    "Hf": 72,
    "Ta": 73,
    "W": 74,
    "Re": 75,
    "Os": 76,
    "Ir": 77,
    "Pt": 78,
    "Au": 79,
    "Hg": 80,
    "Tl": 81,
    "Pb": 82,
    "Bi": 83,
    "Th": 90,
    "Pa": 91,
    "U": 92,
    "Np": 93,
    "Pu": 94,
    "Am": 95,
    "Cm": 96,
    "Bk": 97,
    "Cf": 98,
    "Es": 99,
    "Fm": 100,
    "Md": 101,
    "No": 102,
    "Lr": 103,
    "Rf": 104,
    "Db": 105,
    "Sg": 106,
    "Bh": 107,
    "Hs": 108,
    "Mt": 109,
    "Ds": 110,
    "Rg": 111,
    "Cn": 112,
    "Nh": 113,
    "Fl": 114,
    "Mc": 115,
    "Lv": 116,
    "Ts": 117,
    "Og": 118,
}

feff_template = """TITLE	{title}
EDGE	{edge}
S02	0.9
CONTROL	1	1	1	1	1	1
PRINT	0	0	0	0	0	0
EXCHANGE	0	1.	0.
SCF	5.5	0	100	0.1	1
COREHOLE	RPA
XANES	5	0.05	0.1
FMS	7	0
POTENTIALS
{potentials}
ATOMS
{atoms}
END"""

fdmnes_template = """Absorber
{absorber}
Filout
{filename}
Conv_out
{filename}_conv
Radius
11.1
Green
Relativism
Edge
{edge}
Center_abs
Range	!	Energy	range	of	calculation	(eV)
-3.	0.2	5.	0.5	20.	1.	75.	!	first	energy,	step,	intermediary	energy,	step	...,	last	energy
Molecule
1	1	1	90	90	90

{coordinates}
Convolution
Estart
-20
Efermi
-1.
End
"""


def run_feff(directory):
    cd_commands = ["cd", directory]

    for bin in tqdm(feff_bin):
        cmd = cd_commands + ["&&", "../" + feff_dir + bin]
        cmd = " ".join(cmd)
        subprocess.run(cmd, shell=True)


def run_feff_from_string(feff_inp, directory):
    os.makedirs(directory, exist_ok=True)
    with open(directory + "feff.inp", "w") as f:
        f.write(feff_inp)
    run_feff(directory)


def run_fdmnes(directory, filename="tmp"):
    fdmfile_txt = f"""1
{filename}.inp.txt"""

    os.makedirs(directory, exist_ok=True)
    with open(directory + "fdmfile.txt", "w") as f:
        f.write(fdmfile_txt)

    cd_commands = ["cd", directory]
    cmd = cd_commands + ["&&", "../" + fdmnes_bin]
    cmd = " ".join(cmd)

    subprocess.run(cmd, shell=True)


def run_fdmnes_from_string(
    fdmnes_inp, directory, filename="tmp", edge="K", absorber=1
):
    os.makedirs(directory, exist_ok=True)
    with open(directory + f"{filename}.inp.txt", "w") as f:
        f.write(fdmnes_inp.format(edge=edge, filename=filename, absorber=absorber))
    run_fdmnes(directory, filename=filename)


def make_potential_atoms_from_xyz(xyz, absorber=0):
    lines = xyz.split("\n")

    if len(lines) < 3:
        raise ValueError("Invalid xyz")

    n_atoms = int(lines[0])
    lines = lines[2:]

    elements = []
    coodinates = []

    for line in lines:
        element, x, y, z = line.split()
        element = element.strip()
        x, y, z = float(x), float(y), float(z)

        elements.append(element)
        coodinates.append([x, y, z])

    elements = np.array(elements)
    coodinates = np.array(coodinates)

    # Potentials
    unique_elements = np.unique(elements)
    unique_counts = np.array(
        [np.sum(elements == element) for element in unique_elements]
    )

    absorber_element = element_to_Z[elements[absorber]]

    potentials = []
    potential_dict = {}

    potentials.append(
        f"0 {absorber_element} {elements[absorber]} -1 -1 0.001"
    )  # absorber

    counter = 1
    for element, count in zip(unique_elements, unique_counts):
        if (element == absorber) and (count <= 1):
            continue

        potentials.append(f"{counter} {element_to_Z[element]} {element} -1 -1 {count}")
        potential_dict[element] = counter
        counter += 1

    potentials = "\n".join(potentials)

    # Atoms

    atoms = []

    for i, (element, coodinate) in enumerate(zip(elements, coodinates)):
        if i == absorber:
            print(i)
            atoms.append(f"{coodinate[0]} {coodinate[1]} {coodinate[2]} 0")
            continue
        atoms.append(
            f"{coodinate[0]} {coodinate[1]} {coodinate[2]} {potential_dict[element]}"
        )

    atoms = "\n".join(atoms)

    return potentials, atoms


def make_fdmnes_coordinates_from_xyz(xyz, absorber=0):
    lines = xyz.split("\n")

    if len(lines) < 3:
        raise ValueError("Invalid xyz")

    n_atoms = int(lines[0])
    lines = lines[2:]

    elements = []
    coodinates = []

    for line in lines:
        element, x, y, z = line.split()
        element = element.strip()
        x, y, z = float(x), float(y), float(z)

        elements.append(element)
        coodinates.append([x, y, z])

    elements = np.array(elements)
    coodinates = np.array(coodinates)

    fdmnes_coordinates = []

    for i, (element, coodinate) in enumerate(zip(elements, coodinates)):
        fdmnes_coordinates.append(
            f"{element_to_Z[element]} {coodinate[0]} {coodinate[1]} {coodinate[2]}"
        )

    fdmnes_coordinates = "\n".join(fdmnes_coordinates)

    return fdmnes_coordinates, absorber + 1


def run_feff_from_xyz(xyz, directory, absorber=0, edge="K", title="test"):
    potentials, atoms = make_potential_atoms_from_xyz(xyz, absorber=absorber)
    feff_inp = feff_template.format(
        title=title, edge=edge, potentials=potentials, atoms=atoms
    )
    run_feff_from_string(feff_inp, directory)

def run_feff_from_xyz_file(xyz_file, directory, absorber=0, edge="K", title="test"):
    with open(xyz_file, "r") as f:
        xyz = f.read()
    run_feff_from_xyz(xyz, directory, absorber=absorber, edge=edge, title=title)


def run_fdmnes_from_xyz(xyz, directory, absorber=0, edge="K", filename="tmp"):
    fdmnes_coordinates, fdmnes_absorber = make_fdmnes_coordinates_from_xyz(xyz, absorber=absorber)
    fdmnes_inp = fdmnes_template.format(
        absorber=fdmnes_absorber, edge=edge, filename=filename, coordinates=fdmnes_coordinates
    )
    run_fdmnes_from_string(
        fdmnes_inp, directory, filename=filename
    )
    
def run_fdmnes_from_xyz_file(xyz_file, directory, absorber=0, edge="K", filename="tmp"):
    with open(xyz_file, "r") as f:
        xyz = f.read()
    run_fdmnes_from_xyz(xyz, directory, absorber=absorber, edge=edge, filename=filename)

def lattice_points_to_xyz(lattice_points, atoms):
    lattice_points = np.array(lattice_points)
    
    if isinstance(atoms, str):
        atoms = [atoms] * len(lattice_points)
    elif isinstance(atoms, list):
        if len(atoms) != len(lattice_points):
            raise ValueError("atoms and lattice_points must have the same length")
    
    atoms = np.array(atoms)

    n_atoms = len(atoms)

    xyz = f"{n_atoms}\n\n"

    for atom, lattice_point in zip(atoms, lattice_points):
        xyz += f" {atom} {lattice_point[0]} {lattice_point[1]} {lattice_point[2]}\n"

    return xyz