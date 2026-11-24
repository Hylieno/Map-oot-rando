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
    updated_chest = dict(chest, Translate=[18.0, 107.0, -7.5])
    adult_pot = dict(pot, Hash=322, Translate=[16.0, 108.0, -8.0])
    water_chest = dict(chest, Hash=987, Translate=[55.5, 119.0, -9.5])
    water_skulltula = {'Gyaml': 'Enemy_Skulltula_Gold', 'Hash': 988, 'Translate': [50.0, 120.0, -13.5]}

    def resource(data):
        return compressor.compress(dump({'endian': '<', 'version': 7, 'root': data}))

    def scene(*actors):
        return resource({'Actors': list(actors)})

    def map_parameters(floor):
        floors = [{'TBox': [{'InstanceID': 987}] if number == floor else [],
                   'CollectSign': [{'InstanceID': 988}] if number == -1 else []}
                  for number in range(-1, 3)]
        return dump({'endian': '<', 'version': 7,
                     'root': {'WaterTemple': {'MinFloor': -1, 'Floor': floors}}})

    # Both package trees start at their own root in the directory table.
    directories = [(None, b''), (0, b'romfs'), (1, b'Pack'), (1, b'Banc'), (3, b'KokiriForest'),
                   (None, b''), (5, b'romfs'), (6, b'Banc'), (7, b'KokiriForest'),
                   (3, b'WaterTemple'), (3, b'BancBasedResource'), (7, b'BancBasedResource')]
    child_static = b'KokiriForest_Child_Static.bcett.byml.zs'
    files = [(2, b'ZsDic.pack.zs', compressor.compress(build_sarc({}))),
             (4, child_static, scene(chest)),
             (4, b'KokiriForest_Child_Dynamic.bcett.byml.zs', scene(pot)),
             (8, child_static, scene(updated_chest)),
             (8, b'KokiriForest_Adult_Dynamic.bcett.byml.zs', scene(adult_pot)),
             (9, b'WaterTemple_Static.bcett.byml.zs', scene(water_chest, water_skulltula)),
             (10, b'MapParam.byml', map_parameters(0)),
             (11, b'MapParam.byml.zs', compressor.compress(map_parameters(1)))]
    children_by_directory = [[] for _ in directories]
    for index, (parent, _) in enumerate(directories):
        if parent is not None:
            children_by_directory[parent].append(index)
    for index, (parent, _, _) in enumerate(files, start=len(directories)):
        children_by_directory[parent].append(index)
    name_pool = bytearray()
    child_indices = bytearray()
    directory_records = bytearray()
    file_records = bytearray()
    for (_, name), children in zip(directories, children_by_directory):
        directory_records.extend(pack('<IIIIQ', len(name_pool), len(name), len(child_indices) // 4,
                                      len(children), 0))
        name_pool.extend(name)
        child_indices.extend(pack('<' + 'I' * len(children), *children))

    header = bytearray(128)
    body = bytearray()
    for _, name, content in files:
        file_records.extend(pack('<IIQQQ32sB15x', len(name_pool), len(name), len(content),
                                 len(header) + len(body), len(content), sha256(content).digest(), 0))
        name_pool.extend(name)
        body.extend(content)
    # Put the update first in the table. It still takes precedence by title ID.
    packages = pack('<QIIII40x', 0x801, 5, 0, 0, 0) + pack('<QIIII40x', 1, 0, 0, 0, 0)
    tables = packages + directory_records + file_records + child_indices
    toc = pack('<IIQQQQQ', 0x01434F54, 2, len(directories), len(files), 48 + len(tables), len(name_pool), 0)
    toc += tables + name_pool
    pack_into('<4s4xQQ32s', header, 0, b'NUP\x01', len(header) + len(body), len(toc), sha256(toc).digest())
    (directory / 'synthetic.nup').write_bytes(header + body + toc)
    checks = [{'id': 'KokiriForest#123', 'name': 'Fixture chest', 'category': 'full_chests'},
              {'id': 'KokiriForest#pots#321', 'name': 'Fixture pot', 'category': 'full_pots'},
              {'id': 'KokiriForest#pots#322', 'name': 'Fixture adult pot', 'category': 'full_pots'},
              {'id': 'WaterTemple#987', 'name': 'Fixture Water Temple chest', 'category': 'full_chests'},
              {'id': 'WaterTemple#gs#988', 'name': 'Fixture Skulltula', 'category': 'full_skulltula'}]
    catalogue = {'schema_version': 1, 'seed_id': 'portable-test', 'checks': checks}
    (directory / 'checks.json').write_text(json.dumps(catalogue), encoding='utf-8')


if __name__ == '__main__':
    path = Path(sys.argv[1])
    path.mkdir(parents=True, exist_ok=True)
    write_fixture(path)
