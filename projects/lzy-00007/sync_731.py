import shutil
import os

src_dir = r'e:\WORKSPACE_ROOT\项目\lzy-00007'
dst_dir = r'E:\WORKSPACE_ROOT\DogFooding\projects\lzy-00007'

# 同步 src
src = os.path.join(src_dir, 'src')
dst = os.path.join(dst_dir, 'src')
if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree(src, dst)
print('src 同步完成')

# 同步 public
src = os.path.join(src_dir, 'public')
dst = os.path.join(dst_dir, 'public')
if os.path.exists(dst):
    shutil.rmtree(dst)
shutil.copytree(src, dst)
print('public 同步完成')

# 同步根目录文件（包括新的测试文件、配置文件、过程文件等）
for item in os.listdir(src_dir):
    s = os.path.join(src_dir, item)
    d = os.path.join(dst_dir, item)
    if os.path.isfile(s):
        shutil.copy2(s, d)
        print(f'{item} 同步完成')
