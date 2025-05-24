import random
from scripts.utils import Animation
from scripts.constants import BASE_IMG_DUR
import math


class StarAnimated:
    def __init__(self, pos, anim: Animation, depth, anim_offset=0):
        self.pos = pos
        self.anim = anim.copy()
        self.anim.frame = anim_offset  # random starting frame
        self.depth = depth

    def update(self, dt=1.0):
        self.anim.update(dt)

    def render(self, surf, offset=(0, 0)):
        render_pos = (
            self.pos[0] - offset[0] * self.depth,
            self.pos[1] - offset[1] * self.depth
        )
        img = self.anim.img()
        x = render_pos[0] % (surf.get_width() + img.get_width()) - img.get_width()
        y = render_pos[1] % (surf.get_height() + img.get_height()) - img.get_height()
        surf.blit(img, (x, y))


class StarsAnimated:
    def __init__(self, base_images, display_size, count=50, min_dist=100):
        self.stars = []
        positions = []

        for _ in range(count):
            while True:
                pos = (random.random() * 99999, random.random() * 99999)
                if all(math.dist(pos, p) >= min_dist for p in positions):
                    positions.append(pos)
                    break
            
            depth = random.uniform(0.4, 1.0)
            img_dur = BASE_IMG_DUR + random.randint(0, 5)
            anim = Animation(base_images, img_dur=img_dur, loop=True)
            anim.frame = random.uniform(0, img_dur * len(base_images))
            self.stars.append(StarAnimated(pos, anim, depth))

        self.stars.sort(key=lambda star: star.depth)

    def update(self, dt=1.0):
        for star in self.stars:
            star.update(dt)

    def render(self, surf, offset=(0, 0)):
        for star in self.stars:
            star.render(surf, offset=offset)
