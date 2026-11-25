import struct
import unittest
from importlib.util import find_spec

from map_oot_rando.link_position import read_link_position


class PlayerMemory:
    """Small synthetic guest-memory image laid out at a relocated main base."""
    def __init__(self, *, scene='KokiriForest_Child', folder=None, x=23.5, appearance=None, fallback_scenes=()):
        self.main = 0x80634000
        self.slot = self.main + 0x04C7E180
        singleton, player, components, pose, scene_record = (
            0x2010001000, 0x2010002000, 0x2010003000, 0x2010004000, 0x2010005000)
        header = bytearray(0x60)
        struct.pack_into('<Q', header, 0, self.main + 0x04BA27C8)
        struct.pack_into('<I4xQ', header, 0x50, 37, components)
        table = bytearray(37 * 8)
        struct.pack_into('<Q', table, 7 * 8, scene_record)
        struct.pack_into('<Q', table, 36 * 8, pose)
        self.pose = bytearray(0x34)
        struct.pack_into('<QQQ', self.pose, 0, self.main + 0x04BA1818, self.main + 0x03EE4F8C, player)
        struct.pack_into('<6f', self.pose, 0x1C, x, 102.0, -8.0, 1.0, 0.0, 0.0)
        self.blocks = {
            self.main: struct.pack('<II', 1, 0x03C4705C),
            self.main + 0x04E6C7A8: bytes(8),
            self.main + 0x04E6C938: struct.pack('<Q', singleton),
            singleton + 0x10: struct.pack('<Q', player),
            player: header,
            components: table,
            pose: self.pose,
            scene_record + 0x34: f'Work/Banc/Scene/{folder or scene.split("_")[0]}/{scene}.bcett.json'
            .encode().ljust(0x80, b'\0'),
        }
        if appearance is not None:
            appearance_address = 0x2010006000
            struct.pack_into('<Q', table, 23 * 8, appearance_address)
            self.blocks[appearance_address + 0x80] = appearance.encode().ljust(0x80, b'\0')
        if fallback_scenes:
            scene_blob = '\0'.join(f'Work/Banc/Scene/{region}/{resource}.bcett.json'
                                   for region, resource in fallback_scenes).encode()
            self.blocks[player + 0x768] = scene_blob.ljust(0x480, b'\0')

    def read(self, address, count):
        from oot_rando.tracker.live_memory import LiveUnavailable

        block = self.blocks.get(address)
        if block is None or len(block) != count:
            raise LiveUnavailable('Fixture address not mapped')
        return block


@unittest.skipUnless(find_spec('oot_rando'), 'Pinned OotrR sources not on PYTHONPATH')
class LinkPositionTests(unittest.TestCase):
    def test_reads_relocated_player_and_alternate_singleton(self):
        sample = read_link_position(PlayerMemory(), 'Adult')
        self.assertEqual((sample.scene, sample.age), ('KokiriForest', 'Child'))
        self.assertEqual((sample.x, sample.y, sample.z, sample.yaw), (23.5, 102.0, -8.0, 90.0))

    def test_shared_scene_uses_verified_game_age(self):
        sample = read_link_position(PlayerMemory(scene='FireTemple'), 'Adult')
        self.assertEqual((sample.scene, sample.age), ('FireTemple', 'Adult'))

    def test_shared_scene_can_use_exact_link_model_when_the_age_flag_is_absent(self):
        for age in ('Child', 'Adult'):
            with self.subTest(age=age):
                memory = PlayerMemory(scene='SpiritTemple', appearance=f'Link_{age}')
                sample = read_link_position(memory, None)
                self.assertEqual((sample.scene, sample.age), ('SpiritTemple', age))
        memory = PlayerMemory(scene='SpiritTemple', appearance='Link_Child')
        self.assertEqual(read_link_position(memory, 'Adult').age, 'Adult')
        memory = PlayerMemory(scene='KokiriForest_Adult', appearance='Link_Child')
        self.assertEqual(read_link_position(memory, None).age, 'Adult')
        memory = PlayerMemory(scene='SpiritTemple', appearance='Npc_Link_Adult')
        self.assertIsNone(read_link_position(memory, None))

    def test_escape_scene_preserves_the_resource_inside_the_shared_folder(self):
        memory = PlayerMemory(scene='CrumblingGanonCastle_Dynamic', folder='GanonCastle')
        sample = read_link_position(memory, 'Adult')
        self.assertEqual((sample.scene, sample.age, sample.scene_resource),
                         ('GanonCastle', 'Adult', 'CrumblingGanonCastle'))

    def test_reads_the_loaded_kakariko_variant_when_the_scene_names_it(self):
        for resource, alternative in (('KakarikoVillage_Adult_Alternative_Dynamic', True),
                                      ('KakarikoVillage_Adult_Static', False),
                                      ('KakarikoVillage_Dynamic', None)):
            with self.subTest(resource=resource):
                sample = read_link_position(PlayerMemory(scene=resource), 'Adult')
                self.assertEqual((sample.scene, sample.age, sample.scene_resource, sample.scene_alternative),
                                 ('KakarikoVillage', 'Adult', 'KakarikoVillage', alternative))

    def test_rejects_wrong_game_layout_and_empty_pose(self):
        memory = PlayerMemory()
        memory.blocks[memory.main] = bytes(8)
        self.assertIsNone(read_link_position(memory, 'Child'))
        memory = PlayerMemory()
        struct.pack_into('<3f', memory.pose, 0x1C, 0, 0, 0)
        self.assertIsNone(read_link_position(memory, 'Child'))

    def test_fallback_requires_one_scene_after_combining_static_and_dynamic_layers(self):
        kokiri = ('KokiriForest', 'KokiriForest_Child_Static')
        woods = ('LostWood', 'LostWood_Child_Static')
        memory = PlayerMemory(scene='', fallback_scenes=(kokiri, woods))
        self.assertIsNone(read_link_position(memory, 'Child'))
        variants = (('KakarikoVillage', 'KakarikoVillage_Adult_Static'),
                    ('KakarikoVillage', 'KakarikoVillage_Adult_Alternative_Dynamic'))
        self.assertIsNone(read_link_position(PlayerMemory(scene='', fallback_scenes=variants), 'Adult'))
        memory = PlayerMemory(scene='', fallback_scenes=(kokiri, ('KokiriForest', 'KokiriForest_Child_Dynamic')))
        sample = read_link_position(memory, 'Adult')
        self.assertEqual((sample.scene, sample.scene_resource, sample.age),
                         ('KokiriForest', 'KokiriForest', 'Child'))

        memory = PlayerMemory(scene='LostWood_Child', fallback_scenes=(kokiri, woods))
        self.assertEqual(read_link_position(memory, 'Child').scene, 'LostWood')
