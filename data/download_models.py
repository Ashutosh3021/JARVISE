import urllib.request, os, sys, time

os.chdir(r'C:\Users\ashut\Downloads\JARVISE\data\kokoro_models')
base = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0'

files = [
    ('kokoro-v1.0.int8.onnx', base + '/kokoro-v1.0.int8.onnx'),
    ('voices-v1.0.bin', base + '/voices-v1.0.bin'),
]

for name, url in files:
    if os.path.exists(name) and os.path.getsize(name) > 1000000:
        print(name + ' already exists (' + str(os.path.getsize(name)) + ' bytes)')
        continue
    print('Downloading ' + name + '...')
    start = time.time()
    try:
        urllib.request.urlretrieve(url, name)
        elapsed = time.time() - start
        print('Downloaded ' + name + ' (' + str(os.path.getsize(name)) + ' bytes) in ' + str(int(elapsed)) + 's')
    except Exception as e:
        print('Failed: ' + str(e))

print('Done')
