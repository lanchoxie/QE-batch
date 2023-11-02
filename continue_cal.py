import numpy
import os
import time
import sys


prefix="BTO"  #the prefix same in your input file

root_dir = os.path.expandvars('$HOME')
#code_dir="%s/bin/QE-batch"%root_dir
code_dir=sys.path[0]
############job_script_settings##########
flat_info=open("%s/flat.save/FLAT_INFO"%code_dir).readlines()
for lines in flat_info:
    if lines.find("flat_number=")!=-1:
        flat_number=int(lines.split("flat_number=")[-1].split("#")[0])
    if lines.find("node_num=")!=-1:
        node_num=int(lines.split("node_num=")[-1].split("#")[0])
    if lines.find("ppn_num")!=-1:
        ppn_num_man=int(lines.split("ppn_num=")[-1].split("#")[0])
        if ppn_num_man==0:
            ppn_set=0
        elif ppn_num_man!=0:
            ppn_set=1
    if lines.find("wall_time=")!=-1:
        wall_time=lines.split("wall_time=")[-1].split("#")[0].strip("\n")


#flat_number=2           # 1 for"zf_normal",2 for "spst_pub",3 for "dm_pub_cpu"
#node_num=2
#wall_time="116:00:00"
#ppn_set=1
#ppn_num_man=16
####################"zf_normal" has 52ppn,"spst_pub" has 32 ppn ,"dm_pub_cpu" has 32 ppn
if flat_number==1:
    type_flat="zf_normal"
if flat_number==2:
    type_flat="spst_pub"
if flat_number==3:
    type_flat="dm_pub_cpu"
###################
qe_dir="/hpc/data/home/spst/zhengfan/open/replace"

def JOB_func(type_flat,node_num):

    type_hpc=""
    if type_flat=="spst_pub":
        ppn_num=32
        type_hpc="pbs"
    elif type_flat=="zf_normal":
        ppn_num=52
        type_hpc="pbs"
    elif type_flat=="dm_pub_cpu":
        ppn_num=32
        type_hpc="sbatch"
    if ppn_set==1:
        ppn_num=ppn_num_man
    ppn_tot=node_num*ppn_num

    if type_hpc=="pbs":
        jobscript_file_in=['#!/bin/bash\n',
        '#PBS  -N   coolxty\n',
        '#PBS  -l   nodes=%d:ppn=%d\n'%(node_num,ppn_num),
        '#PBS  -l   walltime=%s\n'%wall_time,
        '#PBS  -S   /bin/bash\n',
        '#PBS  -j   oe\n', 
        '#PBS  -q   %s\n'%(type_flat),
        '\n',
        'cd $PBS_O_WORKDIR\n',
        '\n',
        'NPROC=`wc -l < $PBS_NODEFILE`\n',
        'JOBID=$( echo $PBS_JOBID | awk -F \".\"  \'{print $1}\')\n',
        "echo \'JOB-ID = \'  $JOBID >> JOB-${JOBID}\n",
        "echo This job has allocated $NPROC procs >> JOB-${JOBID}\n",
        "TW=$( qstat -f \"$JOBID\" | grep -e \'Resource_List.walltime\' | awk -F \"=\" \'{print $(NF)}\' )\n",
        "echo \'requested walltime = \'  $TW  >> JOB-${JOBID}\n",
        "Q=$( qstat -f \"$JOBID\" | grep -e \'queue\' | awk \'{print $3}\' )\n",
        "echo \'requested queue = \'  $Q >> JOB-${JOBID}\n",
        "TC=$( qstat -f \"$JOBID\" | grep -e \'etime\' | awk -F \"=\" \'{print $(NF)}\' )\n",
        "TC_s=$( date -d \"$TC\" +%s )\n",
        "echo \'time submit = \'  $TC $TC_s >> JOB-${JOBID}\n",
        "TS=$( qstat -f \"$JOBID\" | grep -e \'start_time\' | awk -F \"=\" \'{print $(NF)}\' )\n",
        "TS_s=$( date -d \"$TS\" +%s )\n",
        "echo \'time start = \'  $TS  $TS_s >> JOB-${JOBID}\n",
        "TimeDu=`expr $TS_s - $TC_s`\n",
        "echo \'Waiting time(s) = \'  $TimeDu  >> JOB-${JOBID}\n",
        "\n",
        "echo This job has allocated $NPROC proc > log\n",
        "\n",
        "module load compiler/intel/2021.3.0\n",
        "module load mpi/intelmpi/2021.3.0\n",
        "\n",
        ]
    if type_hpc=="sbatch":
        jobscript_file_in=[
        "#!/bin/bash\n",
        "#SBATCH --job-name=xty\n",
        "#SBATCH -D ./\n",
        "#SBATCH --nodes=%d\n"%node_num,
        "#SBATCH --ntasks-per-node=%d\n"%ppn_num,
        "#SBATCH -o output.%j\n",
        "##SBATCH -e error.%j\n",
        "#SBATCH --time=%s\n"%wall_time,
        "#SBATCH --partition=dm_pub_cpu\n",
        "\n",
        "##SBATCH --gres=gpu:4 #if use gpu, uncomment this\n",
        "#export I_MPI_PMI_LIBRARY=/opt/gridview/slurm/lib/libpmi.so\n",
        "ulimit -s unlimited\n",
        "ulimit -l unlimited\n",
        "\n",
        "#setup intel oneapi environment \n",
        "source /dm_data/apps/intel/oneapi/setvars.sh\n",
        "#source /etc/profile\n",
        "module load compiler/latest\n",
        "module load mpi/latest\n",
        "module load mkl/latest\n",
        ]
    return jobscript_file_in,type_hpc,ppn_tot

def JOB_modify(JOB,mode,molecule_i,type_hpc_out,ppn_tot_out):
    vaspfile=molecule_i
    fj=open(JOB,"w+")
    jobscript_file_1=[]
    for i in range(len(jobscript_file)):
        j_rename=""
        #print(jobscript_file[i],type(jobscript_file[i]),i)
        if type_hpc_out=="pbs":
            if jobscript_file[i].find('#PBS  -N')!=-1:
                job_name_split=vaspfile.split("_")
                for j_names in job_name_split:
                    j_rename+=j_names[:2].zfill(2)
                jobscript_file[i]='#PBS  -N   %s\n'%(j_rename)
            jobscript_file_1.append(jobscript_file[i])
        if type_hpc_out=="sbatch":
            if jobscript_file[i].find('#SBATCH --job-name')!=-1:
                job_name_split=vaspfile.split("_")
                for j_names in job_name_split:
                    j_rename+=j_names[:2].zfill(2)
                jobscript_file[i]='#SBATCH --job-name=%s\n'%(j_rename)
            jobscript_file_1.append(jobscript_file[i])
    if (type_hpc_out=="pbs") & (mode!="pdos") & (mode!="BaderCharge"):
        if solvation_model==0:
            jobscript_file_1.append("mpirun --bind-to core -np $NPROC -hostfile $PBS_NODEFILE %s/pw-6.8.x -npool 4 -ndiag 4 < in_%s_%s  >& out_%s_%s"%(qe_dir,mode,molecule_i,mode,molecule_i)) 
        elif solvation_model==1:
            jobscript_file_1.append("mpirun --bind-to core -np $NPROC -hostfile $PBS_NODEFILE %s/pw-7.2-environ.x -npool 4 -ndiag 4 --environ < in_%s_%s  >& out_%s_%s"%(qe_dir,mode,molecule_i,mode,molecule_i))
    elif (type_hpc_out=="sbatch") & (mode!="pdos") & (mode!="BaderCharge"):
        if solvation_model==0:
            jobscript_file_1.append("mpirun --bind-to core -np %s %s/pw-6.8.x -npool 4 -ndiag 4 < in_%s_%s  >& out_%s_%s"%(ppn_tot_out,qe_dir,mode,molecule_i,mode,molecule_i))
        elif solvation_model==1:
            jobscript_file_1.append("mpirun --bind-to core -np %s -hostfile $PBS_NODEFILE %s/pw-7.2-environ.x -npool 4 -ndiag 4 --environ < in_%s_%s  >& out_%s_%s"%(ppn_tot_out,qe_dir,mode,molecule_i,mode,molecule_i))
    elif mode=="pdos":
        jobscript_file_1.append("mpirun --bind-to core -np %s %s/projwfc.x -npool 4 -ndiag 4 < in_%s_%s  >& out_%s_%s"%(ppn_tot_out,qe_dir,mode,molecule_i,mode,molecule_i))
    elif mode=="BaderCharge":
        jobscript_file_1.append("mpirun --bind-to core -np %s %s/pp.x -npool 4 -ndiag 4 < in_%s_%s  >& out_%s_%s"%(ppn_tot_out,qe_dir,mode,molecule_i,mode,molecule_i))



    fj.writelines(jobscript_file_1)
    jobscript_file_1=[]
    fj.close()

jobscript_file,type_hpc_out,ppn_tot_out=JOB_func(type_flat,node_num)
##default value of mode is relax
str_in_dir_i=sys.argv[1]
mode=sys.argv[2]
print(mode)

dir_file=(os.popen("pwd").read())
dir=max(dir_file.split('\n'))
JOB_name=""
error=0
if os.path.isfile("%s/replace.py"%code_dir)==1:
    replace_line=open("%s/replace.py"%code_dir).readlines()
#get the job_script name:
    for i in replace_line:
        if i.find("JOB=")!=-1:
            JOB_name=i.split("JOB=")[-1].split("#")[0].split("\"")[1]
            #print("JOB_name**************",JOB_name)
        if i.find("#solvation")!=-1:
            solvation_model=int(i.split("#")[0].split("solvation_model=")[-1].strip())
    if (JOB_name==""):
        print("ERROR: replace.py not set correctly!")
        error=1
elif os.path.isfile("%s/replace.py"%code_dir)==0:
    print("plz copy /hpc/data/home/spst/zhengfan/open/replace/replace.py here, otherwise some func does not work! ")
    error=1

sub_method=""
if (flat_number==1)|(flat_number==2):
    sub_method="qsub"
elif (flat_number==3):
    sub_method="sbatch"

#print("**************************%s %s"%(sub_method,JOB_name))

find_bcon=0
root_dir = os.path.expandvars('$HOME')
#print("%s/bin/bcon.sh"%root_dir)
if os.path.isfile("%s/bin/bcon.sh"%root_dir)==1:
    print("bcon.sh found")
    find_bcon=1
if find_bcon==0:
    print("bcon.sh not found,copy from /hpc/data/home/spst/zhengfan/open/ to ~/bin")
    os.system("cp /hpc/data/home/spst/zhengfan/open/bcon.sh  ~/bin/.")
 #recalculate if out of timing

os.chdir("%s/%s/"%(dir,(str_in_dir_i)))
if mode=="relax":
    os.system("bcon.sh out_relax_%s in_relax_%s"%((str_in_dir_i),(str_in_dir_i)))
    print("bcon.sh out_relax_%s in_relax_%s"%((str_in_dir_i),(str_in_dir_i)))

JOB_modify(JOB_name,mode,str_in_dir_i,type_hpc_out,ppn_tot_out)
os.system("%s %s"%(sub_method,JOB_name))
os.system("mv out_%s_%s out_buffer_%s"%(mode,str_in_dir_i,mode))
os.chdir(dir)
print("%s subed!"%str_in_dir_i)
