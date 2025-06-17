import os
import sys
import shutil

if len(sys.argv) < 3:
    print("err: wrong number of arguments given")
    print("usage: integrate SET_THIS_DIR LIKE_THAT_DIR")
    sys.exit()

target = sys.argv[1]
template = sys.argv[2]

base_dir = os.listdir(f"cache/{target}")

if not base_dir:
    print("err: no base cache file found")
    sys.exit()

print("using", base_dir[0], "as cache state")
for filename in filter(lambda x: x != base_dir[0], os.listdir(f"cache/{template}")):
    print("=> create", filename, end=" ")
    shutil.copy(f"cache/{target}/{base_dir[0]}", f"cache/{target}/{filename}")
    print("+")

print("done")
