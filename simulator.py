import pygame
import os
import map_defs as md
import map as map_obj
import administrators as vms_lib
import car as car_obj

def main():
    # Init pygame
    pygame.init()
    clock = pygame.time.Clock()

    # set screen location
    x = 10
    y = 150
    os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (x, y)

    # Create screen
    screen_width = 600
    screen_height = 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Driving Simulator")

    # load data for maps
    maps = md.load()
    map_idx = -1

    # Car
    car = car_obj.ObjCar(pygame, screen, 'images/vehicle_car_24.png', 0)

    running = True
    while running:
        # Map
        map_idx = (map_idx + 1) % len(maps)
        map = map_obj.ObjMap(pygame, screen, car, maps[map_idx])

        # Management System
        vms = vms_lib.VehicleManagementSystem(pygame, screen, map)

        # game loop
        driving = True
        while driving:
            # This limits the while loop to a max of 15 times per second.
            # It helps create a common game speed across processors
            # Otherwise, the game will use all possible CPU.
            clock.tick(15)

            screen.fill((146, 154, 166))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    driving = False
                    running = False

            map.update()
            map.draw()
            if vms.update() == 'arrived':
                car.reset()
                break
            car.draw()

            #test.update()

            pygame.display.flip()


if __name__ == "__main__":
    main()
