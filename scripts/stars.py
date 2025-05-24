import random
from scripts.utils import Animation
from scripts.constants import BASE_IMG_DUR
import math


import pygame

class StarAnimated:
    def __init__(self, pos, anim: Animation, depth, anim_offset=0, scale=1.0):
        self.pos = pos
        self.anim = anim.copy()
        self.anim.frame = anim_offset
        self.depth = depth
        self.scale = scale
        self._scaled_image_cache = None
        self._last_frame = -1

    def update(self, dt=1.0):
        self.anim.update(dt)

    def render(self, surf, offset=(0, 0)):
        render_pos = (
            self.pos[0] - offset[0] * self.depth,
            self.pos[1] - offset[1] * self.depth
        )
        img = self.anim.img()

        # Cache scaled image to avoid rescaling every frame if not changed
        if self._last_frame != int(self.anim.frame) or self._scaled_image_cache is None:
            size = (int(img.get_width() * self.scale), int(img.get_height() * self.scale))
            self._scaled_image_cache = pygame.transform.smoothscale(img, size)
            self._last_frame = int(self.anim.frame)

        scaled_img = self._scaled_image_cache

        x = render_pos[0] % (surf.get_width() + scaled_img.get_width()) - scaled_img.get_width()
        y = render_pos[1] % (surf.get_height() + scaled_img.get_height()) - scaled_img.get_height()

        surf.blit(scaled_img, (x, y))

class StarsAnimated:
    def __init__(self, base_images, display_size, count=200, min_dist=30):
        self.stars = []
        positions = []

        BASE_IMG_DUR = 20  # base duration for slower animation

        for _ in range(count):
            # Find a non-overlapping position
            while True:
                pos = (random.random() * 99999, random.random() * 99999)
                if all(math.dist(pos, p) >= min_dist for p in positions):
                    positions.append(pos)
                    break
            
            depth = random.uniform(0.4, 1.0)
            img_dur = BASE_IMG_DUR + random.randint(0, 5)
            anim = Animation(base_images, img_dur=img_dur, loop=True)
            anim_offset = random.uniform(0, img_dur * len(base_images))
            scale = random.uniform(0.5, 1.5)

            self.stars.append(StarAnimated(pos, anim, depth, anim_offset, scale))

        self.stars.sort(key=lambda star: star.depth)

    def update(self, dt=1.0):
        for star in self.stars:
            star.update(dt)

    def render(self, surf, offset=(0, 0)):
        for star in self.stars:
            star.render(surf, offset=offset)