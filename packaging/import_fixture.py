"""Generate a tiny synthetic NUP and catalogue for the frozen import check."""
from hashlib import sha256
import json
from pathlib import Path
from struct import pack, pack_into
import sys

import zstandard

from oot_rando.formats.byml_codec import build_sarc, dump


def write_fixture(directory):
    compressor = zstandard.ZstdCompressor()
    chest = {'Gyaml': 'Obj_TBox_A_01', 'Hash': 123, 'Translate': [12.5, 106.0, -4.5],
             'Dynamic': {'Drop__DropActor': 'TBox_Rupee_Green'}}
    pot = {'Gyaml': 'Obj_Pot_A_01', 'Hash': 321, 'Translate': [14.0, 106.0, -3.0]}

    def scene(actor):
        return compressor.compress(dump({'endian': '<', 'version': 7, 'root': {'Actors': [actor]}}))

    # Directory indexes run from 0 to 4, followed by the three member indexes.
    directories = [(b'', [1]), (b'romfs', [2, 3]), (b'Pack', [5]), (b'Banc', [4]),
                   (b'KokiriForest', [6, 7])]
    files = [(b'ZsDic.pack.zs', compressor.compress(build_sarc({}))),
             (b'KokiriForest_Child_Static.bcett.byml.zs', scene(chest)),
             (b'KokiriForest_Child_Dynamic.bcett.byml.zs', scene(pot))]
    name_pool = bytearray()
    child_indices = bytearray()
    directory_records = bytearray()
    file_records = bytearray()
    for name, children in directories:
        directory_records.extend(pack('<IIIIQ', len(name_pool), len(name), len(child_indices) // 4,
                                      len(children), 0))
        name_pool.extend(name)
        child_indices.extend(pack('<' + 'I' * len(children), *children))

    header = bytearray(128)
    body = bytearray()
    for name, content in files:
        file_records.extend(pack('<IIQQQ32sB15x', len(name_pool), len(name), len(content),
                                 len(header) + len(body), len(content), sha256(content).digest(), 0))
        name_pool.extend(name)
        body.extend(content)
    package = pack('<QIIII40x', 1, 0, 0, 0, 0)
    tables = package + directory_records + file_records + child_indices
    toc = pack('<IIQQQQQ', 0x01434F54, 1, len(directories), len(files), 48 + len(tables), len(name_pool), 0)
    toc += tables + name_pool
    pack_into('<4s4xQQ32s', header, 0, b'NUP\x01', len(header) + len(body), len(toc), sha256(toc).digest())
    (directory / 'synthetic.nup').write_bytes(header + body + toc)
    checks = [{'id': 'KokiriForest#123', 'name': 'Fixture chest', 'category': 'full_chests'},
              {'id': 'KokiriForest#pots#321', 'name': 'Fixture pot', 'category': 'full_pots'}]
    catalogue = {'schema_version': 1, 'seed_id': 'portable-test', 'checks': checks}
    (directory / 'checks.json').write_text(json.dumps(catalogue), encoding='utf-8')


if __name__ == '__main__':
    path = Path(sys.argv[1])
    path.mkdir(parents=True, exist_ok=True)
    write_fixture(path)
