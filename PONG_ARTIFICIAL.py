import pygame
from pygame.locals import *
from sys import exit
import random
import neat
import os
import math
import pickle

pygame.init()

# Tamanho da Tela
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

pygame.display.set_caption('PONG ARTIFICIAL')

# Limitações da Arena
start_line = 100
finish_line = SCREEN_HEIGHT - start_line

ball_speed = 5

# Cores
GREEN = (0, 255, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
BLACK = (0, 0, 0)

generation = 0
population = 0
tick = 200


class Player:
    def __init__(self, x, y, width, height, color):
        # Inicialização do Jogador
        self.speed = ball_speed * 2
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def move_top(self):
        # Mover para Cima
        self.speed = - ball_speed * 2

    def move_down(self):
        # Mover para Baixo
        self.speed = ball_speed * 2

    def move_stop(self):
        #Parar o Movimento
        self.speed = 0

    def move(self):
        # Impede Passar para Fora da Arena e Movimentar
        if self.rect.top <= start_line - self.speed:
            self.speed = 0
        if self.rect.bottom >= finish_line - self.speed:
            self.speed = 0
        self.rect = self.rect.move([0, self.speed])

    def move_ia(self, ball):
        # Move o Jogador 2 para seguir a bola
        if self.rect.centery < ball.rect.centery and self.rect.bottom + self.speed < finish_line:
            self.rect.y += self.speed
        elif self.rect.centery > ball.rect.centery and self.rect.top - self.speed > start_line:
            self.rect.y -= self.speed

    def draw(self, SCREEN):
        # Desenhar os Jogadores
        pygame.draw.rect(SCREEN, self.color, self.rect, 0, 20)
        pygame.draw.rect(SCREEN, WHITE, self.rect, 1, 20)

        #pygame.draw.line(SCREEN, self.color, (1, 2), (2, 3))


class Ball:
    def __init__(self, x, y, width, height, color):
        # Inicialização da Bola
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.angle = random.uniform(0, 2 * math.pi)  # Ângulo inicial da bola
        self.speed = ball_speed

        while -0.5 < self.speed * math.cos(self.angle) < 0.5:
            self.angle = random.uniform(0.1, 2 * math.pi)

    def change_move_y(self):
        # Rebate a Bola se bater na Lateral
        self.angle = -self.angle

    def change_move_x(self):
        # Rebate a Bola se bater no Jogador e altera o ângulo
        self.angle = math.pi - self.angle + random.uniform(-0.1 * math.pi, 0.1 * math.pi)
        while -0.5 < self.speed * math.cos(self.angle) < 0.5:
            self.angle = random.uniform(0.1, 2 * math.pi)

    def move(self):
        # Move a Bola pela Arena e Verifica sua colisão com as bordas
        if self.rect.bottom >= SCREEN_HEIGHT - start_line:
            self.rect.bottom = SCREEN_HEIGHT - start_line
            self.change_move_y()
        elif self.rect.top <= start_line:
            self.rect.top = start_line
            self.change_move_y()

        self.rect.x += self.speed * math.cos(self.angle)
        self.rect.y += self.speed * math.sin(self.angle)

        # Certifique-se de que a bola não fique presa nas bordas
        if self.rect.left <= start_line:
            self.rect.left = start_line
            self.angle = math.pi - self.angle
        elif self.rect.right >= SCREEN_WIDTH - start_line:
            self.rect.right = SCREEN_WIDTH - start_line
            self.angle = math.pi - self.angle

    def collide(self, player):
        # Verifica se a Bola bateu no jogador
        return self.rect.colliderect(player)

    def draw(self, SCREEN):
        # Desenha a Bola
        pygame.draw.circle(SCREEN, self.color, self.rect.center, self.width // 2)
        pygame.draw.circle(SCREEN, (255, 255, 255), self.rect.center, self.width // 2, 1)


def direction_ball_x():
    direcao = random.randint(1, 2)
    return 1 if direcao == 1 else -1


def draw_map():
    global generation, population
    # Desenha a Arena
    color_line = WHITE
    pygame.draw.line(SCREEN, color_line, (start_line, start_line), (SCREEN_WIDTH - start_line, start_line), 5)
    pygame.draw.line(SCREEN, color_line, (start_line, finish_line), (SCREEN_WIDTH - start_line, finish_line), 5)
    pygame.draw.line(SCREEN, color_line, (start_line, start_line), (start_line, SCREEN_HEIGHT - start_line), 5)
    pygame.draw.line(SCREEN, color_line, (SCREEN_WIDTH - start_line, SCREEN_HEIGHT - start_line),
                     (SCREEN_WIDTH - start_line, start_line), 5)

    # Exibir a geração atual
    generation_font = pygame.font.Font(None, 36)
    generation_label = generation_font.render(f'Geração: {generation}', True, WHITE)
    population_label = generation_font.render(f'População: {population}', True, WHITE)
    ia_label = generation_font.render('IA', True, WHITE)
    bot_label = generation_font.render('BOT', True, WHITE)

    SCREEN.blit(generation_label, (10, 10))
    SCREEN.blit(population_label, (10, 50))
    SCREEN.blit(ia_label, (start_line + 20, finish_line + 20))
    SCREEN.blit(bot_label, (SCREEN_WIDTH - 160, finish_line + 20))


def eval_genomes(genomes, config):
    global generation, population, tick

    # Funções de Tela
    clock = pygame.time.Clock()
    color = GRAY
    FITNESS = 50000

    # Geração
    generation += 1

    # Valores padrões do Jogador
    width_player = 10
    height_player = 70
    y_player = SCREEN_HEIGHT // 2 - 35

    # Valores de Localização X dos Players
    x_player_1 = start_line + 25
    x_player_2 = SCREEN_WIDTH - start_line - 25

    # Valores da Bola
    x_ball = SCREEN_WIDTH // 2 + 35
    width_ball = 15
    height_ball = 15

    # Jogadores e Suas Redes Neurais
    player_one = []
    player_two = []
    balls = []
    nets = []
    ge = []

    for genome_id, g in genomes:
        population += 1

        # Parâmetros da IA
        BALL_AND_PLAYER_COLOR = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        BALL_LOCAL_Y = random.randint(start_line + 100, finish_line - 100)

        # Criar a Rede Neural
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)

        # Adicionar os jogadores e Bola
        player_one.append(Player(x_player_1, y_player, width_player, height_player, BALL_AND_PLAYER_COLOR))
        player_two.append(Player(x_player_2, y_player, width_player, height_player, BALL_AND_PLAYER_COLOR))

        balls.append(Ball(x_ball, BALL_LOCAL_Y, width_ball, height_ball, BALL_AND_PLAYER_COLOR))

        # Sistema de Ganhos
        g.fitness = 0
        ge.append(g)

    run = True

    while run:
        clock.tick(tick)
        SCREEN.fill(color)
        
        # Sair do Jogo e Aumento de Velocidade
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()

            if event.type == KEYUP:
                if event.key == K_UP:
                    tick += 100

                if event.key == K_DOWN:
                    tick -= 100

        # Desenhar Jogador 1
        for p1 in player_one:
            p1.draw(SCREEN)

        # Desenhar Jogador 2
        for p2 in player_two:
            p2.draw(SCREEN)

        # Desenhar Bola
        for b in balls:
            b.draw(SCREEN)
            b.move()

        # Código para lidar com a colisão com os jogadores
        for ball in balls:
            # Colisão com Jogadores
            if ball.collide(player_one[balls.index(ball)]) or ball.collide(player_two[balls.index(ball)]):
                if ball.collide(player_one[balls.index(ball)]):
                    ge[balls.index(ball)].fitness += 1000
                    ball.change_move_x()
                    ball.rect.left = player_one[balls.index(ball)].rect.right + 1

                elif ball.collide(player_two[balls.index(ball)]):
                    ball.change_move_x()
                    ball.rect.right = player_two[balls.index(ball)].rect.left - 1


            # Eliminar jogador caso a bola passe dele
            elif ball.rect.left <= start_line or ball.rect.right >= SCREEN_WIDTH - start_line:
                ge[balls.index(ball)].fitness -= 2000
                idx = balls.index(ball)
                player_one.pop(idx)
                player_two.pop(idx)
                balls.pop(idx)
                nets.pop(idx)
                ge.pop(idx)
                population -= 1

        # Rede neural Da IA e criação do seu movimento
        for i, move_player_1 in enumerate(player_one):
            move_player_1.move()
            output = nets[i].activate((move_player_1.rect.centery,
                                       abs(move_player_1.rect.centerx - balls[i].rect.centerx),
                                       balls[i].rect.centery))
            if output[0] > output[1]:
                if output[0] > 0.5:
                    move_player_1.move_top()
            elif output[1] > 0.5:
                move_player_1.move_down()

        for player_t, ball in zip(player_two, balls):
            player_t.move_ia(ball)

        # Reiniciar jogo se bola o número de bolas for 0
        if len(balls) <= 0 or ge[balls.index(ball)].fitness > FITNESS:
            break

        # Desenhar o mapa e atualizar cenário constantemente
        draw_map()
        pygame.display.update()

# Rodar Jogo e Redes Neurais
def run(config_file):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet,
                                neat.DefaultStagnation, config_file)
    p = neat.Population(config)
    p.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)
    winner = p.run(eval_genomes, 50)
    print(f'Best genome:\n{winner}')

    with open('best_genomes.pkl', 'wb') as f:
        pickle.dump(winner, f)


if __name__ == '__main__':
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'neat_config.txt')
    run(config_path)
