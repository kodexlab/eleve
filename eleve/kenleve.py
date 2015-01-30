import subprocess
from multiprocessing import Pipe, Process



def iter_of_connexion(conn, process):
    data = conn.recv_bytes()
    while data != '':
        yield data.decode("utf8")
        data = conn.recv_bytes()
    yield ''
    process.terminate()

def bidir_lmplz(iterable, order):
    parent_fwd, child_fwd = Pipe()
    parent_bwd, child_bwd = Pipe()
    process_fwd = Process(target=process_lmplz, args=(child_fwd, order))
    process_bwd = Process(target=process_lmplz, args=(child_bwd, order))
    process_fwd.start()
    process_bwd.start()
    for fwd,bwd in iterable:
        parent_fwd.send_bytes(fwd)
        parent_bwd.send_bytes(bwd)
    parent_fwd.send_bytes('')
    parent_bwd.send_bytes('')
    return (iter_of_connexion(parent_fwd, process_fwd), iter_of_connexion(parent_bwd, process_bwd))



def process_lmplz(connexion, order):
    lmplz = subprocess.Popen(['lmplz', '-o', str(order)],stdin=subprocess.PIPE, stdout=subprocess.PIPE,bufsize=1)
    data_in = connexion.recv_bytes()
    while data_in != '':
        lmplz.stdin.write(data_in)
        lmplz.stdin.write('\n')
        data_in = connexion.recv_bytes()
    lmplz.stdin.close()
    while lmplz.poll() is None:
        l = lmplz.stdout.readline()
        connexion.send_bytes(l)
    connexion.send_bytes('')
