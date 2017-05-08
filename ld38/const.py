import os
import re
import sys
from math import floor
from pathlib import Path
from enum import Enum, unique

from bearlibterminal import terminal
from clubsandwich.datastore import DataStore, CSVReader


root = Path(os.path.abspath(sys.argv[0])).parent


def _bool(val):
  return val.lower() in ('1', 'yes', 'true')

def _int(val):
  """
  Parse string as an int, even if it has decimals. This works around some
  dumb scim editor behavior.
  """
  return floor(float(val))

def _enum_value(TheEnum):
  def _specific_enum_value(val):
    try:
      return TheEnum[val]
    except KeyError:
      raise ValueError("Invalid value for enum {!r}: {!r}".format(TheEnum, val))
  return _specific_enum_value

def _int_or_star(val):
  return None if val == '*' else _int(val)

def _pipe_separated_uppercase(val):
  return None if val == '*' else set(s.upper() for s in val.split('|'))

def _pipe_separated(val):
  return val.split('|')

def _upper(val):
  return val.upper()

def _color(val):
  """
  Parse string as hex color string. scim does some dumb things like truncate,
  convert to float, and remove #, so fix all that crap.
  """
  if val.startswith('#'):
    return val  # already ok
  if val.endswith('.00'):
    val = val[:-3]
  while len(val) < 6:
    val = '0' + val
  return '#' + val


ITEM_RE = re.compile(r'(.*)x(\d+)')
def _items(val):
  if not val:
    return []
  items = []
  for s in val.split('|'):
    m = ITEM_RE.match(s)
    for _ in range(int(m.group(2))):
      items.append(m.group(1).upper())
  return items



class EnumUppercaseWithLookup(Enum):
  @classmethod
  def lookup(cls, k):
    return getattr(cls, k.upper())


@unique
class EnumMode(EnumUppercaseWithLookup):
  DEFAULT = 0
  CLOSE = 1
  THROW = 2


@unique
class EnumTerrain(EnumUppercaseWithLookup):
  EMPTY = 0
  FLOOR = 1
  WALL = 2
  DOOR_CLOSED = 3
  DOOR_OPEN = 4
  CORRIDOR = 5


@unique
class EnumFeature(EnumUppercaseWithLookup):
  NONE = 0
  STAIRS_UP = 1
  STAIRS_DOWN = 2


@unique
class EnumMonsterMode(EnumUppercaseWithLookup):
  DEFAULT = 0
  CHASING = 1
  FLEEING = 2
  SLEEPING = 3
  STUNNED = 4


@unique
class EnumRoomShape(EnumUppercaseWithLookup):
  BOX_RANDOM = 0
  BOX_FULL = 1


@unique
class EnumEventNames(EnumUppercaseWithLookup):
  key_u = "key_u"
  key_d = "key_d"
  key_l = "key_l"
  key_r = "key_r"
  key_ul = "key_ul"
  key_ur = "key_ur"
  key_dl = "key_dl"
  key_dr = "key_dr"
  key_get = "key_get"

  entity_moved = "entity_moved"
  entity_bumped = "entity_bumped"
  entity_died = "entity_died"
  entity_attacking = "entity_attacking"
  entity_attacked = "entity_attacked"
  entity_took_damage = "entity_took_damage"
  entity_picked_up_item = "entity_picked_up_item"
  entity_dropped_item = "entity_dropped_item"
  door_open = "door_open"
  player_took_action = "player_took_action"
  score_increased = "score_increased"

entity_names = DataStore('EntityName', (
  ('id', _upper),
  ('name', str),
  ('is_second_person', _bool),
))
entity_names.add_source(CSVReader(str(root / 'data' / 'names.csv')))

verbs = DataStore('Verb', (
  ('id', str),
  ('present_2p', str),
  ('present_3p', str),
))
verbs.add_source(CSVReader(str(root / 'data' / 'verbs.csv')))

room_types = DataStore('RoomType', (
  ('id', str),
  ('shape', _enum_value(EnumRoomShape)),
  ('difficulty', _int_or_star),
  ('monsters', _pipe_separated_uppercase),
  ('chance', float),
  ('color', _color),
  ('monster_density', float),
  ('item_density', float),
))
room_types.add_source(CSVReader(str(root / 'data' / 'rooms.csv')))

monster_types = DataStore('MonsterType', (
  ('id', _upper),
  ('char', str),
  ('color', _color),
  ('difficulty', _int),
  ('chance', float),
  ('behaviors', _pipe_separated),
  ('hp_max', _int),
  ('strength', _int),
  ('items', _items),
))
monster_types.add_source(CSVReader(str(root / 'data' / 'monsters.csv')))

def _float_list(str_list):
  return [float(s) for s in str_list]

item_types = DataStore('ItemType', (
  ('id', str),
  ('char', str),
  ('color', _color),
  ('chance_by_difficulty', _float_list),
))
class ItemTypeReader(CSVReader):
  """Combines cols 6-10 into a list"""
  def read(self):
    for line in super().read():
      yield line[:3] + [line[3:]]
item_types.add_source(ItemTypeReader(str(root / 'data' / 'items.csv')))

def _key_list(str_list):
  return [getattr(terminal, 'TK_' + s.strip()) for s in str_list]
key_bindings = DataStore('KeyBinding', (
  ('id', str),
  ('keys', _key_list)
))
class KeyBindingsReader(CSVReader):
  """Combines cols 1-end as list"""
  def read(self):
    for line in super().read():
      yield [line[0], line[1:]]
key_bindings.add_source(KeyBindingsReader(
  str(root / 'data' / 'key_bindings.csv'), skip_first_line=False))
