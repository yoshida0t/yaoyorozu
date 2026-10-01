import sys

def xyz_to_jsonlike(xyz_filename):
    jsonlike = []
    with open(xyz_filename, 'r') as f:
        lines = f.readlines()
        for line in lines[2:]:  # 最初の2行（原子数とコメント）をスキップ
            parts = line.strip().split()
            if len(parts) != 4:
                continue
            atom = parts[0]
            coords = list(map(float, parts[1:]))
            jsonlike.append({ "atom": atom, "xyz": coords })

    for i,item in enumerate(jsonlike):
        if i<len(jsonlike)-1:
            print(f'{{ "atom" : "{item["atom"]}", "xyz" : [ {item["xyz"][0]: .14f}, {item["xyz"][1]: .14f}, {item["xyz"][2]: .14f}]}},')
        else:
            print(f'{{ "atom" : "{item["atom"]}", "xyz" : [ {item["xyz"][0]: .14f}, {item["xyz"][1]: .14f}, {item["xyz"][2]: .14f}]}}')

xyz_to_jsonlike(sys.argv[1])
