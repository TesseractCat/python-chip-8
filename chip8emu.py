import pygame, pygame.gfxdraw
import random
import time
import sys

memory = 4096*[0]
v = 16*[0]
i = 0
pc = 0x200
gfx = [[0]*32 for _ in range(64)]
sounds_timer = 0
delay_timer = 0
stack = 16*[0]
sp = 0
key = 16*[0]

def load_rom(name = "PONG", pos = 0x200):
    with open(name, "rb") as f:
        pos_in_list = 0
        for n in list(f.read()):
            memory[pos + pos_in_list] = n
            pos_in_list += 1

#print(memory)

def msb(n):
  ndx = 0
  while ( 1 < n ):
    n = ( n >> 1 )
    ndx += 1
  return ndx

def do_cycle():
    global pc
    global memory
    global v
    global i
    global gfx
    global delay_timer
    global sounds_timer
    global stack
    global sp
    global key
    
    opcode = memory[pc] << 8 | memory[pc + 1]

    #print("Running opcode: " + hex(opcode))
    
    if opcode == 0x00E0:
        #00E0   Clears the screen.
        #print("Not implemented - Screen cleared")
        gfx = [[0]*32 for _ in range(64)]
        pc += 2
    elif opcode == 0x00EE:
        #00EE	Returns from a subroutine.
        sp -= 1
        pc = stack[sp]
    elif opcode & 0xF000 == 0x1000:
        #1NNN	Jumps to address NNN.
        pc = opcode & 0x0FFF
    elif opcode & 0xF000 == 0x2000:
        #2NNN	Calls subroutine at NNN.
        stack[sp] = pc
        sp += 1
        pc = opcode & 0x0FFF
    elif opcode & 0xF000 == 0x3000:
        #3XNN	Skips the next instruction if VX equals NN.
        if v[(opcode & 0x0F00) >> 8] == (opcode & 0x00FF):
            pc += 4
        else:
            pc += 2
    elif opcode & 0xF000 == 0x4000:
        #4XNN	Skips the next instruction if VX doesn't equal NN.
        if v[(opcode & 0x0F00) >> 8] != 0x00FF:
            pc += 4
        else:
            pc += 2
    elif opcode & 0xF000 == 0x5000:
        #5XY0	Skips the next instruction if VX equals VY.
        if v[(opcode & 0x0F00) >> 8] == v[(opcode & 0x00F0) >> 4]:
            pc += 4
        else:
            pc += 2
    elif opcode & 0xF000 == 0x6000:
        #6XNN	Sets VX to NN.
        v[(opcode & 0x0F00) >> 8] = opcode & 0x00FF
        pc += 2
    elif opcode & 0xF000 == 0x7000:
        #7XNN	Adds NN to VX.
        v[(opcode & 0x0F00) >> 8] = v[(opcode & 0x0F00) >> 8] + (opcode & 0x00FF)
        pc += 2
    elif opcode & 0xF00F == 0x8000:
        #8XY0	Sets VX to the value of VY.
        v[(opcode & 0x0F00) >> 8] = v[(opcode & 0x00F0) >> 4]
        pc += 2
    elif opcode & 0xF00F == 0x8001:
        #8XY1	Sets VX to VX or VY.
        v[(opcode & 0x0F00) >> 8] = v[(opcode & 0x0F00) >> 8] | v[(opcode & 0x00F0) >> 4]
        pc += 2
    elif opcode & 0xF00F == 0x8002:
        #8XY2	Sets VX to VX and VY.
        v[(opcode & 0x0F00) >> 8] = v[(opcode & 0x0F00) >> 8] & v[(opcode & 0x00F0) >> 4]
        pc += 2
    elif opcode & 0xF00F == 0x8003:
        #8XY3	Sets VX to VX xor VY.
        v[(opcode & 0x0F00) >> 8] = v[(opcode & 0x0F00) >> 8] ^ v[(opcode & 0x00F0) >> 4]
        pc += 2
    elif opcode & 0xF00F == 0x8004:
        #8XY4	Adds VY to VX. VF is set to 1 when there's a carry, and to 0 when there isn't. -- IF IT DOESN'T WORK CHECK FORUM POST
        temp = v[(opcode & 0x0F00) >> 8] + v[(opcode & 0x00F0) >> 4]
        if temp > 255:
            v[(opcode & 0x0F00) >> 8] = temp - 256
            v[0xF] = 1
        else:
            v[(opcode & 0x0F00) >> 8] = temp
            v[0xF] = 0
        pc += 2
    elif opcode & 0xF00F == 0x8005:
        #8XY5	VY is subtracted from VX. VF is set to 0 when there's a borrow, and 1 when there isn't. -- IF IT DOESN'T WORK CHECK FORUM POST
        temp = v[(opcode & 0x0F00) >> 8] - v[(opcode & 0x00F0) >> 4]
        if temp < 0:
            v[(opcode & 0x0F00) >> 8] = temp + 256
            v[0xF] = 0
        else:
            v[(opcode & 0x0F00) >> 8] = temp
            v[0xF] = 1
        pc += 2
    elif opcode & 0xF00F == 0x8006:
        #8XY6	Shifts VX right by one. VF is set to the value of the least significant bit of VX before the shift. -- CORRECT?
        v[0xF] = v[(opcode & 0x0F00) >> 8] & 1
        v[(opcode & 0x0F00) >> 8] = v[(opcode & 0x0F00) >> 8] >> 1
    elif opcode & 0xF00F == 0x8007:
        #8XY7	Sets VX to VY minus VX. VF is set to 0 when there's a borrow, and 1 when there isn't. -- IF IT DOESN'T WORK CHECK FORUM POST
        temp = v[(opcode & 0x00F0) >> 4] - v[(opcode & 0x0F00) >> 8]
        if temp < 0:
            v[(opcode & 0x0F00) >> 8] = temp + 256
            v[0xF] = 0
        else:
            v[(opcode & 0x0F00) >> 8] = temp
            v[0xF] = 1
        pc += 2
    elif opcode & 0xF00F == 0x800E:
        #8XYE	Shifts VX left by one. VF is set to the value of the most significant bit of VX before the shift. -- CORRECT?
        v[0xF] = msb(v[(opcode & 0x0F00) >> 8])
        v[(opcode & 0x0F00) >> 8] = v[(opcode & 0x0F00) >> 8] << 1
    elif opcode & 0xF00F == 0x9000:
        #9XY0	Skips the next instruction if VX doesn't equal VY.
        if v[(opcode & 0x0F00) >> 8] != v[(opcode & 0x00F0) >> 4]:
            pc += 4
        else:
            pc += 2
    elif opcode & 0xF000 == 0xA000:
        #ANNN	Sets I to the address NNN.
        i = opcode & 0x0FFF
        pc+=2
    elif opcode & 0xF000 == 0xB000:
        #BNNN	Jumps to the address NNN plus V0.
        i = opcode & 0x0FFF
        pc+=2
    elif opcode & 0xF000 == 0xC000:
        #CXNN	Sets VX to the result of a bitwise and operation on a random number and NN.
        v[(opcode & 0x0F00) >> 8] = random.randint(0, 255) & (opcode & 0x00FF)
        pc+=2
    elif opcode & 0xF000 == 0xD000:
        #DXYN	Draws a sprite at coordinate (VX, VY) that has a width of 8 pixels and a height of N pixels.
        #print("Drawing sprite! I = {}".format(i))
        co_x = v[(opcode & 0x0F00) >> 8]
        co_y = v[(opcode & 0x00F0) >> 4]
        #co_x = (opcode & 0x0F00) >> 8
        #co_y = (opcode & 0x00F0) >> 4
        height = (opcode & 0x000F)

        v[0xF] = 0

        for y in range(0, height):
            pixel = memory[i + y]
            for x in range(0,8):
                try: pix = int("{0:b}".format(pixel)[x])
                except: pix = 0

                #if pix == 1:
                    #print("SETTING SPRITE PIXEL AT: {} {} {}".format(x, y, height))

                try:
                    if gfx[co_x + x][co_y + y] == 1:
                        v[0xF] = 1
                    gfx[co_x + x][co_y + y] ^= pix #int(bin(pixel)[2+x])
                except:
                    pass
        
        pc += 2
    elif opcode & 0xF0FF == 0xE09E:
        #EX9E	Skips the next instruction if the key stored in VX is pressed.
        if key[(opcode & 0x0F00) >> 8] == 1:
            pc += 4
        else:
            pc += 2
    elif opcode & 0xF0FF == 0xE0A1:
        #EXA1	Skips the next instruction if the key stored in VX isn't pressed.
        if key[(opcode & 0x0F00) >> 8] != 1:
            pc += 4
        else:
            pc += 2
    elif opcode & 0xF0FF == 0xF007:
        #FX07	Sets VX to the value of the delay timer.
        v[(opcode & 0x0F00) >> 8] = delay_timer
        pc += 2
    elif opcode & 0xF0FF == 0xF00A:
        #FX0A	A key press is awaited, and then stored in VX. -- HOW TO GET KEY
        v[(opcode & 0x0F00) >> 8] = input("Enter key -> ")
        pc += 2
    elif opcode & 0xF0FF == 0xF015:
        #FX15	Sets the delay timer to VX.
        delay_timer = v[(opcode & 0x0F00) >> 8]
        pc += 2
    elif opcode & 0xF0FF == 0xF018:
        #FX18	Sets the sound timer to VX.
        sound_timer = v[(opcode & 0x0F00) >> 8]
        pc += 2
    elif opcode & 0xF0FF == 0xF01E:
        #FX1E	Adds VX to I.
        i += v[(opcode & 0x0F00) >> 8]
        pc += 2
    elif opcode & 0xF0FF == 0xF029:
        #FX29	Sets I to the location of the sprite for the character in VX. Characters 0-F (in hexadecimal) are represented by a 4x5 font.
        print("Not implemented - Program attempted to set I to sprite but im evil hue hue")
        sys.exit()
        pc += 2
    elif opcode & 0xF0FF == 0xF033:
        #FX33	Stores the binary-coded decimal representation of VX, with the most significant of three digits at the address in I, the middle digit at I plus 1, and the least significant digit at I plus 2.
        memory[i] = v[(opcode & 0x0F00) >> 8] / 100
        memory[i+1] = (v[(opcode & 0x0F00) >> 8] / 10) % 10
        memory[i+2] = (v[(opcode & 0x0F00) >> 8] % 100) % 10
        pc += 2
    elif opcode & 0xF0FF == 0xF055:
        #Stores V0 to VX (including VX) in memory starting at address I.
        for x in range(0, (opcode & 0x0F00) >> 8):
            memory[i+x] = v[x]
        pc += 2
    elif opcode & 0xF0FF == 0xF065:
        #FX65	Fills V0 to VX (including VX) with values from memory starting at address I.
        for x in range(0, (opcode & 0x0F00) >> 8):
            v[x] = memory[i+x]
        pc += 2
    else:
        print("UNKNOWN OPCODE!")
        pc += 2
        
    if delay_timer > 0:
        delay_timer -= 1

#Pygame setup
white = (255,255,255)
black = (0,0,0)
scale_factor = 10

pygame.init()

screen = pygame.display.set_mode((64 * scale_factor,32 * scale_factor))

pygame.display.set_caption("CHIP-8 Emulator")
#Done

#input("Go? -> ")

load_rom(name = "FONTS", pos = 0)
load_rom(name = "INVADERS")

while True:
    key = 16 * [0]

    keys=pygame.key.get_pressed()
    for k in range(0, len(keys)):
        if keys[k] == 1:
            print("{} - {}".format(k, keys[k]))
            try:
                key[k-48] = 1
            except:
                pass


    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        #key[int(keys.name(event.key))] = 1
        #if event.type == pygame.KEYDOWN:
        #   key[int(pygame.key.name(event.key))] = 1
        #    print(key)
        #    #input(pygame.key.name(event.key))
        
    screen.fill(black)

    for x in range(0, len(gfx)):
        #print(
        for y in range(0, len(gfx[x])):
            if gfx[x][y] == 1:
                #print("Doing draw at {} {}".format(x,y))
                pygame.gfxdraw.box(screen, ((x * scale_factor, y * scale_factor), (scale_factor, scale_factor)), white)
    
    pygame.display.flip()
    #print(v)
    #print(i)
    do_cycle()
