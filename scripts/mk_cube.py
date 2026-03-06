import sys 
import os
import subprocess


# Setting argument's array name
args = sys.argv

# 
input_file = args[1]
spin_type = int(args[2])
orb_num = []

for i in range(len(args)-3):
    orb_num.append(int(args[i+3]))


# echo -e '5\n 7\n 4\n 60\n 2\n 284\n 10\n 2\n 285\n 10\n 11\n' | orca_plot  triplet_2220.uno -i
sc  =   "5\n7\n4\n100\n"
sc +=  f"3\n{spin_type}\n "
for i in range(len(orb_num)):
    sc +=  f"2\n {orb_num[i]}\n11\n "

sc +=   "12\n"
#sc +=  f"| orca_plot {input_file} -i"

#print(sc)
#os.system(f"{sc}")


import subprocess
input_text = sc


# コマンド本体（echo とパイプの代わりに subprocess を使う）
cmd = ['orca_plot', input_file, '-i']

# 実行
result = subprocess.run(cmd, input=input_text, text=True, capture_output=True)

# 結果出力（必要に応じて）
#print(result.stdout)
#print(result.stderr)
