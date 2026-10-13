#Itamar Fishbine and Amit Navrotsky

import sys
import time
import random
import math
import queue
import multiprocessing
import pygame
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"  # hides all the "hello from..." prints it for every ball so it is annoying
def print_process_func(print_queue):

    while True:
        try:
            msg = print_queue.get(timeout=1.0)

        except queue.Empty:
            continue
        if msg == "STOP":
            break
        print(msg)


def ball_process_func(ball_id, ball_data, ball_to_detector_queue, print_queue):
    #changes the ball x,y every second (time.sleep)
    x, y, color, moves_left = ball_data

    # Send initial placement proposal
    ball_to_detector_queue.put({
        'id': ball_id,
        'x': x,
        'y': y,
        'color': color,
        'moves_left': moves_left
    })

    while moves_left > 0:
        time.sleep(1.0)  # Wait 1 second before jumping
        new_x = random.randint(20, 780)
        new_y = random.randint(20, 580)
        moves_left -= 1

        # Propose new position to Collision Detector
        ball_to_detector_queue.put({
            'id': ball_id,
            'x': new_x,
            'y': new_y,
            'color': color,
            'moves_left': moves_left
        })

    ball_to_detector_queue.put({'id': ball_id, 'status': 'FINISHED'})


def collision_detector_process_func(ball_to_detector_queue, detector_to_gui_queue, print_queue):
    #Validates proposals, resolves overlaps, and forwards final data

    active_balls = {}

    while True:
        try:
            data = ball_to_detector_queue.get(timeout=1.0)
        except queue.Empty:
            continue

        if data.get('status') == 'STOP':
            detector_to_gui_queue.put({'status': 'STOP'})
            break

        ball_id = data['id']

        if data.get('status') == 'FINISHED':
            if ball_id in active_balls:
                del active_balls[ball_id]
            detector_to_gui_queue.put({'type': 'REMOVE', 'id': ball_id})
            continue

        new_x = data['x']
        new_y = data['y']

        # Distance collision resolution loop[cite: 1]
        has_collision = True
        while has_collision:
            has_collision = False
            for other_id, other_ball in active_balls.items():
                if other_id == ball_id:
                    continue

                dist = math.sqrt((new_x - other_ball['x']) ** 2 + (new_y - other_ball['y']) ** 2)
                if dist < 40:  # Overlap detected
                    has_collision = True
                    print_queue.put(
                        f"overlap detected between Ball {ball_id} and Ball {other_id}! "
                        f"Relocating Ball {ball_id}."
                    )
                    new_x = random.randint(20, 780)
                    new_y = random.randint(20, 580)
                    break

        data['x'] = new_x
        data['y'] = new_y
        active_balls[ball_id] = data

        # Pass validated position to GUI
        detector_to_gui_queue.put({'type': 'UPDATE', 'ball': data})


if __name__ == '__main__':
    num_balls = int(input("Enter the number of balls: "))

    #starts all the multiprocceses
    print_queue = multiprocessing.Queue()
    ball_to_detector_queue = multiprocessing.Queue()
    detector_to_gui_queue = multiprocessing.Queue()

    # Start Print Process
    p_print = multiprocessing.Process(target=print_process_func, args=(print_queue,))
    p_print.start()

    # Start Detector Process
    p_detector = multiprocessing.Process(
        target=collision_detector_process_func,
        args=(ball_to_detector_queue, detector_to_gui_queue, print_queue)
    )
    p_detector.start()

    # Start Ball Processes amd create a color placement and amount of jumps
    ball_processes = []
    for i in range(num_balls):
        ball_data = [
            random.randint(20, 780),
            random.randint(20, 580),
            (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255)),
            random.randint(5, 25)
        ]
        p_ball = multiprocessing.Process(
            target=ball_process_func,
            args=(i, ball_data, ball_to_detector_queue, print_queue)
        )
        ball_processes.append(p_ball)
        p_ball.start()

    # Initialize Pygame GUI Process
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("My Jumping Balls (Multiprocessing IPC)")
    clock = pygame.time.Clock()

    rendered_balls = {} #balls that are printed on screen
    is_running = True
    last_count = -1
    has_started_balls = False

    while is_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False

        # Read all pending updates non-blockingly
        while True:
            try:
                msg = detector_to_gui_queue.get_nowait()
            except queue.Empty:
                break

            if msg.get('type') == 'UPDATE':
                ball = msg['ball']
                rendered_balls[ball['id']] = ball
                has_started_balls = True
            elif msg.get('type') == 'REMOVE':#removes ball if jumps are done
                ball_id = msg['id']
                rendered_balls.pop(ball_id, None)

        active_count = len(rendered_balls) #amouint of balls on screen so you can print

        # Print count updates when active ball total changes[cite: 1]
        if active_count != last_count:
            print_queue.put(f"Active balls on screen: {active_count}")
            last_count = active_count

        # Auto-exit when all balls finish their moves[cite: 1]
        if has_started_balls and active_count == 0:
            print_queue.put("all balls finished. Closing program.")
            is_running = False

        # Render screen in 60 fps
        screen.fill((0, 0, 0))
        for ball_id, ball in rendered_balls.items():
            pygame.draw.circle(screen, ball['color'], (ball['x'], ball['y']), 20)

        pygame.display.flip()
        clock.tick(60)

    # Destroy Pygame window immediately so it doesn't freeze on screen
    pygame.quit()

    # Disable queue join locks to prevent shutdown deadlocks
    print_queue.cancel_join_thread()
    ball_to_detector_queue.cancel_join_thread()
    detector_to_gui_queue.cancel_join_thread()

    # Clean up child ball processes
    for p in ball_processes:
        if p.is_alive():
            p.terminate()
            p.join(timeout=0.2)

    # Stop Collision Detector process
    ball_to_detector_queue.put({'status': 'STOP'})
    p_detector.join(timeout=1.0)
    if p_detector.is_alive():
        p_detector.terminate()

    # Stop Print process
    print_queue.put("STOP")
    p_print.join(timeout=1.0)
    if p_print.is_alive():
        p_print.terminate()

    sys.exit()