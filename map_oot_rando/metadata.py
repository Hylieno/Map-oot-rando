"""Export already-labelled OotrR scan results without reading or copying game assets."""
from fnmatch import fnmatchcase
from math import dist

from .model import REGION_NAMES, UPSTREAM_REVISION, load_metadata, resource_region

LOST_WOOD_EVENT_ACTORS = {
    'npc#LW Skull Kid': ('Npc_SkullKid_Child', None),
    'npc#LW Ocarina Memory Game': ('Npc_SkullKid_Child_02', None),
    'npc#LW Target in Woods': ('NPC_Scrub_Deku_TargetPractice', None),
    'scrub#LW Deku Scrub Near Bridge': ('Enemy_Scrub_Business', 'Enemy_Scrub_Business_DekuStickPouch_01'),
    'scrub#LW Deku Scrub Grotto Front': ('Enemy_Scrub_Business', 'Enemy_Scrub_Business_DekuNutsPouch_01'),
}
EVENT_ACTORS = {
    'KokiriForest': {('Npc_Kokiri_Saria_Child', 'KokiriForest_ArriveLostWood'): 'quest#LW Gift from Saria'},
    'LostWood': {actor: ident for ident, actor in LOST_WOOD_EVENT_ACTORS.items()},
    'GoronCity': {
        ('Npc_Goron_Darunia_Child', None): 'npc#GC Darunias Joy',
        ('Npc_Goron_006_Child', None): 'npc#GC Rolling Goron as Child',
        ('Npc_Goron_DaruniaJr_Adult', 'SageOfFire_Step01_DaruniaJr_BombHit'): 'npc#GC Rolling Goron as Adult',
    },
    'KakarikoVillage': {
        ('MapIconFacilityAnchor', 'GatheringTokenGold_FirstTalk'): tuple(
            f'npc#Kak {count} Gold Skulltula Reward' for count in range(10, 51, 10)),
        ('MapIconFacilityAnchor', 'KakarikoVillage_MiniGame_HitTarget_FirstTalk'): 'npc#Kak Shooting Gallery Reward',
        ('Npc_Hylia_049_Child', None): 'npc#Kak Anju as Child',
        ('Npc_Hylia_001_Adult', None): 'npc#Kak Man on Roof',
    },
    'Graveyard': {
        ('MapIconFacilityAnchor', 'MiniGame_DiggingHole_MinigameIconOn'): 'npc#Graveyard Dampe Gravedigging Tour',
    },
    'DeathMountainTrail': {
        ('MapIconFacilityAnchor', 'HavePlayedEvent.Dm_FairyFountain_Din'): 'fairy#DMT Great Fairy Reward',
        ('Npc_Goron_Biggoron_Adult', None): 'quest#DMT Biggoron',
    },
    'HyruleField': {
        ('Obj_Ocarina_Time_A_01', None): 'quest#HF Ocarina of Time Item',
        ('Enemy_Scrub_Business', 'Enemy_Scrub_Business_Heart_01'): 'scrub#HF Deku Scrub Grotto',
        ('Npc_Hylia_Fishman_001_Child', None): 'npc#LH Child Fishing',
        ('Npc_Hylia_Fishman_001_Adult', None): 'npc#LH Adult Fishing',
        ('Npc_Hylia_045_Child', None): 'npc#LH Lab Dive',
        ('MapIconFacilityAnchor', 'MiniGame_Unlock_FindOutCucco'): 'npc#LLR Talons Chickens',
    },
    'ZoraRiver': {('OcarinaPoint_MiniGame_FrogTenors', None): 'npc#ZR Frogs Ocarina Game'},
    'ZoraDomain': {
        ('MapIconFacilityAnchor', 'MiniGame_Diving_Mapicon'): 'npc#ZD Diving Minigame',
        ('Npc_Zora_KingZora_adult', None): 'npc#ZD King Zora Thawed',
    },
    'ZoraFountain': {
        ('MapIconFacilityAnchor', 'HavePlayedEvent.Dm_FairyFountain_Frore'): 'fairy#ZF Great Fairy Reward',
    },
    'DodongoCavern': {('Enemy_DungeonBoss_Dodongo', None): 'boss#King Dodongo'},
    'FireTemple': {('Enemy_DungeonBoss_Volvagia', None): 'boss#Volvagia'},
    'InsideJabuJabuBelly': {('Enemy_DungeonBoss_Barinade', None): 'boss#Barinade'},
    'InsideTheDekuTree': {('Enemy_DungeonBoss_Gohma', None): 'boss#Queen Gohma'},
    'ForestTemple': {('Enemy_DungeonBoss_PhantomGanon', None): 'boss#Phantom Ganon'},
    'ShadowTemple': {('Enemy_DungeonBoss_BongoBongo', None): 'boss#Bongo Bongo'},
    'SpiritTemple': {('Enemy_DungeonBoss_Twinrova', None): 'boss#Twinrova'},
    'WaterTemple': {('Enemy_DungeonBoss_Morpha', None): 'boss#Morpha'},
    'Market': {
        ('MapIconFacilityAnchor', 'Market_MiniGame_BombchuBowling_FirstTalk'): (
            'npc#Market Bombchu Bowling First Prize', 'npc#Market Bombchu Bowling Second Prize'),
        ('MapIconFacilityAnchor', 'Market_MiniGame_HitTarget_FirstTalk'): 'npc#Market Shooting Gallery Reward',
        ('MapIconFacilityAnchor', 'HaveTalked_Special.Npc_Hylia_048_BottleShop_Talk_Event5'): 'npc#Market 10 Big Poes',
        ('HeartPieceAnchor', 'SubEvent_FindRichard_GetHeartPiece'): 'npc#Market Lost Dog',
        ('Obj_TimeTemple_MasterSword_A_01', None): 'master_sword#ToT Master Sword',
        ('Npc_Hylia_Sheik_Adult', None): 'ap#Sheik at Temple',
        ('Land_TempleOfTime_A_01', None): 'quest#ToT Light Arrows Cutscene',
    },
    'SageRoom': {('StartPos', None): 'boss#Links Pocket'},
    'HyruleCastle': {
        ('MapIconFacilityAnchor', 'HavePlayedEvent.Dm_FairyFountain_Power'): 'fairy#HC Great Fairy Reward',
        ('Npc_Hylia_Zelda_Child', None): 'quest#HC Zeldas Letter',
    },
    'GanonCastle': {
        ('MapIconFacilityAnchor', 'HavePlayedEvent.Dm_FairyFountain_Courage'): 'fairy#OGC Great Fairy Reward',
    },
    'GerudoFortress': {
        ('Npc_Gerudo_008', None): ('npc#GF HBA 1000 Points', 'npc#GF HBA 1500 Points'),
    },
    'DesertColossus': {
        ('MapIconFacilityAnchor', 'HavePlayedEvent.Dm_FairyFountain_Nayru'): 'fairy#Colossus Great Fairy Reward',
    },
    'DeathMountainCrater': {
        ('MapIconFacilityAnchor', 'HavePlayedEvent.Dm_FairyFountain_Wisdom'): 'fairy#DMC Great Fairy Reward',
    },
}
DEKU_THEATER_CHECKS = ('npc#Deku Theater Skull Mask', 'npc#Deku Theater Mask of Truth')
ZORA_POT_ENTRANCE = ((5489068764052953067, 'Land_Kokiri_HidingHoleCover_A_01'),)
FOUNTAIN_CAVE_ENTRANCES = ((8723749739734887775, 'Land_ZoraFountain_Cave_A_01'),
                          (9794916849655187961, 'Land_ZoraFountain_Cave_A_01'))
GERUDO_STORMS_ENTRANCE = ((12817575131469044248, 'Land_Gerudo_HidingHoleCover_A_02'),)
FORTRESS_STORMS_ENTRANCE = ((1947815094993250377, 'DestinationAnchor'),)
# Dm_Gerudo_0025 moves Link beside the last freed carpenter. Each branch is
# identified by its nearby rescue anchor in the adult scene.
GERUDO_CARD_WARPS = {
    2581536444609170668: (28.79, 102.5, -71.60),
    15831574489666697813: (70.22, 120.5, -111.74),
    15814936526007887057: (42.30, 119.0, -25.93),
    15652772230412420096: (15.83, 110.0, -76.06),
}
GROTTO_ENTRANCE_ACTORS = {
    'KokiriForest#14818888396401495482': ((389687166017056250, 'Land_Kokiri_HidingHoleCover_A_01'),),
    'scrub#HF Deku Scrub Grotto': ((2319887810288392884, 'Land_HrlField_HidingHoleCover_A_01'),),
    'SacredForestMeadow#7995233962349162969': ((8456945034417122929, 'Land_Kokiri_HidingHoleCover_A_01'),),
    'SacredForestMeadow#1764383515296652106': ((15024208487326008169, 'Land_SacredForest_HidingHoleCover_A_02'),),
    **dict.fromkeys(DEKU_THEATER_CHECKS, ((4876738002315557989, 'DestinationAnchor'),)),
    'ZoraRiver#8838426083116998768': ((17321193928923817093, 'DestinationAnchor'),
                                     (15446115664186718191, 'DestinationAnchor')),
    **{f'ZoraRiver#pots#{pot}': ZORA_POT_ENTRANCE for pot in (
        10869334366827386783, 5730330007630899881, 4776081376285256939,
        8980910965654538945, 5095784848033030406, 8953658065056150046)},
    'ZoraFountain#gs#9537398183107003742': FOUNTAIN_CAVE_ENTRANCES,
    'ZoraFountain#pots#14131098108744088630': FOUNTAIN_CAVE_ENTRANCES,
    'ZoraFountain#pots#12389449717548603491': FOUNTAIN_CAVE_ENTRANCES,
    **{f'GerudoValley#{key}': GERUDO_STORMS_ENTRANCE for key in (
        '17750686910716887133', '18413589940135955604', 'pots#6896071498853277403',
        'pots#3407692112799570510', 'pots#15334540056586068351', 'pots#10851977283896645114')},
    'GerudoValley#6463521162691873710': ((2898121583347267819, 'DestinationAnchor'),
                                       (15684957330767796996, 'DestinationAnchor')),
    'GerudoFortress#16619432200060282313': FORTRESS_STORMS_ENTRANCE,
    'GerudoFortress#pots#12401477347800941236': FORTRESS_STORMS_ENTRANCE,
    'DesertColossus#1186167733408299582': ((6814744896634068027, 'DestinationAnchor'),
                                          (1089669422726566991, 'DestinationAnchor')),
}
CHECK_ACTOR_PATTERNS = {
    ('full_chests', ''): ('Obj_TBox_*',),
    ('full_crates', 'crates'): ('Obj_BrokenBox_*',),
    ('full_pots', 'pots'): ('Obj_Pot_*',),
    ('full_rocks', 'rocks'): ('Obj_BrokenRock_*', 'Obj_LiftRock_*'),
    ('full_bushes', 'bushes'): ('Obj_Plant_Grass_*',),
    ('full_trees', 'trees'): ('Obj_Tree_*',),
    ('full_freestanding', 'free'): ('Obj_Heart', 'Obj_Heart_Piece', 'Obj_Rupee_*'),
    ('full_skulltula', 'gs'): ('Enemy_Skulltula_Gold',),
    ('full_bossheart', 'heart'): ('Obj_Heart_Container',),
}
EVENT_ACTOR_FIELDS = {
    'MapIconFacilityAnchor': 'MapIconFacilityIsOpen',
    'HeartPieceAnchor': 'HeartPieceAnchor_GameDataPath',
    'Npc_Goron_DaruniaJr_Adult': 'ActorDeleteSetGameDataBool',
}
# The original catalogue labels also exist as actor checks in the remake.
# Match only encounters with an explicit chest trigger or a unique room reward.
CATALOGUE_PLACEMENT_ALIASES = {
    'ap#Gerudo Training Ground Stalfos Chest': 'GerudoTrainingGround#13501407288943710656',
    'ap#Gerudo Training Ground Beamos Chest': 'GerudoTrainingGround#4709724720801091788',
    'ap#Gerudo Training Ground Underwater Silver Rupee Chest': 'GerudoTrainingGround#3717705376223508790',
}
DUNGEON_ROOM_REGIONS = frozenset({'InsideJabuJabuBelly', 'InsideTheDekuTree', 'ForestTemple',
                                  'BottomOfTheWell', 'ShadowTemple', 'InsideGanonCastle', 'GerudoTrainingGround',
                                  'SpiritTemple', 'WaterTemple'})


def add_dungeon_rooms(rows, maps):
    """Preserve the explicit room number when actors share X/Z across levels."""
    rooms = {}
    for path, source in maps.items():
        if resource_region(path) not in DUNGEON_ROOM_REGIONS:
            continue
        for actor in source['root'].get('Actors', ()):
            position = actor.get('Translate')
            dynamic = actor.get('Dynamic')
            if position and isinstance(dynamic, dict):
                room = dynamic.get('DefaultDungeonRoomIndex')
                if type(room) is int and room >= 0:
                    rooms.setdefault((path, tuple(position)), set()).add(room)
    for row in rows:
        if row['position'] is not None:
            indices = rooms.get((row['resource'], tuple(row['position'])), ())
            if len(indices) == 1:
                row['dungeon_room'] = next(iter(indices))


def add_surface_entrances(rows, maps):
    """Place the surface marker at the known entrance of a buried check."""
    entrance_ids = {key for keys in GROTTO_ENTRANCE_ACTORS.values() for key in keys}
    candidates = {}
    for path, source in maps.items():
        if resource_region(path) is None:
            continue
        age_frame = path.rsplit('_', 1)[0]
        for actor in source['root'].get('Actors', ()):
            key = (actor.get('Hash'), actor.get('Gyaml'))
            if key in entrance_ids and actor.get('Translate'):
                candidates.setdefault((age_frame, key), set()).add(tuple(actor['Translate']))
    for row in rows:
        keys = GROTTO_ENTRANCE_ACTORS.get(row['id'])
        if keys and row['position'] is not None:
            frame = row['resource'].rsplit('_', 1)[0]
            points = {point for key in keys for point in candidates.get((frame, key), ())}
            if len(points) == 1:
                row['entrance'] = next(iter(points))


def export_scan(groups, extra, *, provenance, regions=('KokiriForest',)):
    """Consume scan_world chest groups and extra sources; never generate labels.

    Caller must scan the full world before restricting the regions so OotrR
    numbering remains authoritative. No positions are inferred for event checks.
    """
    rows, diagnostics = [], []
    entries = [(gid, 'chest', variants) for gid, variants in groups.items()]
    entries += [(gid, entry['source'], entry['variants']) for gid, entry in extra.items()]
    for gid, category, variants in entries:
        for variant in variants:
            resource = variant.get('resource', '')
            if resource_region(resource) not in regions:
                continue
            position = variant.get('position')
            if position is None:
                diagnostics.append(f'{gid}: missing coordinates in {resource}')
            rows.append(dict(id=gid, name=variant.get('label') or gid,
                             category=category, resource=resource, position=position))
        if not variants and gid.partition('#')[0] in regions:
            diagnostics.append(f'{gid}: no positioned variants')
    document = dict(schema_version=1, region='KokiriForest',
                    upstream_revision=UPSTREAM_REVISION, provenance=provenance,
                    locations=rows, diagnostics=diagnostics)
    if tuple(regions) != ('KokiriForest',):
        document['regions'] = list(regions)
    load_metadata(document)
    return document



def world_check_rows(maps, checks, eligible):
    """Resolve legacy world-map check IDs by the actor hash and exact patch field."""
    requested = {check['id']: check for check in checks}
    rows = []
    for path, resource in maps.items():
        region = resource_region(path)
        if region is None:
            continue
        for actor in resource['root'].get('Actors', ()):
            if type(actor.get('Hash')) is not int or not eligible(path, actor):
                continue
            prefix = f"{region}#{actor['Hash']}#"
            dynamic = actor.get('Dynamic')
            fields = ['Gyaml', *(dynamic if isinstance(dynamic, dict) else ())]
            for field in fields:
                ident = prefix + field
                if ident in requested:
                    check = requested[ident]
                    rows.append(dict(id=ident, name=check['name'], category=check['category'],
                                     resource=path, position=actor.get('Translate')))
    return rows


def placed_check_rows(maps, checks, existing, eligible):
    """Resolve typed catalogue IDs absent from the pack-based scan in each scene."""
    positioned = {(row['id'], row['resource'].rsplit('_', 1)[0])
                  for row in existing if row['position'] is not None}
    requested = {}
    for check in checks:
        region, _, suffix = check['id'].partition('#')
        kind, _, actor_hash = suffix.rpartition('#')
        patterns = CHECK_ACTOR_PATTERNS.get((check['category'], kind))
        if region in REGION_NAMES and patterns and actor_hash.isascii() and actor_hash.isdecimal():
            requested.setdefault((region, int(actor_hash)), []).append((check, patterns))
    for path, source in maps.items():
        region = resource_region(path)
        if region is None:
            continue
        frame = path.rsplit('_', 1)[0]
        for actor in source['root'].get('Actors', ()):
            position = actor.get('Translate')
            for check, patterns in requested.get((region, actor.get('Hash')), ()):
                if (position and (check['id'], frame) not in positioned and eligible(path, actor)
                        and any(fnmatchcase(actor.get('Gyaml', ''), pattern) for pattern in patterns)):
                    yield dict(id=check['id'], name=check['name'], category=check['category'],
                               resource=path, position=position)


def event_check_rows(maps, eligible):
    """Locate event rewards using their unique actor or cutscene position."""
    candidates = {}
    for path, source in maps.items():
        region = resource_region(path)
        ids = EVENT_ACTORS.get(region)
        if ids is None:
            continue
        age_frame = path.removesuffix('.bcett.byml.zs').rsplit('_', 1)[0]
        actors = source['root'].get('Actors', ())
        for actor in actors:
            dynamic = actor.get('Dynamic')
            gyaml = actor.get('Gyaml')
            parameter = EVENT_ACTOR_FIELDS.get(gyaml, 'TalkEventName')
            event = dynamic.get(parameter) if isinstance(dynamic, dict) else None
            ident = ids.get((gyaml, event))
            if ident is None and actor.get('Name'):
                ident = ids.get((gyaml, actor['Name']))
            position = actor.get('Translate')
            if ident == 'boss#Volvagia':
                # The model waits below the floor before the cutscene. The linked
                # destination is the center used during the encounter.
                centers = {link['Dst'] for link in actor.get('Links', ())
                           if link.get('Name') == 'RoomCenter' and 'Dst' in link}
                points = [anchor['Translate'] for anchor in actors
                          if anchor.get('Hash') in centers and anchor.get('Gyaml') == 'DestinationAnchor'
                          and anchor.get('Translate')]
                if len(points) == 1:
                    position = points[0]
            if ident == 'quest#ToT Light Arrows Cutscene':
                if not age_frame.endswith('_Adult'):
                    continue
                # Dm_TimeTemple_0130 places Link in the entrance hall.
                position = (81.55999755859375, 103.93000030517578, -34.0)
            if ident == 'boss#Links Pocket':
                # Dm_SageRoom_0005 moves Link to the center of the platform.
                position = (0, 100.12000274658203, 0)
            if ident == 'quest#LW Gift from Saria':
                # Goto_HyruleCastle places Saria on the bridge before Dm_Kokiri_0155.
                position = (-120.1259994506836, 114.48249816894531, -36.88779830932617)
            checks = (ident,) if isinstance(ident, str) else ident or ()
            if (region == 'LostWood' and actor.get('Gyaml') == 'Enemy_Scrub_ForestStage_Elder'
                    and actor.get('Name') == 'ScrubForestStageElder' and age_frame.endswith('_Child')):
                checks = DEKU_THEATER_CHECKS
            variant = None
            if (region == 'GerudoFortress' and gyaml == 'DestinationAnchor'
                    and actor.get('Name') == 'Dm_Gerudo_0023_LinkEndPosition'
                    and actor.get('Hash') in GERUDO_CARD_WARPS):
                variant = actor['Hash']
                position = GERUDO_CARD_WARPS[variant]
                checks = ('gerudo_card#Hideout Gerudo Membership Card',)
            if position and checks and eligible(path, actor):
                for check in checks:
                    candidates.setdefault((check, age_frame, variant), []).append(
                        dict(id=check, name=check.partition('#')[2], category='event',
                             resource=path, position=position))
    return [rows[0] for rows in candidates.values() if len(rows) == 1]


def domain_adult_placements(matches):
    """Keep distinct placements when the two adult scene layers share a view."""
    prefix = 'Banc/ZoraDomain/ZoraDomain_Adult_'
    alternative = prefix + 'Alternative_'
    regular = [row['position'] for row in matches if row['position']
               and row['resource'].startswith(prefix) and not row['resource'].startswith(alternative)]
    return [row for row in matches if not (row['resource'].startswith(alternative) and row['position']
                                           and any(dist(row['position'], point) < 0.05 for point in regular))]


def bind_catalogue(document, catalogue):
    """Use the seed's names and IDs and keep unmatched entries searchable."""
    if (catalogue.get('schema_version') != 1 or not isinstance(catalogue.get('seed_id'), str)
            or not catalogue['seed_id']):
        raise ValueError('Catalogue OotrR v1 avec seed_id requis')
    by_id = {}
    for row in document['locations']:
        by_id.setdefault(row['id'], []).append(row)
    regions = document.get('regions', ('KokiriForest',))
    names = {name: region for region, name in REGION_NAMES.items()}
    names.update({'Lost Woods': 'LostWood', 'the Lost Woods': 'LostWood', 'Hyrule Field': 'HyruleField',
                  'Sacred Forest Meadow': 'SacredForestMeadow', 'Kakariko Village': 'KakarikoVillage',
                  'Death Mountain Trail': 'DeathMountainTrail', 'Goron City': 'GoronCity',
                  "Dodongo's Cavern": 'DodongoCavern', 'Death Mountain Crater': 'DeathMountainCrater',
                  'Fire Temple': 'FireTemple', "Zora's River": 'ZoraRiver', "Zora's Domain": 'ZoraDomain',
                  "Zora's Fountain": 'ZoraFountain', 'Ice Cavern': 'IceCavern',
                  "Inside Jabu-Jabu's Belly": 'InsideJabuJabuBelly', 'Inside the Deku Tree': 'InsideTheDekuTree',
                  'Forest Temple': 'ForestTemple', 'Bottom of the Well': 'BottomOfTheWell',
                  'Shadow Temple': 'ShadowTemple', 'the Market': 'Market', 'Hyrule Castle': 'HyruleCastle',
                  "Outside Ganon's Castle": 'GanonCastle', "Ganon's Castle": 'InsideGanonCastle',
                  'Gerudo Valley': 'GerudoValley', 'Gerudo Fortress': 'GerudoFortress',
                  'Gerudo Training Ground': 'GerudoTrainingGround', 'Haunted Wasteland': 'HountedWasteland',
                  'Desert Colossus': 'DesertColossus', 'Spirit Temple': 'SpiritTemple',
                  'Lake Hylia': 'LakeHylia', 'Water Temple': 'WaterTemple', 'Lon Lon Ranch': 'LonLonRanch',
                  'Temple of Time': 'TempleOfTime'})
    locations, diagnostics, seen = [], [], set()
    for check in catalogue['checks']:
        ident = check['id']
        if ident in seen:
            raise ValueError(f'Identifiant en double dans le catalogue : {ident}')
        seen.add(ident)
        matches = by_id.get(ident, ())
        if not any(row['position'] is not None for row in matches) and ident in CATALOGUE_PLACEMENT_ALIASES:
            native = by_id.get(CATALOGUE_PLACEMENT_ALIASES[ident], ())
            matches = [row for row in native if row['position'] is not None] or matches
        if not matches and ident.isdecimal():
            # OotrR's original Kokiri chest mode uses the bare actor hash.
            matches = by_id.get('KokiriForest#' + ident, ())
        if not matches:
            candidates = (check.get('zone'), names.get(check.get('region'), check.get('region')),
                          ident.partition('#')[0])
            region = next((value for value in candidates if value in regions), None)
            if region is None:
                continue
            matches = [dict(resource='Emplacements sans position', position=None, region=region)]
        if all(row['position'] is None for row in matches):
            diagnostics.append(f'{ident}: coordonnées absentes pour ce check')
        for row in domain_adult_placements(matches):
            locations.append(dict(row, id=ident, name=check['name'],
                                  alias=row.get('name', ''), category=check['category']))
    result = dict(document, seed_id=catalogue['seed_id'], locations=locations,
                  diagnostics=diagnostics)
    load_metadata(result)
    return result
