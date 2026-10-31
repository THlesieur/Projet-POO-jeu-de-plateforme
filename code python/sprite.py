
import pygame
import math

#variable time
time = pygame.time.Clock().tick(60) / 1000

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        #variables utiles au code du joueur
        self.name = "player"
        self.spritesheet = pygame.image.load("../sprites/persos/character_sprite_sheet (2).png").convert_alpha()
        self.width = 32
        self.height = 64
        self.image = self.get_sprite(0, 0)

        #spritesheet de la main du joueur pour redessiner au dessus de l'arme tenue
        self.hands_spritesheet = pygame.image.load("../sprites/persos/hand_character.png").convert_alpha()
        self.hand_image = pygame.Surface((8, 8), pygame.SRCALPHA)

        self.entity = True
        self.ennemi = False

        self.position = [x, y]

        # Obtenir le rectangle englobant l'image
        self.rect = self.image.get_rect()

        self.rect.bottomleft = self.position

        #creation hitbox
        self.hitbox = pygame.Rect(self.rect.left , self.rect.right , self.rect.width - 6, self.rect.height - 10)
        self.hitbox.midbottom = self.rect.midbottom

        self.player = True

        # Positionner le joueur
        self.bottom = 8

        self.old_position = self.position.copy()

        # Vitesse de déplacement du joueur
        self.speed_x = 2.3
        self.gravity = 0.3  # Force gravitationnelle constante
        self.speed_y = 0  # Vitesse verticale
        self.on_ground = False
        self.saut = False
        self.echelle =False
        self.monteechelle = False

        self.current_frame = 0
        self.animation_speed = 0.2  # Plus la valeur est petite, plus l'animation est rapide
        self.time_since_last_frame = 0
        self.current_direction = 0

        self.time = pygame.time.Clock().tick(60) / 1000

        self.life = 3
        self.life_max = 3

        self.collisions_ennemi = False

        self.invincible = 3
        self.attaque_ennemi = 0
        self.position_mort = []

        #propriétés des items que le joueur peut tenir
        self.items_properties = {
            "epee": {"can_attack": True, "power": 2},
            "couteau": {"can_attack": True, "power": 1},
            "key": {"can_attack": False}
        }

        self.equip_item = None
        self.hand_position = False
        self.hand_position_rect = pygame.Rect(100,100,5,5)
        #init des variables pour l'attaque
        self.arme_image = pygame.image.load(f"../sprites/objets/epee.png")
        self.rect_arme = self.arme_image.get_rect()
        self.centre_rotation_arme = pygame.Vector2(8,27)

        self.attaque_image = pygame.image.load(f"../sprites/objets/arme_attaque.png")
        self.rect_arme_attaque = self.attaque_image.get_rect()

        self.attaque = False
        self.time_since_last_attack = 2

        self.puissance_attaque = 1
        self.affichage_attaque = False

        self.rect_attaque = pygame.Rect(100,100,20,20)

        self.action = False

        self.degats = False

        self.can_attack = True

    def get_sprite(self, x, y, spritesheet_ref=None):
        """Découpe et renvoie un sprite à partir des coordonnées de la spritesheet."""
        spritesheet = spritesheet_ref if spritesheet_ref else self.spritesheet
        sprite = spritesheet.subsurface(pygame.Rect(x, y, self.width, self.height))

        return sprite

    def apply_gravity(self):
        # Ajouter la gravité si le joueur n'est pas au sol

        if self.monteechelle:
            self.speed_y = 0
            return

        if not self.on_ground:
            self.speed_y += self.gravity
        else:
            if not self.saut:
                self.speed_y = 0

        self.position[1] += self.speed_y

    def handle_input(self):
        #verifie les tpuches ^ressées pour faire bouger le player
        self.old_position = self.position.copy()

        dx = 0
        dy = 0
        
        keys = pygame.key.get_pressed()  # Vérifie quelles touches sont enfoncées
        if self.invincible >= 0.2 and self.life > 0 and not self.attaque:
            if keys[pygame.K_q]:
                self.current_direction = 1
                self.animation()
                dx = -self.speed_x
            elif keys[pygame.K_d]:
                self.current_direction = 0
                self.animation()
                dx = self.speed_x

            else:
                self.current_frame = 4
                if self.equip_item:
                    self.image = self.get_sprite(4*self.width, self.height*self.current_direction + 2*self.height)
                    self.hand_image = self.get_sprite(4*self.width, self.height*self.current_direction + 2*self.height, self.hands_spritesheet)

                else:
                    self.image = self.get_sprite(4*self.width, self.height*self.current_direction)


            if keys[pygame.K_SPACE] and self.on_ground:
                self.speed_y = -6  # Impulsion initiale pour le saut
                self.saut = True

#monte à l'echelle si il est devant
            if self.echelle:
                if keys[pygame.K_z]:
                    dy = -2
                    self.monteechelle = True

                elif keys[pygame.K_s]:
                    if not self.on_ground:
                        dy = 2
                        self.monteechelle = True

            if self.equip_item:
                if keys[pygame.K_LEFT] and self.time_since_last_attack >= 0.5 and self.items_properties[self.equip_item["type"]]["can_attack"]:
                    self.attaque = True
                    self.current_frame = 0
                    self.time_since_last_frame = 0

            if keys[pygame.K_RIGHT]:
                self.action = True
            else:
                self.action = False

        self.position[0] += dx
        self.position[1] += dy

    def animation(self):

#gere les animations en fonction de la direction ou de l'action (marcher, attaquer)
        if self.attaque:
            self.animation_speed = 0.115

            if self.current_frame == 2:
                self.current_frame = 0
                self.attaque=False
                self.time_since_last_attack = 0

            else:
                self.image = self.get_sprite(self.current_frame*32 + 5*self.width, self.current_direction*64 + 128)
                self.hand_image = self.get_sprite(self.current_frame*32 + 5*self.width, self.current_direction*64 + 128, self.hands_spritesheet)
            if self.current_frame == 1:
                self.degats = True
            else:
                self.degats = False
        else:

            self.animation_speed = 0.2

            if self.current_frame >= 4:
                self.current_frame = 0

            if not self.equip_item:
                self.image = self.get_sprite(self.current_frame*32, self.current_direction*64)
                self.hand_image = self.get_sprite(self.current_frame*32, self.current_direction*64, self.hands_spritesheet)

            else:
                self.image = self.get_sprite(self.current_frame*32, self.current_direction*64 + 128)
                self.hand_image = self.get_sprite(self.current_frame*32, self.current_direction*64 + 128, self.hands_spritesheet)

        self.time_since_last_frame += self.time
        if self.time_since_last_frame >= self.animation_speed:
            self.current_frame +=1
            self.time_since_last_frame = 0

    def get_hand_position(self):

#donne la position de la main du joueur en fonction de son rect en temps reel
        if self.attaque:
            if self.current_direction == 0:
                if self.current_frame == 0:
                    self.hand_position =[19,52]
                else:
                    self.hand_position = [20,17]
            else:
                if self.current_frame == 0:
                    self.hand_position = [8, 52]
                else:
                    self.hand_position = [7, 17]

        else:

            if self.current_direction == 0:
                if self.current_frame ==0:
                    self.hand_position = [7,14]
                elif self.current_frame == 1 or self.current_frame == 3:
                    self.hand_position = [9,15]
                elif self.current_frame == 2:
                    self.hand_position = [11, 15]
                else:
                    self.hand_position = [7,14]
            else:
                if self.current_frame ==0:
                    self.hand_position = [20,14]
                elif self.current_frame == 1 or self.current_frame == 3:
                    self.hand_position = [17,15]
                elif self.current_frame == 2:
                    self.hand_position = [16,15]
                else:
                    self.hand_position = [18,14]

        self.hand_position_rect = pygame.Rect(self.rect.left + self.hand_position[0], self.rect.bottom - self.hand_position[1], 5,5)
        if self.equip_item:
            self.positionner_arme()

    def positionner_arme(self):

#positionne l'arme en fonction de la main du joueur
        if self.attaque:
            if self.current_frame == 0:
                angle = -35
            else:
                angle = -125

        else:
            if self.current_frame == 0 or self.current_frame == 4:
                angle = -90  # ou dynamique
            elif self.current_frame == 1 or self.current_frame == 3:
                angle = -75
            elif self.current_frame == 2:
                angle = -60


        # Rotation de l'image
        rotated_image = pygame.transform.rotate(self.arme_image, angle)
        if self.equip_item["type"] == "epee":
            self.attaque_image = pygame.transform.scale(self.attaque_image, (self.attaque_image.get_width() * 1.5, self.attaque_image.get_height()))
        self.rect_arme_attaque = self.attaque_image.get_rect()

        #retourne l'arme si le joueur est dans le sens opposé
        if self.current_direction == 1:
            self.arme_image = pygame.transform.flip(rotated_image, True, False)
            self.attaque_image = pygame.transform.flip(self.attaque_image, True, False)
        else:
            self.arme_image= rotated_image
        self.centre_rotation_arme.x = self.arme_image.get_width() - self.centre_rotation_arme.x  # miroir horizontal

        self.rect_arme = self.arme_image.get_rect()
        self.rect_arme_attaque = self.attaque_image.get_rect()

#defini le rect de l'arme et de l'animation de l'attaque
        if self.current_direction == 0:
            if angle > -90:
                self.rect_arme.bottomleft = self.hand_position_rect.bottomleft
                self.rect_arme.bottom += 5
            else:
                self.rect_arme.topleft = self.hand_position_rect.topleft
                self.rect_arme.bottom -=5
            self.rect_arme.left -= 3

            self.rect_arme_attaque.bottomleft = self.rect_arme.center
            self.rect_arme_attaque.y += 15

        else:
            if angle > -90:
                self.rect_arme.bottomright = self.hand_position_rect.bottomright
                self.rect_arme.bottom += 5
            else:
                self.rect_arme.topright = self.hand_position_rect.topright
                self.rect_arme.bottom -=5
            self.rect_arme.left += 3

            self.rect_arme_attaque.bottomright = self.rect_arme.center
            self.rect_arme_attaque.y += 15

        self.rect_attaque =self.rect_arme_attaque

    def update(self):
        # Gère les mises à jour du joueur chaque frame

        # Si une attaque est en cours, lancer l'animation
        if self.attaque:
            self.animation()
            # Affiche l'image d'attaque uniquement au frame 1
            if self.current_frame == 1:
                self.affichage_attaque = True
            else:
                self.affichage_attaque = False

        # Applique la gravitation au joueur
        self.apply_gravity()

        # Mise à jour du timer depuis la dernière attaque
        self.time_since_last_attack += self.time

        # Met à jour la position de l'image avec la position calculée
        self.rect.bottomleft = self.position
        self.hitbox.midbottom = self.rect.midbottom

        # Empêche d'avoir plus de vie que le maximum
        if self.life > self.life_max:
            self.life = self.life_max

        # Si le joueur est touché récemment, applique un recul
        if self.invincible <= 0.2 and self.life > 0:
            self.position[0] += self.attaque_ennemi * 2

        # Si le joueur est invincible, on le rend transparent (effet de clignotement)
        if self.invincible <= 3 and self.life > 0:
            self.image.set_alpha(155)

        # Si le joueur est mort
        if self.life <= 0:
            # Petite animation de chute avant immobilisation
            if self.invincible > 1.5:
                self.position[1] += 2
            else:
                self.speed_y = 0

        # Mise à jour du timer d'invincibilité
        self.invincible += self.time

        # Si la vitesse y est positive, le saut est terminé
        if self.speed_y >= 0:
            self.saut = False

        # Vérifie si on est encore sur l'échelle
        if self.monteechelle:
            if self.on_ground or not self.echelle:
                self.monteechelle = False

        # Si un objet est équipé, charger les sprites correspondants
        if self.equip_item:
            self.arme_image = pygame.image.load(f"../sprites/objets/{self.equip_item["type"]}.png")
            self.attaque_image = pygame.image.load(f"../sprites/objets/arme_attaque.png")
            self.rect_arme_attaque = self.attaque_image.get_rect()
            # Mettre à jour la puissance si l'objet peut attaquer
            if self.items_properties[self.equip_item["type"]]["can_attack"]:
                self.puissance_attaque = self.items_properties[self.equip_item["type"]]["power"]

    def move_back_y(self):
        self.position[1] = self.old_position[1]  # Restaurer seulement la position y
        self.hitbox.bottomleft = (self.hitbox.left, self.position[1])  # Garder X inchangé


# Classe représentant une maison à gauche du décor
class House_left(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.name = "house_left"
        self.entity = False
        self.position = [0, 10 * 64]  # Position de la maison dans le monde
        self.spritesheet = pygame.image.load("../maps/tiles/images/maison.png").convert_alpha()
        self.image = self.get_sprite(0, 192, 64 * 3, 64 * 3)  # Sprite par défaut (3 tuiles de large et haut)
        self.rect = self.image.get_rect()
        self.hitbox = self.rect
        self.nature = "object"

    def get_sprite(self, x, y, width, height):
        # Récupère une portion de la spritesheet correspondant au sprite de la maison
        return self.spritesheet.subsurface(pygame.Rect(x, y, width, height))

    def update(self):
        # Met à jour la position de l'image de la maison
        self.rect.topleft = self.position


# Classe pour la maison de droite (affiche différente selon le début du jeu)
class House_right(pygame.sprite.Sprite):
    def __init__(self, *groups):
        super().__init__(*groups)
        self.name = "house_right"
        self.debut_jeu = True  # Utilisé pour afficher une image spécifique en début de partie
        self.entity = False
        self.position = [64 * 3, 10 * 64]  # Position initiale
        self.spritesheet = pygame.image.load("../maps/tiles/images/maison.png").convert_alpha()
        self.image = self.get_sprite(64 * 3, 0, 64, 64 * 3)  # Image de départ
        self.rect = self.image.get_rect()
        self.hitbox = self.rect
        self.nature = "object"

    def get_sprite(self, x, y, width, height):
        # Extrait une partie de la spritesheet (64x192 ou autre)
        return self.spritesheet.subsurface(pygame.Rect(x, y, width, height))

    def update(self):
        # Met à jour la position de la maison
        self.rect.topleft = self.position
        # Affiche une image différente si le début du jeu est terminé
        if self.debut_jeu:
            self.image = self.get_sprite(64 * 3, 0, 64, 64 * 3)
        else:
            self.image = self.get_sprite(64 * 3, 192, 64, 64 * 3)


class Gluglu(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.name = "gluglu"
        self.width = 32
        self.height = 32

        self.spritesheet = pygame.image.load("../sprites/persos/gluglu (1).png").convert_alpha()
        self.image = self.get_sprite(0, 0)

        self.attaque = False
        self.phase_attaque = 0

        self.entity = True
        self.ennemi = True

        self.player = False

        self.position_depart =[x, y]
        self.position =[x, y]
        self.speed_y = 0
        self.speed_x = -1
        self.gravity = 0.3

        self.rect = self.image.get_rect()

        self.hitbox = pygame.Rect(self.rect.left + 1, self.rect.top + 4, self.rect.width - 2, self.rect.height - 8)

        self.rect.bottomleft = self.position
        self.bottom = 1

        self.old_position = self.position.copy()

        self.capteur = False

        self.on_ground = False
        self.saut = False

        self.current_frame = 0
        self.animation_speed = 0.2  # Plus la valeur est petite, plus l'animation est rapide
        self.time_since_last_frame = 0
        self.current_direction = 0

        self.time = pygame.time.Clock().tick(60) / 1000

        self.player_position = [0, 0]

        self.dt = 0
        self.time_since_last_attack = 3
        self.puissance_attaque = 1

        self.touch_wall = False

        self.attacked = False

        self.life = 3

        self.death = False

        self.recul = 0
        self.alpha_state = 255

        self.rect_attaque = self.hitbox
        self.can_attack = True
        self.degats = False

    def get_sprite(self, x, y):

        sprite = self.spritesheet.subsurface(pygame.Rect(x, y, self.width, self.height))

        return sprite

    def animation(self):
        #anime en fonction de si il marche ou si il meurt
        if self.life>0:
            self.image = self.get_sprite(self.current_frame*self.width, self.current_direction*self.height)
            self.time_since_last_frame += time
            if self.time_since_last_frame >= self.animation_speed:
                self.current_frame += 1
                self.time_since_last_frame = 0
                if self.current_frame == 1:
                    self.hitbox.height += 2

            if self.current_frame == 2:
                self.current_frame = 0
                self.hitbox.height -= 2
        else:
            self.animation_speed = 0.25
            self.image = self.get_sprite(self.current_frame * self.width, 2 * self.height)
            self.time_since_last_frame += time
            if self.time_since_last_frame >= self.animation_speed:
                self.current_frame += 1
                self.time_since_last_frame = 0

            if self.current_frame == 3:
                self.death = True
                self.current_frame = 2


    def apply_gravity(self):
        #ajoute gravité si il est pas au sol

        if not self.on_ground:
            self.speed_y += self.gravity
        else:
            if not self.saut:
                self.speed_y = 0

        self.position[1] += self.speed_y

    def attaquer(self):
        #attaque en trois phaseset modifie egalement l'image en fonction de la phase

        if self.phase_attaque ==0:
            self.image = self.get_sprite(2 * self.width, self.current_direction * self.height)
            if self.speed_x == -1 or self.speed_x == 1:
                self.speed_x *= -2

            self.time_since_last_frame += self.time
            self.dt += self.time

            if self.time_since_last_frame >= 0.05:
                self.speed_x *= -1
                self.time_since_last_frame = 0

            if self.dt >= 1.5:
                self.dt = 0
                self.phase_attaque = 1

        if self.phase_attaque == 1:
            self.image = self.get_sprite(self.width, self.current_direction * self.height)
            if self.on_ground:
                self.speed_y = -5
                self.saut = True
            else:
                self.phase_attaque = 2

            if self.current_direction == 0:
                self.speed_x = -3
            else:
                self.speed_x = 3

        if self.phase_attaque == 2:
            #active les degats si la phase est 2
            self.degats = True
            if self.on_ground:
                #fini l'attaque si il touche le sol
                self.attaque = False
                self.degats =False
                self.phase_attaque = 0
                self.time_since_last_attack = 0
                self.position_depart = self.position.copy()

        self.position[0] +=self.speed_x

    def subit_attaque(self, puissance, player_direction):

        #fais perdre de la vie et le fait reculer quand il recoit une attaque, change certaine variable pour eviter les bugs
        self.life -= puissance
        self.recul = 0.4  # durée du recul (en secondes)
        self.recul_direction = 1 if player_direction == 0 else -1
        self.attacked = True
        self.attaque = False
        self.phase_attaque = 0
        self.dt = 0
        self.time_since_last_attack = 1

    def update(self):

        self.rect_attaque = self.hitbox

        if self.life > 0:
            # definit la position
            self.old_position = self.position.copy()
            self.rect.bottomleft = self.position
            self.hitbox.midbottom = self.rect.midbottom

            #lance l'attaque sous condition sinon appelle fonction mouvement
            if self.attaque and self.time_since_last_attack > 3:
                self.attaquer()
            else:
                self.mouvements()
                self.time_since_last_attack += self.time

            self.apply_gravity()

            if self.speed_y >= 0:
                self.saut = False

            #active le capteur si le joueur est plus ou moins proche
            if -180 < self.position[0] - self.player_position[0] < 180:
                self.capteur = True
            elif self.capteur:
                self.capteur = False
                #redefinit position depart pour ses mouvements quand il ne voit pas le joueur
                self.position_depart = self.position.copy()

            if self.recul > 0:
                self.recul -= time
                self.position[0] += self.recul_direction * 2  # Reculer horizontalement
                self.image.set_alpha(self.alpha_state)
                self.alpha_state = 255 if self.alpha_state == 0 else 0  # Clignoter
            else:
                self.image.set_alpha(255)

            if self.attacked and self.recul <= 0:
                self.attacked = False

        else:
            self.animation()

    def mouvements(self):

#gere les mouvements en fonction de si il capte ou pas le joueur
        if not self.capteur:

            if self.touch_wall == "left" and self.current_direction == 0:
                self.touch_wall = False
                self.position_depart = [self.position[0] + 15, self.position[1]]
            elif self.touch_wall == "right" and self.current_direction == 1:
                self.touch_wall = False
                self.position_depart = [self.position[0] - 15, self.position[1]]

            if self.current_direction == 0 and self.position[0] <= self.position_depart[0] - 15:
                self.speed_x = 1
                self.current_direction = 1

            elif self.current_direction == 1 and self.position[0] >= self.position_depart[0] + 15:

                self.speed_x = -1
                self.current_direction = 0

        else:
            if self.position[0] < self.player_position[0]:
                self.speed_x = 1
                self.current_direction = 1

                if self.position[0] > self.player_position[0] - 100:
                    self.attaque = True
                else:
                    self.attaque = False


            elif self.position[0] > self.player_position[0]:
                self.speed_x = -1
                self.current_direction = 0

                if self.position[0] < self.player_position[0] + 100:
                    self.attaque = True
                else:
                    self.attaque = False

        self.animation()
        self.position[0] += self.speed_x

    def move_back_y(self):
        self.position[1] = self.old_position[1]  # Restaurer seulement la position y
        self.rect.bottomleft = (self.rect.left, self.position[1])  # Garder X inchangé

class Heart(pygame.sprite.Sprite):

    def __init__(self, x, y, *groups, indice=-1, drop=False):
        super().__init__(*groups)
        self.name = "heart"
        self.width = 16
        self.height = 16

        self.spritesheet = pygame.image.load("../sprites/objets/heart.png").convert_alpha()
        self.image = self.get_sprite(0, 0)

        self.indice = indice
        self.life_player = 3

        self.rect = self.image.get_rect()
        self.position = [x,y]
        self.rect.topleft = self.position

        self.drop = drop
        self.blink_time = 0.3
        self.visible = True

        self.timer = 0

    def get_sprite(self, x, y):
        sprite = self.spritesheet.subsurface(pygame.Rect(x, y, self.width, self.height))
        return sprite

    def update(self):
        #gere update si c'est un coeur drop ou un coeur qui affiche la vie
        if self.drop:
            self.timer += time
            #timer qui fais clignoter le sprite avant qu'il disparaisse
            if self.timer > 5:
                self.blink_time-=time
                if self.blink_time <=0:
                    self.visible = not self.visible
                    self.blink_time = 0.3
            if self.timer >= 10:
                self.kill()
            if not self.visible:
                self.image.set_alpha(0)
            else:
                self.image.set_alpha(255)

        else:
            if self.indice <= self.life_player:
                self.image = self.get_sprite(0,0)
            else:
                self.image = self.get_sprite(self.width, 0)

            self.image = pygame.transform.scale(self.image, (32, 32))

class Chest(pygame.sprite.Sprite):
    def __init__(self, x, y, contenu, super_chest=False, *groups):
        super().__init__(*groups)
        self.name = "chest"
        self.width = 64
        self.height = 64
        self.name = "coffre special" if super_chest else "coffre simple"
        self.spritesheet = pygame.image.load(f"../sprites/objets/{self.name}.png")
        self.image = self.get_sprite(0,0)
        self.position = [x,y]
        self.rect = self.image.get_rect()
        self.rect.topleft = self.position
        self.hitbox = self.rect
        self.open = False
        self.contenu = contenu
        self.closed = True if super_chest else False  #fermé à clé si coffre special
        self.entity = False

    def get_sprite(self, x, y):
        sprite = self.spritesheet.subsurface(pygame.Rect(x, y, self.width, self.height))
        return sprite

    def update(self):
        #afiche le coffre ouvert ou non
        if self.open:
            self.image = self.get_sprite(self.width,0)

        self.rect.topleft = self.position

class Eye(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.name = "eye"
        self.width = 32
        self.height = 32
        self.spritesheet = pygame.image.load("../sprites/persos/oeil (1).png")
        self.image = self.get_sprite(0,0)
        self.rect = self.image.get_rect()
        self.position = [x, y]
        self.rect.topleft = self.position
        self.hitbox = self.rect
        self.current_direction = 0
        self.current_frame = 0
        self.time_since_last_frame = 0
        self.animation_speed = 0.2
        self.capteur = False

        self.entity = True
        self.ennemi = True

        self.death = False

        self.attaque = False
        self.time_since_last_attack = 1
        self.attacked = False
        self.life = 1

        self.death = False

        self.player_position = [0,0]

        self.phase_attaque = 1

        self.angle = 0

        self.projectile = False
        self.attaque_image = pygame.image.load("../sprites/objets/laser.png")
        self.laser = False
        self.direction_laser = pygame.Vector2()
        self.position_laser = pygame.Vector2()
        self.speed_laser = 5
        self.rect_attaque = self.attaque_image.get_rect()

        self.can_attack = True

        self.affichage_attaque = False
        self.degats = False
        self.puissance_attaque = 2

    def get_sprite(self, x, y):
        sprite = self.spritesheet.subsurface(pygame.Rect(x, y, self.width, self.height))
        return sprite

    def animation(self):
        #anime l'oeil en fonction de si il voit le personnage et qu'il est en train d'attaquer ou si il ne le voit pas et cligne des yeux
        if self.life > 0:
            if self.capteur:
                if self.attaque:
                    self.animation_speed = 0.2 / self.phase_attaque if self.phase_attaque != 4 or self.current_frame != 4 else 1.5
                    self.time_since_last_frame += time
                    if self.time_since_last_frame >= self.animation_speed:
                        self.current_frame += 1
                        self.time_since_last_frame = 0
                    if self.current_frame == 5:
                        self.current_frame = 0
                        self.phase_attaque += 1
                    if self.phase_attaque == 5:
                        self.phase_attaque = 1
                        self.attaque = False
                        self.time_since_last_attack = 0
                        self.attaquer()
                else:
                    self.current_frame = 0
                original_image = self.get_sprite(self.width * self.current_frame, self.height)
                rotated_image = pygame.transform.rotate(original_image, -self.angle)

                # Centre l’image rotatée à l’ancienne position du centre
                old_center = self.rect.center
                self.image = rotated_image
                self.rect = self.image.get_rect()
                self.rect.center = old_center

            else:
                self.animation_speed = 0.15 if self.current_frame != 0 else 3.5
                self.image = self.get_sprite(self.current_frame*self.width,0)
                self.rect = self.image.get_rect()
                self.rect.topleft=self.position

                self.time_since_last_frame += time
                if self.time_since_last_frame >= self.animation_speed:
                    self.time_since_last_frame = 0
                    self.current_frame += 1

                if self.current_frame == 4:
                    self.current_frame = 0
        else:
            #animation de mort
            self.animation_speed = 0.3 if self.current_frame != 0 else 1.5
            self.image = self.get_sprite(self.current_frame*self.width, 2*self.height)
            self.time_since_last_frame +=time
            self.rect = self.image.get_rect()
            self.rect.topleft = self.position

            if self.time_since_last_frame >= self.animation_speed:
                self.current_frame += 1
                self.time_since_last_frame = 0
            if self.current_frame == 7:
                self.death = True

    def subit_attaque(self, puissance, player_direction):
        #enleve seulement de la vie
        self.attacked = True
        self.life -= puissance
        self.current_frame = 0
        self.time_since_last_frame = 0

    def attaquer(self):

        #crée le laser si il ne l'a pas encore lancé sinon il avance le laser
        if not self.laser:
            #oriente le laser
            self.attaque_image = pygame.image.load("../sprites/objets/laser.png")
            self.attaque_image = pygame.transform.rotate(self.attaque_image, -self.angle)
            self.rect_attaque = self.attaque_image.get_rect()
            self.position_laser = self.hitbox.center
            radians = math.radians(self.angle)
            self.direction_laser = pygame.Vector2(math.cos(radians), math.sin(radians))
            self.laser = True
        else:
            self.position_laser += self.direction_laser * self.speed_laser
            self.rect_attaque.center = self.position_laser

    def update(self):

        if self.life > 0:

#definit quand il voit ou non le joueur en fonction de x et y
            if (
                    330 > self.player_position[0] - self.hitbox.centerx > -330
                and 180 > self.player_position[1] - self.hitbox.centery > -180
            ):
                if not self.capteur:
                    self.capteur = True
                    self.current_frame = 0
                    self.time_since_last_frame = 0

            elif self.capteur:
                self.capteur = False
                self.current_frame = 0
                self.time_since_last_frame = 0
                self.phase_attaque = 1
                self.time_since_last_attack = 0
                self.attaque = False

            if self.capteur:
#calcule l'angle avec le joueur
                cot_opp = self.player_position[1] - self.hitbox.centery
                cot_adj = self.player_position[0] - self.hitbox.centerx
                self.angle = math.degrees(math.atan2(cot_opp, cot_adj))  # Angle en degrés

                self.time_since_last_attack += time

                if self.time_since_last_attack >= 1.5:
                    self.attaque = True

        self.animation()
        if self.laser:
            #appelle le fonction attaquer si il y a un laser, supprime le laser si l'oeil se remet à attaquer
            self.attaquer()
            self.affichage_attaque = True
            self.degats = True
            if self.attaque:
                self.laser = False
        else:
            self.affichage_attaque = False
            self.degats = False

class Red_key(pygame.sprite.Sprite):
    def __init__(self, x, y, serrure_pos,  *groups):
        super().__init__(*groups)
        self.name = "red_key"
        self.width = 16
        self.height = 32
        self.spritesheet = pygame.image.load("../sprites/objets/red_key.png")
        self.image = self.get_sprite(0,0)
        self.statut = "course"

        self.position = [x,y]

        self.rect = self.image.get_rect()
        self.rect.topleft = self.position
        self.hitbox = self.rect

        self.saut = False

        self.entity = True
        self.ennemi = False

        self.current_frame = 0
        self.animation_speed = 0.2  # Plus la valeur est petite, plus l'animation est rapide
        self.time_since_last_frame = 0
        self.current_direction = 0

        self.time_asleep = 3

        self.speed_x = 3
        self.speed_y = 0

        self.capteur = False

        self.player_position = [0,0]

        self.attacked = False
        self.attaque = False

        self.on_ground = False

        self.can_attack = False

        self.aller_ouvrir_porte = False
        self.serrure_position = serrure_pos

        self.old_position = self.position.copy()

    def get_sprite(self, x, y):
        sprite = self.spritesheet.subsurface(pygame.Rect(x, y, self.width, self.height))
        return sprite

    def animation(self):

#anime en fonction de son statut (si il est par terre ou si il court
        if self.statut == "par terre":
            self.image = self.get_sprite(3 * self.width, 0)
            self.image = pygame.transform.rotate(self.image, 90)
        elif self.capteur or self.speed_x != 0:
            self.image = self.get_sprite(self.current_frame * self.width, 0)
            self.time_since_last_frame += time
            if self.time_since_last_frame >= self.animation_speed:
                self.current_frame += 1
                self.time_since_last_frame = 0

            if self.current_frame == 4:
                self.current_frame = 0
        elif not self.capteur:
            self.image = self.get_sprite(3*self.width,0)

        if self.current_direction == 0:
            self.image = pygame.transform.flip(self.image,True, False)

    def mouvements(self):

#defnit ses actions en fonction de son statut
        if self.aller_ouvrir_porte:
            #va vers la serrure de la porte pour l'ouvrir
            if -2 <= self.position[0] - self.serrure_position[0] <= 2:
                self.speed_x = 0
                self.speed_y = -2
                if self.position[1] <= self.serrure_position[1]:
                    self.statut = "ouvert"
            elif self.position[0] < self.serrure_position[0]:
                self.speed_x = 2.3
                self.current_direction = 0
            elif self.position[0] > self.serrure_position[0]:
                self.speed_x = -2.3
                self.current_direction = 1

        elif self.statut == "course":
            #fuit le joueur quand il est proche

            if (self.position[0] - self.player_position[0] < 180 and self.position[0] - self.player_position[0] > -180):
                self.capteur = True
            if (self.position[0] - self.player_position[0] > 300 or self.position[0] - self.player_position[0] < -300):
                self.capteur = False

            if not self.capteur:
                self.speed_x = 0
            else:
                if self.position[0] < self.player_position[0]:
                    self.speed_x = -3
                    self.current_direction = 1

                elif self.position[0] > self.player_position[0]:
                    self.speed_x = 3
                    self.current_direction = 0

        elif self.statut == "suivre":
            #suit le joueur si il s'eloigne
            if -30 < self.position[0] - self.player_position[0] < 30:
                self.capteur = False
            if abs(self.position[0] - self.player_position[0]) > 100:
                self.capteur = True
            if abs(self.position[0] - self.player_position[0]) > 250 or abs(self.position[1] - self.player_position[1]) > 100:
                self.position[0] = self.player_position[0]
                self.position[1] = self.player_position[1]

            if self.capteur:
                if self.position[0] < self.player_position[0]:
                    self.speed_x = 2.3
                    self.current_direction = 0

                elif self.position[0] > self.player_position[0]:
                    self.speed_x = -2.3
                    self.current_direction = 1
            else:
                self.speed_x = 0

        else:
            #reste par terre pendant un laps de temps
            self.speed_x = 0
            self.time_asleep -= time
            if self.time_asleep <= 0:
                self.statut = "suivre"

        self.position[0] += self.speed_x
        self.position[1] += self.speed_y

    def subit_attaque(self, puissance, player_direction):
        #definit seulement son stautut à par terre

        self.statut = "par terre"

    def apply_gravity(self):

        if not self.on_ground:
            self.speed_y += 0.3
        else:
            if not self.saut:
                self.speed_y = 0

        self.position[1] += self.speed_y

    def update(self):
#appelle les fonctions et definit sa position
        self.old_position = self.position.copy()

        self.rect = self.image.get_rect()

        self.rect.topleft = self.position
        self.hitbox = self.rect

        self.mouvements()
        self.animation()
        self.apply_gravity()

    def move_back_y(self):
        self.position[1] = self.old_position[1]  # Restaurer seulement la position y
        self.hitbox.bottomleft = (self.hitbox.left, self.position[1])  # Garder X inchangé

class End_door(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups)
        self.name = "end_door"
        self.spritesheet = pygame.image.load("../sprites/objets/porte_fin.png")
        self.width = 32
        self.height = 64
        self.image = self.get_sprite(0,0)
        self.position = pygame.Vector2(x,y)
        self.statut = "closed"
        self.entity = False

        self.rect = self.image.get_rect()
        self.rect.topleft = self.position

        self.hitbox = self.rect

    def get_sprite(self, x, y):
        sprite = self.spritesheet.subsurface(pygame.Rect(x, y, self.width, self.height))
        return sprite

    def update(self):
        #definit son image si elle est ouverte ou non
        if self.statut == "closed":
            self.image = self.get_sprite(0,0)
        else:
            self.image = self.get_sprite(self.width, 0)

        self.image = pygame.transform.scale(self.image,(64,128))
        self.rect=self.image.get_rect()
        self.rect.topleft = self.position

