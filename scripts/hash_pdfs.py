import hashlib as hs

hash_sha1 = hs.sha1()
BLOCK_SIZE = 8192  # Read 8192 bytes at a time
PATH = "/Users/albert/repos/valeria/nomina_Y9006705B_338109(1).pdf"

with open(PATH, 'rb') as file:
    buffer = file.read(BLOCK_SIZE)
    while len(buffer) > 0:
        hash_sha1.update(buffer)
        buffer = file.read(BLOCK_SIZE)

print('Hash of file is:', hash_sha1.hexdigest())