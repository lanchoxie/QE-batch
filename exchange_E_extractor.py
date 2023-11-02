# -*- coding: utf-8 -*-
from pymatgen.core.periodic_table import Element
from pymatgen.io.xcrysden import XSF
from pymatgen.analysis.structure_matcher import StructureMatcher
from pymatgen.core.composition import Composition
from pymatgen.core import Structure
from collections import defaultdict
import numpy as np
import os
import sys

str_name=sys.argv[1]
exchange_dir=f"{str_name}-exhange_file-extractor"
infile=f"{str_name}/out_relax_{str_name}.xsf"

dir_file=(os.popen("pwd").read())
current_dir=max(dir_file.split('\n'))
code_path=sys.path[0]
input_properties=sys.argv[2]  #searched properties

if not os.path.isfile(f"{exchange_dir}/pv_result_out"):
    os.chdir(exchange_dir)
    os.system("python QE-batch/read_relax_E_for_UI.py relax")
    os.chdir(current_dir)

#read the original coords from {str_name}/out_relax_{str_name}.xsf
class XSF_1:
    def __init__(self, structure):
        self.structure = structure
    def to_string(self, atom_symbol=True):
        lines = []
        app = lines.append
        app("CRYSTAL")
        app("# Primitive lattice vectors in Angstrom")
        app("PRIMVEC")
        cell = self.structure.lattice.matrix
        for i in range(3):
            app(f" {cell[i][0]:.14f} {cell[i][1]:.14f} {cell[i][2]:.14f}")
        cart_coords = self.structure.cart_coords
        app("# Cartesian coordinates in Angstrom.")
        app("PRIMCOORD")
        app(f" {len(cart_coords)} 1")
        for site, coord in zip(self.structure, cart_coords):
            sp = site.specie.symbol if atom_symbol else f"{site.specie.Z}"
            x, y, z = coord
            app(f"{sp} {x:20.14f} {y:20.14f} {z:20.14f}")
        return "\n".join(lines)

    @classmethod
    def from_string(cls, input_string, cls_=None):
        lattice, coords, species = [], [], []
        lines = input_string.splitlines()
        for i, line in enumerate(lines):
            if "PRIMVEC" in line:
                for j in range(i + 1, i + 4):
                    lattice.append([float(c) for c in lines[j].split()])
            if "PRIMCOORD" in line:
                num_sites = int(lines[i + 1].split()[0])

                for j in range(i + 2, i + 2 + num_sites):
                    tokens = lines[j].split()
                    #Z = Element(tokens[0]).Z if tokens[0].isalpha() else int(tokens[0])
                    Z = Element(''.join([i for i in tokens[0] if not i.isdigit()])).Z
                    species.append(Z)
                    coords.append([float(j) for j in tokens[1:4]])
                break
        else:
            raise ValueError("Invalid XSF data")
        if cls_ is None:
            from pymatgen.core.structure import Structure
            cls_ = Structure
        s = cls_(lattice, species, coords, coords_are_cartesian=True)
        return XSF(s)

f1=open(infile).readlines()
f2=""
for i in f1:
    f2+=i
xsf = XSF_1.from_string(f2)
structure = xsf.structure
def read_files(infiles):
    f=open(infiles,"r+")
    f1=f.readlines()
    read_data=[]
    for lines in f1:
        read_data_row=[]
        if "Direct" in lines:
            continue
        if len(lines) <= 1:
            continue
        if "\t" in lines:
            a_bf=(lines.split("\n")[0]).split("\t")
        else:
            a_bf=(lines.split("\n")[0]).split(" ")
        for i in a_bf:
            if len(i)>0:
                read_data_row.append(i)
        read_data.append(read_data_row)
   # print(len(read_data),len(read_data[0]))
    f.close()
    return read_data

read_data_str=read_files(f"{exchange_dir}/pv_result_out")
#print(read_data_str)
av_mode=''
if os.path.isfile(f"{str_name}/out_scf_{str_name}"):
    f_av=open(f"{str_name}/out_scf_{str_name}").readlines()
    if "JOB DONE" in f_av[-2]:
        av_mode="scf"
elif os.path.isfile(f"{str_name}/out_relax_{str_name}"):
    f_av=open(f"{str_name}/out_relax_{str_name}").readlines()
    if "JOB DONE" in f_av[-2]:
        av_mode="relax"
else:
    raise ValueError(f"No scf or relax DONE in {str_name}!")

E_original_line=os.popen(f"grep ! {str_name}/out_{av_mode}_{str_name}").readlines()[-1]
E_original=float(E_original_line.split("=")[-1].split("Ry")[0].strip())*27.211396/2
#E_original=float(E_original_line.split("=")[-1].split("Ry")[0].strip())

info_read=[]
for i,v in enumerate(read_data_str):
    file_name=[x for x in v[0].strip().split(str_name)[-1].split("_") if len(x)>0]
    E_relax_delta=float(v[3])-E_original
    data_buffer_lst=[]
    for j in file_name:
        ele_type="".join([x for x in j if not x.isdigit()])
        ele_number="".join([x for x in j if x.isdigit()])
        data_buffer_lst.append([ele_type,ele_number])
    #consider the periodic condition we select the nearest mirror Li close to Ni
    vec_a=structure.lattice.matrix[0]
    vec_b=structure.lattice.matrix[1]
    vec_c=structure.lattice.matrix[2]
    pbc_cell_333=[-1,0,1]
    dis_i=[]
    for a in pbc_cell_333: #contains the 3x3x3 supercell atoms and only get the minimal distance
        for b in pbc_cell_333:
            for c in pbc_cell_333:
                site_i=np.array(structure.sites[int(data_buffer_lst[0][1])-1].coords)+vec_a*a+vec_b*b+vec_c*c
                #calculate the distance between the neighbors and the center to select the nearest neighbors
                dis_i.append(np.linalg.norm(site_i - np.array(structure.sites[int(data_buffer_lst[1][1])-1].coords)))
    dis=min(dis_i)
    #dis=np.linalg.norm(np.array(structure.sites[int(data_buffer_lst[1][1])-1].coords - np.array(structure.sites[int(data_buffer_lst[0][1])-1].coords)))
    data_buffer_lst.append([v[0],"%.6f"%dis,"%.6f"%E_relax_delta])
    info_read.append(data_buffer_lst)
info_read=sorted(info_read,key=lambda x:float(x[-1][-1]))
#for i in info_read:
    #print(i)

#read available properties from search_data.py
av_prop_lines=os.popen("python %s/search_data.py %s \'{1}\' magnetic"%(code_path,str_name)).readlines()
av_props=[]
tot_props=[]
for lines in av_prop_lines:
    if "#AV_PROP#" in lines:
        av_props=lines.strip("#AV_PROP#").strip().strip("\n").split("\t")
    elif "#TOT_PROP#" in lines:
        tot_props=lines.strip("#TOT_PROP#").strip().strip("\n").split("\t")

#judge if the input properties is available
properties_lst=[x for x in input_properties.strip().split("+") if len(x)>0]
#print(input_properties)
not_found_props=[]
properties_lst_judge=properties_lst.copy()
for i in properties_lst_judge:
    #print("-----",i)
    if ":" in i:
        prop_i=i.split(":")[0]
    else:
        prop_i=i
    if prop_i not in av_props:
        if (prop_i[-1]=="*"):
            pass
        else:
            raise ValueError(f"{i} or {i[:-1]} not found in {av_props}!")

# info_read:[[ele1,index1],[ele2,index2],[filename,dis,delta_E]]
Ni_props=[]
Li_props=[]
for i in properties_lst:
    #print("!!PROPS",i)
    if ":Ni" in i:
        Ni_props.append(i.split(":Ni")[0])
    elif ":Li" in i:
        Li_props.append(i.split(":Li")[0])
    elif i.find(":")==-1:
        Ni_props.append(i)
        Li_props.append(i)

#print("****",Li_props,Ni_props)

Li_index=[]
Ni_index=[]
for entry in info_read:
    if entry[0][0] == 'Ni':
        Ni_index.append(entry[0][1])
    elif entry[0][0] == 'Li':
        Li_index.append(entry[0][1])
    if entry[1][0] == 'Ni':
        Ni_index.append(entry[1][1])
    elif entry[1][0] == 'Li':
        Li_index.append(entry[1][1])
#print(Li_index)
#print(Ni_index)
Li_words="{"+",".join(Li_index)+"}"
Ni_words="{"+",".join(Ni_index)+"}"
#print(Li_words)

Li_prop_words="+".join(Li_props)
Ni_prop_words="+".join(Ni_props)


#print("Calculate Li: python %s/search_multi_dupli_data.py %s \'%s\' %s"%(code_path,str_name,Li_words,Li_prop_words)) 
Li_data_lst_raw=os.popen("python %s/search_multi_dupli_data.py %s \'%s\' %s"%(code_path,str_name,Li_words,Li_prop_words)).readlines()
#print("Calculate Ni: python %s/search_multi_dupli_data.py %s \'%s\' %s"%(code_path,str_name,Ni_words,Ni_prop_words)) 
Ni_data_lst_raw=os.popen("python %s/search_multi_dupli_data.py %s \'%s\' %s"%(code_path,str_name,Ni_words,Ni_prop_words)).readlines()
Li_data_lst=[]
for row in Li_data_lst_raw:
    if row[0].startswith('#'):
        continue
    else:
        Li_data_lst.append([x.strip() for x in row.strip("\n").split("\t") if len(x)>0])
Ni_data_lst=[]
for row in Ni_data_lst_raw:
    if row[0].startswith('#'):
        continue
    else:
        Ni_data_lst.append([x.strip() for x in row.strip("\n").split("\t") if len(x)>0])

for i,v in enumerate(Li_data_lst[0]):
    Li_data_lst[0][i]=v+":Li"
for i,v in enumerate(Ni_data_lst[0]):
    Ni_data_lst[0][i]=v+":Ni"

#print(info_read)
#print(Ni_data_lst)

output_data=[["file_name","Li-Ni-distance","delta_E"]]
output_data[0].extend(Li_data_lst[0])
output_data[0].extend(Ni_data_lst[0])
#print("%%%%%%%%",output_data)
#print("AAA",len(info_read),len(Li_data_lst))
for i,v in enumerate(info_read):
    output_data_i=[]
    #print(v[-1][0],len(Li_data_lst[i]),len(Ni_data_lst[i]))
    output_data_i.extend([v[-1][0],v[-1][1],v[-1][2]])
    output_data_i.extend(Li_data_lst[i+1])
    output_data_i.extend(Ni_data_lst[i+1])
    output_data.append(output_data_i)
for i in output_data:
    print("\t".join(i))
