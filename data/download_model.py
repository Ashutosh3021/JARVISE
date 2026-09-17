import urllib.request, os, time

os.chdir(r'C:\Users\ashut\Downloads\JARVISE\data\kokoro_models')

# Remove truncated file
if os.path.exists('kokoro-v1.0.int8.onnx'):
    sz = os.path.getsize('kokoro-v1.0.int8.onnx')
    if sz < 90_000_000:
        os.remove('kokoro-v1.0.int8.onnx')
        print(f'Removed truncated file ({sz} bytes)')

url = 'https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.int8.onnx'

class Progress:
    def __init__(self):
        self.start = time.time()
        self.last_print = 0
    def __call__(self, block_num, block_size, total_size):
        downloaded = block_num * block_size
        elapsed = time.time() - self.start
        speed = downloaded / elapsed if elapsed > 0 else 0
        now = time.time()
        if now - self.last_print < 2:
            return
        self.last_print = now
        pct = downloaded * 100 / total_size if total_size > 0 else 0
        mb = downloaded / 1048576
        total_mb = total_size / 1048576
        print('\r%.1f MB / %.1f MB (%.0f%%) %.0f KB/s' % (mb, total_mb, pct, speed/1024), end='', flush=True)

print('Downloading kokoro-v1.0.int8.onnx...')
urllib.request.urlretrieve(url, 'kokoro-v1.0.int8.onnx', Progress())
print()
sz = os.path.getsize('kokoro-v1.0.int8.onnx')
print(f'Done: {sz} bytes ({sz/1048576:.1f} MB)')
