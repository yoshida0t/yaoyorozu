import sys 
import os
import subprocess


input_file = sys.argv[1]

#if "fchk" in os.path.basename(input_file):
#    print("a")

valid_names = {".molden", ".fchk"} 
filename = os.path.basename(input_file)
ext = os.path.splitext(filename)[1]


if ext in valid_names:
    print("Load %s" % filename)
    for i in range(len(sys.argv)-2):
        mo_index = int(sys.argv[i+2])
        orb_num  = str(mo_index)    
        sc  =   "5\n4\n"
        sc +=  f"{orb_num}\n"
        sc +=  "2\n" # plot quality 1:low, 2:medium, 3:high
        sc +=  "2\n0\nq\n"
        
        input_text = sc
        
        
      #  cmd = ['multiwfn', input_file]
       
        cmd = ['/home/yoshida/apps/Multiwfn_2026.2.2_bin_Linux_noGUI/Multiwfn_noGUI', input_file]
        
        result = subprocess.run(cmd, input=input_text, text=True, capture_output=True)
        filename = os.path.basename(input_file)
        
        new_name = filename + ".mo%04d" % int(orb_num) +".cub"
        
        os.rename("MOvalue.cub",new_name)
        print("Dump %s" % orb_num)

else:
    print("TODO: implement this")
