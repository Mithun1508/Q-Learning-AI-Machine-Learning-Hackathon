import pygame


class Tile:
  def __init__(self, x, y, z, tile_id, tile_size):
    self.x = x
    self.y = y
    self.z = z
    self.id = tile_id
    self.size = tile_size
    
    cart_x = y * tile_size[0]/2
    cart_y = x * tile_size[1]/2
    
    self.iso_x = cart_x - cart_y
    self.iso_y = (cart_x + cart_y)/2 - z * tile_size[1]/2
  
  @property
  def coords(self):
    return (self.x,self.y,self.z)
  
  @property
  def iso_coords(self):
    return (self.iso_x, self.iso_y)


class Sprite:
  def __init__(self, surf, pos):
    self.x = pos[0]
    self.y = pos[1]
    self.z = pos[2]
    self.surf = surf
    self.size = surf.get_size()
    
    cart_x = self.y * self.size[0]/2
    cart_y = self.x * self.size[1]/2
    
    self.iso_x = cart_x - cart_y
    self.iso_y = (cart_x + cart_y)/2 - self.z * self.size[1]/2


class Camera:
  def __init__(self, x, y):
    self.x = x
    self.y = y
    self.moved = False
  
  def move_x(self, dx):
    self.x += dx
    self.moved = True
  
  def move_y(self, dy):
    self.y += dy
    self.moved = True


class Scene:
  def __init__(self, game, screen_rect, scale=2.1):
    self.tile_data = {
      id:pygame.image.load(path).convert_alpha() for id, path in game.tile_data.items()
    }
    
    if scale != 1:
      self.tile_data = {
        id:pygame.transform.smoothscale(surf, 
          (round(surf.get_size()[0]*scale), surf.get_size()[1]*scale)
        ) for id, surf in self.tile_data.items()
      }
    
    self.tiles = set()
    
    for z, layer in enumerate(game.level.tiles):
      for y, row in enumerate(layer):
        for x, tile_id in enumerate(row):
          if tile_id:
            self.tiles.add(Tile(
              x, y, z, tile_id, self.tile_data[tile_id].get_size()
            ))
    
    self.tiles = sorted(self.tiles, key=lambda t: (t.z,t.y,t.x))
    
    self.tile_rects = {}
    
    for i, tile in enumerate(self.tiles):
      tile_pos = (tile.iso_x, tile.iso_y)
      
      tile_rect = pygame.Rect(tile_pos,tile.size)
      
      self.tile_rects[tile] = tile_rect
    
    self.object_data = {
      obj:pygame.image.load(path) for obj, path in game.object_data.items()
    }
    
    if scale != 1:
      self.object_data = {
        obj:pygame.transform.smoothscale(surf, 
          (round(surf.get_size()[0]*scale), surf.get_size()[1]*scale)
        ) for obj, surf in self.object_data.items()
      }
    
    self.screen_rect = screen_rect
    
    self.game_map_rect = pygame.Rect((0,0,0,0)).unionall(
      list(self.tile_rects.values())
    )
    
    start_x, start_y = self.game_map_rect.x, self.game_map_rect.y
    
    self.game_map_rect.center = screen_rect.center
    
    real_x, real_y = self.game_map_rect.x, self.game_map_rect.y
    
    self.camera = Camera(-start_x+real_x, -start_y+real_y)
    
    self.update_rects = []
    
    self.animations = {
      "intro":self.screen_rect.h/5
    }
  
  def render(self, screen, game):
    full_render = False
    
    if "intro" in self.animations:
      full_render = True
      
      animated_tile_render(screen, self.camera, self.tiles, self.tile_data, self.animations["intro"])
      
      self.animations["intro"] -= 1
      
      if self.animations["intro"] < 0:
        del self.animations["intro"]
        
        # small hack to update after animation, should make better implementation later
        self.camera.moved = True
    
    elif "exit" in self.animations:
      full_render = True
      
      reverse_animated_tile_render(screen, self.camera, self.tiles, self.tile_data, self.animations["exit"])
      
      self.animations["exit"] -= 1
      
      if self.animations["exit"] < 0:
        del self.animations["exit"]
        
        # small hack to update after animation, should make better implementation later
        self.camera.moved = True
    
    else:
      if self.camera.moved:
        full_render = True
        
        self.camera.moved = False
        
        self.tile_rects = {}
        
        render_tiles(screen, self.screen_rect, self.camera, self.tiles, self.tile_data, self.tile_rects)
      
      if not full_render:
        dirty_render_tiles(screen, self.camera, self.update_rects, self.tile_data, self.tile_rects)
      
      new_rects = render_sprites(screen, self.camera, game.level.objects, self.object_data)
      
      update_rects = new_rects + self.update_rects
      
      self.update_rects = new_rects
    
    if full_render:
      return True
    else:
      return update_rects


def render_tiles(screen, screen_rect, camera, tiles, tile_data, tile_rects):
  for i, tile in enumerate(tiles):
    tile_pos = (tile.iso_x+camera.x, tile.iso_y+camera.y)
    
    tile_rect = pygame.Rect(tile_pos,tile.size)
    
    tile_rects[tile] = tile_rect
    
    #if screen_rect.colliderect(tile_rect):
    screen.blit(tile_data[tile.id], tile_pos)

def dirty_render_tiles(screen, camera, update_rects, tile_data, tile_rects):
  for rect in update_rects:
    for tile, tile_rect in sorted(tile_rects.items(), key=lambda t:(t[0].z, t[0].y, t[0].x)):
      if rect.colliderect(tile_rect):
        screen.blit(
          tile_data[tile.id], (tile.iso_x + camera.x, tile.iso_y + camera.y)
        )

def render_sprites(screen, camera, objects, object_data):
  updated_rects = []
  
  for obj in objects.values():
    sprite = Sprite(object_data[obj["sprite"]], obj["pos"])
    
    update_rect = screen.blit(sprite.surf, (sprite.iso_x + camera.x, sprite.iso_y + camera.y))
    
    updated_rects.append(update_rect)
  
  return updated_rects

def animated_tile_render(screen, camera, tiles, tile_data, animation_count):
  for i, tile in enumerate(tiles):
    tile_pos = (tile.iso_x+camera.x, tile.iso_y+camera.y)
    
    tile_rect = pygame.Rect(tile_pos,tile.size)
    
    screen.blit(tile_data[tile.id], (tile_pos[0], tile_pos[1] - max(animation_count * 12 - i * 15, 0)))


def reverse_animated_tile_render(screen, camera, tiles, tile_data, animation_count):
  for i, tile in enumerate(tiles):
    tile_pos = (tile.iso_x+camera.x, tile.iso_y+camera.y)
    
    tile_rect = pygame.Rect(tile_pos,tile.size)
    
    screen.blit(tile_data[tile.id], (tile_pos[0], tile_pos[1] + (screen.get_size()[1]/5 - animation_count) * 10 - i * -(screen.get_size()[1]/5 - animation_count)))