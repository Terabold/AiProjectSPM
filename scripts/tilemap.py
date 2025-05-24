# tilemap.py
import json
import pygame
from scripts.constants import PHYSICS_TILES, INTERACTIVE_TILES, SPIKE_SIZE, NEIGHBOR_OFFSETS, AUTOTILE_TYPES, AUTOTILE_MAP

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
        self.lowest_y = 0
    
    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles
    
    def extract(self, id_pairs, keep=False):
        matches = []
        
        # Handle offgrid tiles
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
        
        # Handle grid tiles
        processed = set()
        for loc in list(self.tilemap.keys()):
            if loc in processed:
                continue
                
            tile = self.tilemap[loc]
            base_type = tile['type'].split()[0]
            
            # Check if this tile matches our search
            if not any(base_type == target_type and tile['variant'] == target_variant 
                      for target_type, target_variant in id_pairs):
                continue
            
            # Handle split tiles (finish up/down)
            if tile['type'].endswith(' up'):
                down_loc = f"{tile['pos'][0]};{tile['pos'][1] + 1}"
                # Always create match from the 'up' tile position
                match = self._create_match(tile, base_type)
                matches.append(match)
                processed.update([loc, down_loc])
                if not keep:
                    del self.tilemap[loc]
                    if down_loc in self.tilemap:
                        del self.tilemap[down_loc]
            elif not tile['type'].endswith(' down'):  # Regular tiles
                match = self._create_match(tile, base_type)
                matches.append(match)
                processed.add(loc)
                if not keep:
                    del self.tilemap[loc]
        
        return matches
    
    def _create_match(self, tile, base_type):
        match = tile.copy()
        match['type'] = base_type
        match['pos'] = [tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size]
        return match

    def autotile(self):
        for tile in self.tilemap.values():
            if tile['type'] not in AUTOTILE_TYPES:
                continue
                
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = f"{tile['pos'][0] + shift[0]};{tile['pos'][1] + shift[1]}"
                if check_loc in self.tilemap and self.tilemap[check_loc]['type'] == tile['type']:
                    neighbors.add(shift)
            
            neighbors = tuple(sorted(neighbors))
            if neighbors in AUTOTILE_MAP:
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def _handle_spawners(self, path_for_save=False):
        spawner_tiles = self.extract([('spawners', 0), ('spawners', 1)], keep=True)
        if len(spawner_tiles) > 1:
            self.extract([('spawners', 0), ('spawners', 1)], keep=False)
            spawner = spawner_tiles[0]
            pos = spawner['pos'].copy()
            
            # Convert to tile coordinates if needed
            if len(str(pos[0]).split('.')) == 1:
                pos = [pos[0] // self.tile_size, pos[1] // self.tile_size]
            
            tile_loc = f"{int(pos[0])};{int(pos[1])}"
            self.tilemap[tile_loc] = {
                'type': spawner['type'], 
                'variant': spawner['variant'], 
                'pos': [int(pos[0]), int(pos[1])]
            }

    def save(self, path):
        self.lowest_y = max((tile['pos'][1] for tile in self.tilemap.values()), default=0)
        self._handle_spawners()
        
        with open(path, 'w') as f:
            json.dump({
                'tilemap': self.tilemap, 
                'offgrid': self.offgrid_tiles,
                'lowest_y': self.lowest_y,
            }, f, indent=4)
        
    def load(self, path):
        with open(path, 'r') as f:
            map_data = json.load(f)
        self.tilemap = map_data['tilemap']
        self.offgrid_tiles = map_data['offgrid']
        self.lowest_y = map_data.get('lowest_y', 0)
        self._handle_spawners()
    
    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile['type'].split()[0] in PHYSICS_TILES:
                rects.append(pygame.Rect(
                    tile['pos'][0] * self.tile_size, 
                    tile['pos'][1] * self.tile_size, 
                    self.tile_size, self.tile_size
                ))
        return rects
    
    def _get_spike_rect(self, tile):
        spike_w, spike_h = int(self.tile_size * SPIKE_SIZE[0]), int(self.tile_size * SPIKE_SIZE[1])
        rotation = tile.get('rotation', 0)
        tile_x, tile_y = tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size
        
        positions = {
            0: (tile_x + (self.tile_size - spike_w) // 2, tile_y + (self.tile_size - spike_h), spike_w, spike_h),
            90: (tile_x + (self.tile_size - spike_h), tile_y + (self.tile_size - spike_w) // 2, spike_h, spike_w),
            180: (tile_x + (self.tile_size - spike_w) // 2, tile_y, spike_w, spike_h),
            270: (tile_x, tile_y + (self.tile_size - spike_w) // 2, spike_h, spike_w)
        }
        return pygame.Rect(*positions.get(rotation, positions[0]))

    def interactive_rects_around(self, pos):
        tiles = []
        for tile in self.tiles_around(pos):
            base_type = tile['type'].split()[0]
            if base_type not in INTERACTIVE_TILES:
                continue
                
            match base_type:
                case 'finish':
                    if tile['type'] in ['finish up', 'finish']:
                        rect = pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, 
                                         self.tile_size, self.tile_size * 2)
                        tiles.append((rect, (base_type, tile['variant'])))
                    elif tile['type'] == 'finish down':
                        # Only add if no corresponding 'up' tile exists
                        up_loc = f"{tile['pos'][0]};{tile['pos'][1] - 1}"
                        if up_loc not in self.tilemap or self.tilemap[up_loc]['type'] != 'finish up':
                            rect = pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, 
                                             self.tile_size, self.tile_size)
                            tiles.append((rect, (base_type, tile['variant'])))
                case 'spikes':
                    tiles.append((self._get_spike_rect(tile), (base_type, tile['variant'])))
                case 'kill':
                    rect = pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, 
                                     self.tile_size, self.tile_size)
                    tiles.append((rect, (base_type, tile['variant'])))
        return tiles
    
    def is_below_map(self, entity_pos, tiles_threshold=2):
        return entity_pos[1] > (self.lowest_y + tiles_threshold) * self.tile_size

    def _get_image(self, tile_type, variant):
        asset = self.game.assets[tile_type]
        return asset.img() if hasattr(asset, 'img') else asset[variant]

    def render(self, surf, offset=(0, 0), zoom=10):
        # Render offgrid tiles
        for tile in self.offgrid_tiles:
            if tile['type'] == 'spikes' and 'rotation' in tile:
                img = self.game.get_rotated_image(tile['type'], tile['variant'], tile['rotation'])
                x = tile['pos'][0] * self.tile_size - offset[0] - (img.get_width() - self.tile_size) // 2
                y = tile['pos'][1] * self.tile_size - offset[1] - (img.get_height() - self.tile_size) // 2
            else:
                img = self._get_image(tile['type'], tile['variant'])
                x = tile['pos'][0] * self.tile_size - offset[0]
                y = tile['pos'][1] * self.tile_size - offset[1]
            surf.blit(img, (x, y))
                    
        # Render grid tiles
        for tile in self.tilemap.values():
            if tile['type'].endswith(' down'):  # Skip down parts to avoid duplicates
                continue
                
            base_type = tile['type'].split()[0]
            x_pos = tile['pos'][0] * self.tile_size - offset[0]
            y_pos = tile['pos'][1] * self.tile_size - offset[1]
            
            if base_type == 'spikes' and 'rotation' in tile:
                img = self.game.get_rotated_image(base_type, tile['variant'], tile['rotation'])
                x_pos -= (img.get_width() - self.tile_size) // 2
                y_pos -= (img.get_height() - self.tile_size) // 2
            elif base_type == 'finish':
                img = self._get_image(base_type, tile['variant'])
                if img.get_height() != self.tile_size * 2:
                    img = pygame.transform.scale(img, (self.tile_size, self.tile_size * 2))
            else:
                img = self._get_image(base_type, tile['variant'])
            
            surf.blit(img, (x_pos, y_pos))