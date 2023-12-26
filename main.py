import pygame
import os

from game import Game
import render

os.environ["WANDB_CONSOLE"] = "wrap"


pygame.init()

flags = pygame.FULLSCREEN | pygame.DOUBLEBUF

screen = pygame.display.set_mode((0,0), flags, 16)

screen_w, screen_h = screen.get_size()


def main(fps=40):
  game = Game()
  
  #game.train()
  game.load_model("models/model-879.pkl")
  
  scene = render.Scene(game, screen.get_rect())
  
  clock = pygame.time.Clock()
  
  pygame.event.set_allowed([pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.KEYDOWN, pygame.KEYUP])
  
  ticks = 0
  
  data = ""
  
  font = pygame.font.SysFont(None, 20)
  
  font_update_rect = pygame.Rect((5,25),(50,100))
  
  font_renders = []
  
  msg_render = font.render("WASD/Arrow Keys to move camera",True,(0,0,0))
  
  while True:
    for event in pygame.event.get():
      if event.type == pygame.QUIT:
        pygame.quit()
    
    ticks += 1
    
    if ticks == fps:
      ticks = 0
      
      if "intro" not in scene.animations and "exit" not in scene.animations:
        data = game.step()
        
        if data:
          font_renders = [
            font.render(d,True,(0,0,0)) for d in data
          ]
        
        if game.end == True:
          break # for now
        
        elif game.level_complete == True:
          scene.animations["exit"] = screen_h/5
    
    if game.level_complete and "exit" not in scene.animations:
      game.level_complete = False
      
      scene = render.Scene(game, screen.get_rect())
    
    game.update(fps)
    
    screen.fill("white")
    
    screen.blit(msg_render, (10,10))
    
    for i, r in enumerate(font_renders):
      screen.blit(r, (10,30+i*20))
    
    keys = pygame.key.get_pressed()
    
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
      scene.camera.move_x(3)
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
      scene.camera.move_x(-3)
    if keys[pygame.K_w] or keys[pygame.K_UP]:
      scene.camera.move_y(3)
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
      scene.camera.move_y(-3)
    
    update_rects = scene.render(screen, game)
    
    if update_rects == True:
      pygame.display.flip()
    else:
      pygame.display.update(update_rects+[font_update_rect])
    
    clock.tick(fps)

if __name__ == "__main__":
  main()