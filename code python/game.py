import sys
import random
import pygame
import pytmx

from sprite import Player, House_left, House_right, Gluglu, Heart, Chest, Red_key, Eye, End_door

#code pour la camera
class Camera:
    def __init__(self, width, height):
        self.offset = pygame.Vector2(0, 0)
        self.width = width  # Camera viewport width (e.g., SCREEN_WIDTH)
        self.height = height # Camera viewport height (e.g., SCREEN_HEIGHT)

    def apply(self, rect):
        #permet d'appliquer un décalage à un rect pour jouer entre les coordonnées de la fenêtre et celles de la map
        return rect.move(-self.offset.x, -self.offset.y)

    def apply_point(self, point):
        #pareil pour un point
        return (point[0] - self.offset.x, point[1] - self.offset.y)

    def center_on(self, target_rect, map_width, map_height):
        #centre la caméra sur un rect pour le suivre
        #calcule l'offset pour centrer le rect
        self.offset.x = target_rect.centerx - self.width // 2
        self.offset.y = target_rect.centery - self.height // 2

        # empeche la camera de sortir de la carte
        self.offset.x = max(0, min(self.offset.x, map_width - self.width))
        self.offset.y = max(0, min(self.offset.y, map_height - self.height))

class Game:
    def __init__(self):
        #dimensions de l'ecran
        self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 800, 600

        #creation de la fenetre
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Zelda bros")

        self.game = True

        # Couleurs
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.BLUE = (50, 100, 255)
        self.GREEN = (100, 255, 100)
        self.RED = (255, 0, 0)

        # Variables ecran demarrage
        self.font = pygame.font.Font(None, 74)
        self.title_text = self.font.render("Instructions :", True, self.WHITE)
        self.instruction_text = [
            self.font.render("Q : droite", True, self.WHITE),
            self.font.render("D : gauche", True, self.WHITE),
            self.font.render("Z : monter l'echelle", True, self.WHITE),
            self.font.render("S : descendre l'echelle", True, self.WHITE),
            self.font.render("ESPACE : sauter", True, self.WHITE)
        ]

        # ------------------------------------------------------------

        # Charger la carte
        try:
            self.tmx_data = pytmx.util_pygame.load_pygame("../maps/level1(test).tmx")
        except FileNotFoundError:
            print("Error: TMX map file not found.")
            pygame.quit()
            sys.exit()

        #reprend les dimensions de la carte
        self.tile_width = self.tmx_data.tilewidth
        self.tile_height = self.tmx_data.tileheight
        self.map_width_pixels = self.tmx_data.width * self.tile_width
        self.map_height_pixels = self.tmx_data.height * self.tile_height

        #creation camera
        self.camera = Camera(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)

        #creation groupe contenant tous les sprites et pouvant gérer les calques
        self.all_sprites = pygame.sprite.LayeredUpdates()

        # Generer joueur
        player_position = [45, 815]

        self.player = Player(player_position[0], player_position[1])
        self.all_sprites.add(self.player, layer=2)

        #listes de sprites
        self.gluglu = []
        self.chest = []
        self.end_door = None
        self.red_key = None

        #parcours les objets pour les identifier
        for obj in self.tmx_data.objects:
            if obj.type == 'gluglu':
                gluglu = Gluglu(obj.x, obj.y)
                self.gluglu.append(gluglu)
                self.all_sprites.add(gluglu, layer = 2)

            if obj.type == "coffre simple":
                chest = Chest(obj.x, obj.y, "key")
                self.chest.append(chest)
                self.all_sprites.add(chest, layer=1)

            if obj.type == "coffre special":
                chest = Chest(obj.x, obj.y, obj.name, super_chest=True)
                self.chest.append(chest)
                self.all_sprites.add(chest, layer=1)

            if obj.type == "porte fin":
                self.end_door = End_door(obj.x, obj.y)
                self.all_sprites.add(self.end_door, layer=1)

            if obj.type == "eye":
                self.all_sprites.add(Eye(obj.x, obj.y), layer = 2)

        self.house_left = House_left()
        self.all_sprites.add(self.house_left, layer=3)
        self.house_right = House_right()
        self.all_sprites.add(self.house_right, layer = 1)

        #listes d'objets
        self.collisions = []
        self.door = None
        self.echelle = []

        #parcours les objets
        for obj in self.tmx_data.objects:
            if obj.type == 'collisions':
                self.collisions.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

            if obj.name == "door":
                self.door = pygame.Rect(obj.x, obj.y, obj.width, obj.height)

            if obj.type == 'echelle':
                print("echelle ajoutée")
                self.echelle.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))

        # centrer la camera sur le joueur
        self.camera.center_on(self.player.rect, self.map_width_pixels, self.map_height_pixels)

        #autres groupes de sprites
        self.heart = pygame.sprite.Group()
        self.heart_drop = pygame.sprite.Group()

        for i in range(3):
            self.heart.add(Heart(5 + i *35, 5, indice=i+1))

        #initier variables utiles pour le jeu
        self.recommencer = False

        self.paused = False
        self.current_menu_index = 0
        self.menu_selection_index = 0

        self.inventory = []

        self.items = {"Cœurs : " : str(self.player.life), "Objets : " : self.inventory}
        self.parametres = {"Afficher les rects : " : False}

        self.equip_item = False
        self.actual_item = False

        #permettra de verifier si les touches sont encore pressées pour eviter de repeter plusieurs fois une meme action
        self.keys_states = {pygame.K_RIGHT : False, pygame.K_d : False, pygame.K_q : False, pygame.K_TAB : False}

        self.menus = ["inventaire", "parametres"]
        self.navigation_menus = {"parametres" : self.parametres, "items" : self.items}

        self.level_clear = False

    def fade_transition(self, start_surface, end_surface, duration, screen):
        #permet de faire une transition entre l'ecran de demarrage et l'ecran du jeu
        clock = pygame.time.Clock()
        fade_overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        fade_overlay.fill(self.BLACK)
        alpha = 255

        for step in range(duration):
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            #permet de ne pas avoir un alpha en dessous de 0
            alpha = max(0, 255 - (step * (255 // duration)))
            fade_overlay.set_alpha(alpha)

            screen.blit(start_surface, (0, 0))
            #dessine l'ecran final avec l'overlay au dessus
            if alpha < 255:
                screen.blit(end_surface, (0, 0))
            screen.blit(fade_overlay, (0, 0))

            pygame.display.flip()
            clock.tick(60)

    def create_start_screen(self):
        #crée l'ecran de demarrage
        start_surface = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        start_surface.fill(self.BLACK)
        start_surface.blit(self.title_text, (self.SCREEN_WIDTH // 2 - self.title_text.get_width() // 2, self.SCREEN_HEIGHT // 5))
        n = 0
        for text in self.instruction_text:
            start_surface.blit(text,(self.SCREEN_WIDTH // 2 - text.get_width() // 2, self.SCREEN_HEIGHT // 3 + n))
            n += 75

        return start_surface

    def render_game_to_surface_for_transition(self, surface):
        surface.fill(self.BLACK)

        for layer in self.tmx_data.visible_layers:
    #on recupere les coordonnees de chaque tuiles et on les dessine sur l'ecran en fonction de la position de la camera
    #permet d'afficher la toute premiere frame du jeu pendant la transition
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        world_x = x * self.tile_width
                        world_y = y * self.tile_height
                        tile_rect = pygame.Rect(world_x, world_y, self.tile_width, self.tile_height)
                        surface.blit(tile, self.camera.apply(tile_rect))

        for sprite in self.all_sprites.sprites():
            surface.blit(sprite.image, self.camera.apply(sprite.rect))

    def update(self):

#appelle la fonction update des sprites
        self.all_sprites.update()

        self.heart.update()
        self.heart_drop.update()

#centre la camera
        self.camera.center_on(self.player.rect, self.map_width_pixels, self.map_height_pixels)

#detecte les collisions pour detecter les attaques
        for sprite in self.all_sprites.sprites():

            if sprite.entity and sprite != self.player:
                #echange de données
                sprite.player_position = self.player.hitbox.center
                if sprite.ennemi:
                    if self.player.hitbox.colliderect(sprite.rect_attaque):
                        if sprite.degats and self.player.invincible > 3:
                            #defini l'attaque subit en fonction du rect de l'attaque, definit le recul du player
                            if sprite.rect_attaque == sprite.hitbox:
                                self.player.life -= sprite.puissance_attaque
                                self.player.invincible = 0
                                self.player.attaque_ennemi = sprite.puissance_attaque * 2 if sprite.speed_x >= 0 else -sprite.puissance_attaque * 2
                            else:
                                self.player.life -= sprite.puissance_attaque
                                self.player.invincible = 0
                                self.player.attaque_ennemi = sprite.puissance_attaque if sprite.direction_laser.x >0 else -sprite.puissance_attaque

                if self.player.degats:
                    #appelle la fonction subit attaque du sprite qui se fait attaquer
                        if self.player.rect_attaque.colliderect(sprite.rect):
                            if not sprite.attacked:
                                sprite.subit_attaque(self.player.puissance_attaque, self.player.current_direction)

        for heart in self.heart:
            heart.life_player = self.player.life

        for heart in self.heart_drop:
            #augmente la vie du joueur si il touche un coeur
            if self.player.hitbox.colliderect(heart.rect):
                self.player.life += 1
                heart.kill()

        for sprite in self.all_sprites.sprites():
            if sprite.entity:
                #vitesse maximale quand on tombe
                if sprite.name != "eye" and sprite.speed_y > 5:
                    sprite.speed_y = 5

                if sprite.name != "player" and sprite.name != "red_key":
                    #tue le sprite si il meurtd
                    if sprite.death:
                        #drop un coeur avec 1 chance sur 4 quand il meurt
                        drop = random.randint(1, 4)
                        if drop == 1:
                            self.heart_drop.add(Heart(sprite.hitbox.x, sprite.hitbox.y, drop=True))

                        sprite.kill()

                sprite.on_ground = False

        # Gérer les collisions des sprites
                for rect in self.collisions:
                    if sprite.hitbox.colliderect(rect):

                        # Distance entre les bords
                        dx_right = sprite.hitbox.right - rect.left
                        dx_left = rect.right - sprite.hitbox.left
                        dy_bottom = sprite.hitbox.bottom - rect.top
                        dy_top = rect.bottom - sprite.hitbox.top

                        # Valeur absolue des distances
                        abs_dx = min(abs(dx_right), abs(dx_left))
                        abs_dy = min(abs(dy_bottom), abs(dy_top))

                        # Priorité à la collision la plus "profonde"
                        if abs_dx < abs_dy:
                            # Collision horizontale (mur gauche ou droit)
                            if dx_right > 0 and dx_right < dx_left:
                                # Mur à droite
                                sprite.hitbox.right = rect.left
                            else:
                                # Mur à gauche
                                sprite.hitbox.left = rect.right
                            sprite.rect.midbottom = sprite.hitbox.midbottom
                            sprite.position[0] = sprite.rect.left

                        else:
                            # Collision verticale (sol ou plafond)
                            if dy_bottom > 0 and dy_bottom < dy_top:
                                # Sol
                                sprite.hitbox.bottom = rect.top
                                sprite.speed_y = 0
                                sprite.on_ground = True
                                sprite.rect.midbottom = sprite.hitbox.midbottom
                            else:
                                # Plafond
                                sprite.hitbox.top = rect.bottom
                                sprite.speed_y = 0.7  # Ou 0
                                sprite.move_back_y()
                                sprite.position[1] += 1

#gere les rects echelle et regarde si le player en touche au moins une
        echelles_non_touchée = 0
        total_echelles = 0
        for echelle in self.echelle:
            total_echelles += 1
            if self.player.rect.colliderect(echelle):
                self.player.echelle = True
            else:
                echelles_non_touchée += 1
        if echelles_non_touchée == total_echelles:
            self.player.echelle = False

        # Vérifie si le player passe la porte
        if self.player.position[0] >= 250 and self.house_right.debut_jeu:
            self.house_right.debut_jeu = False
            self.collisions.append(self.door)

#regarde si le joueur tente d'ouvrir un coffre
        for chest in self.chest:
            if self.player.hitbox.colliderect(chest.rect):
                self.player.coffre = True
                if self.player.action and chest.closed and self.player.equip_item and self.player.equip_item["type"] == "key":
                    #ouvre qu'avec la clé
                    chest.closed = False
                    self.equip_item = False
                    self.inventory.remove(self.player.equip_item)

                if self.player.action and not chest.open and not chest.closed:
                    if chest.contenu == "red_key":
                        # Créer la red key qui saute
                        print("ouvert")
                        chest.open = True
                        self.red_key = Red_key(chest.rect.centerx, chest.rect.top - 32,(self.end_door.rect.right - 20, self.end_door.rect.top + 40))
                        self.all_sprites.add(self.red_key, layer=2)
                        self.red_key.speed_y = -5  # Impulsion vers le haut

                    else:
                        #ajout du contenu à l'inventaire
                        chest.open = True
                        self.inventory.append({"type": chest.contenu, "id": id(chest)})
                    self.player.action = False

#verifie si le joueur peut terminer le niveau
        if self.player.hitbox.colliderect(self.end_door.rect) and self.player.action:
            if self.end_door.statut == "closed" and self.red_key:
                if self.red_key.statut == "suivre":
                    self.red_key.aller_ouvrir_porte = True
            elif self.end_door.statut == "ouvert" and self.player.hitbox.left > self.end_door.rect.left and self.player.hitbox.right < self.end_door.rect.right and self.player.on_ground:
                self.all_sprites.change_layer(self.end_door, new_layer=5)
                self.end_door.statut = "closed"
                self.end_door.update()
                self.level_clear = True

#supprime la clé et ouvre la porte quand la clé a ouvert la porte
        if self.red_key and self.red_key.statut == "ouvert":
            self.end_door.statut = "ouvert"
            self.red_key.kill()

#donne equip item au joueur et appelle la fonction get hand position apres toutes ls modifications de upadate
        self.player.equip_item = self.equip_item
        self.player.get_hand_position()

    def draw_pause_menu(self):
        # Assombrit le fond
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        pause_font = pygame.font.Font(None, 64)
        section_font = pygame.font.Font(None, 36)
        object_font = pygame.font.Font(None, 20)

#cree interface menu
        title = pause_font.render("Menu pause", True, (255, 255, 255))
        self.screen.blit(title, (self.SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # Dessiner les flèches de navigation
        arrow_font = pygame.font.Font(None, 72)
        left_arrow = arrow_font.render("<", True, (255, 255, 255))
        right_arrow = arrow_font.render(">", True, (255, 255, 255))

        # Mettre en surbrillance si sélectionnées
        if self.menu_selection_index == "l":
            left_arrow = arrow_font.render("<", True, (255, 255, 0))
        elif self.menu_selection_index == "r":  # valeur spéciale pour droite
            right_arrow = arrow_font.render(">", True, (255, 255, 0))

        left_arrow_rect = left_arrow.get_rect()
        left_arrow_rect.topleft = (25, self.SCREEN_HEIGHT // 2)

        right_arrow_rect = right_arrow.get_rect()
        right_arrow_rect.topleft = (self.SCREEN_WIDTH - 50, self.SCREEN_HEIGHT // 2)

        self.screen.blit(left_arrow, left_arrow_rect)
        self.screen.blit(right_arrow, right_arrow_rect)
        # Dessiner les onglets de menu
        tab_x = 100
        for i, name in enumerate(self.menus):
            color = (255, 255, 0) if i == self.current_menu_index else (180, 180, 180)
            tab_text = section_font.render(name.upper(), True, color)
            self.screen.blit(tab_text, (tab_x, 130))
            tab_x += tab_text.get_width() + 50
        keys = pygame.key.get_pressed()

        #dessine le menu en fonction de l'onglet
        if self.menus[self.current_menu_index] == "inventaire":
            for i, text in enumerate(self.items.keys()):
                if type(self.items[text]) == list:
                    item_text = section_font.render(text, True, (255, 255, 255))
                    text_rect = item_text.get_rect()
                    text_rect.topleft = (100, 200 + i * 50)
                    self.items = {"Cœurs : ": str(self.player.life), "Objets : ": self.inventory}
                    self.screen.blit(item_text, text_rect)

                    for j, obj in enumerate(self.items[text]):
                        object = obj["type"]
                        object_id = obj["id"]

                        object_image = pygame.image.load(f"../sprites/objets/{object}.png").convert_alpha()
                        object_image = pygame.transform.scale(object_image, (32, 64))

                        object_rect = object_image.get_rect()
                        object_rect.width = object_rect.height

                        object_rect.left = text_rect.right + j * 75 + 15
                        object_rect.top = text_rect.top

                        text_object = object_font.render(object, True, (255, 255, 255))
                        text_object_rect = text_object.get_rect()

                        text_object_rect.centerx = object_rect.centerx
                        text_object_rect.top = object_rect.bottom +5

                        pygame.draw.rect(self.screen, (250,250,250), object_rect, 0)

                        self.screen.blit(object_image, (object_rect.x + 16, object_rect.y))
                        self.screen.blit(text_object, (text_object_rect.x, text_object_rect.y))

                        if obj == self.equip_item:
                            equip_rect = object_rect.copy()
                            equip_rect.width += 8
                            equip_rect.height += 8
                            equip_rect.x -= 4
                            equip_rect.y -= 4
                            pygame.draw.rect(self.screen, (255,255,0), equip_rect, 3)

                        if not self.actual_item in self.inventory:
                            if self.equip_item:
                                self.actual_item = self.equip_item
                            else:
                                self.actual_item = self.items[text][0]

                        if obj == self.actual_item:
                            actual_rect = object_rect.copy()

                            actual_rect.width += 8
                            actual_rect.height += 8
                            actual_rect.x -= 4
                            actual_rect.y -= 4

                else:
                    item_text = section_font.render(f"{text}{self.items[text]}", True, (255, 255, 255))
                    self.screen.blit(item_text, (100, 200 + i * 50))

        elif self.menus[self.current_menu_index] == "parametres":

            for idx, (label, value) in enumerate(self.parametres.items()):

                y_pos = 200 + idx * 50
                label_text = section_font.render(label, True, (255, 255, 255))
                self.screen.blit(label_text, (100, y_pos))

                # Affichage du bouton switch
                switch_rect = pygame.Rect(400, y_pos, 60, 30)
                switch_circle_pos = (switch_rect.left + 15, switch_rect.centery) if not value else (switch_rect.right - 15, switch_rect.centery)
                pygame.draw.rect(self.screen, (100, 100, 100), switch_rect, border_radius=15)

                if self.menu_selection_index == 0:
                    actual_rect = switch_rect.copy()
                    actual_rect.width += 8
                    actual_rect.height += 8
                    actual_rect.x -= 4
                    actual_rect.y -= 4

                if value:
                    pygame.draw.rect(self.screen, (100, 255, 100), switch_rect, border_radius=15)

                pygame.draw.circle(self.screen, (255, 255, 255), switch_circle_pos, 12)


        if self.menu_selection_index == "r":
            actual_rect = right_arrow_rect.copy()
            self.actual_item = "r"

        if self.menu_selection_index == "l" or (self.menus[self.current_menu_index] == "inventaire" and self.inventory == [] and self.actual_item != "r"):
            actual_rect = left_arrow_rect.copy()
            self.actual_item = "l"
            self.menu_selection_index = "l"

#dessine le rect de navigation
        pygame.draw.rect(self.screen, (255, 0, 0), actual_rect, 3)

#navigation dans le menu
        if keys[pygame.K_d]:
            if not self.keys_states[pygame.K_d]:
                if self.menu_selection_index != "r":

                    if self.menus[self.current_menu_index] == "inventaire":

                        if self.menu_selection_index == "l":

                                try:
                                    self.menu_selection_index = 0
                                    self.actual_item = self.items["Objets : "][self.menu_selection_index]

                                except:
                                    self.menu_selection_index = "r"
                                    self.actual_item = "r"

                        else:
                            index = self.items["Objets : "].index(self.actual_item) + 1

                            if index < len(self.items["Objets : "]):
                                self.actual_item = self.items["Objets : "][index]
                                self.menu_selection_index = index
                            else:
                                self.menu_selection_index = "r"
                                self.actual_item = "r"

                    elif self.menus[self.current_menu_index] == "parametres":
                        if self.menu_selection_index == "l":
                            self.menu_selection_index = 0
                            self.actual_item = 0

                        elif self.menu_selection_index == 0:
                            self.menu_selection_index = "r"
                            self.actual_item = "r"

            self.keys_states[pygame.K_d] = True
        else:
            self.keys_states[pygame.K_d] = False

        if keys[pygame.K_q]:
            if self.menu_selection_index != "l":
                if not self.keys_states[pygame.K_q]:
                    if self.menus[self.current_menu_index] == "inventaire":

                        if self.menu_selection_index == "r":
                            try:
                                self.menu_selection_index = len(self.items["Objets : "]) - 1
                                self.actual_item = self.items["Objets : "][self.menu_selection_index]
                            except:
                                self.menu_selection_index = "l"
                                self.actual_item = "l"

                        else:
                            index = self.items["Objets : "].index(self.actual_item) - 1

                            if index >= 0:
                                self.actual_item = self.items["Objets : "][index]
                                self.menu_selection_index = index
                            else:
                                self.menu_selection_index = "l"
                                self.actual_item = 'l'

                    elif self.menus[self.current_menu_index] == "parametres":
                        if self.menu_selection_index == "r":
                            self.menu_selection_index = 0
                            self.actual_item = 0

                        elif self.menu_selection_index == 0:
                            self.menu_selection_index = "l"
                            self.actual_item = "l"


            self.keys_states[pygame.K_q] = True
        else:
            self.keys_states[pygame.K_q] = False

#bouton d'action pour selectoionner
        if keys[pygame.K_RIGHT]:
            if not self.keys_states[pygame.K_RIGHT]:
                if self.actual_item == "r":
                    if self.current_menu_index == len(self.menus) - 1:
                        self.current_menu_index = 0
                    else:
                        self.current_menu_index+=1
                elif self.actual_item == "l":
                    if self.current_menu_index == 0:
                        self.current_menu_index = len(self.menus) - 1
                    else:
                        self.current_menu_index -=1
                elif self.menus[self.current_menu_index] == "inventaire":

                    if self.actual_item != self.equip_item:
                        self.equip_item = self.actual_item
                    else:
                        self.equip_item = False
                elif self.menus[self.current_menu_index] == "parametres":
                    if self.actual_item == 0:
                        self.parametres["Afficher les rects : "] = not self.parametres["Afficher les rects : "]
            self.keys_states[pygame.K_RIGHT] = True

        else:
            self.keys_states[pygame.K_RIGHT] = False


    def death(self):
#cree interface lorsqu'on meurt
        death_text = self.font.render("Game Over", True, self.RED)
        retry_text = self.font.render("Recommencer", True, self.BLACK)
        quit_text = self.font.render("Quitter", True, self.BLACK)

        death_rect = death_text.get_rect(center=(self.SCREEN_WIDTH//2, self.SCREEN_HEIGHT// 3))
        retry_rect = retry_text.get_rect(center=(self.SCREEN_WIDTH // 2, 2*self.SCREEN_HEIGHT // 3))
        quit_rect = quit_text.get_rect(center=(self.SCREEN_WIDTH // 2, 4*self.SCREEN_HEIGHT // 5))

        while True:
            self.screen.fill(self.BLACK)

            mouse_pos = pygame.mouse.get_pos()

            # dessine boutons
            #change de couleur si survolé
            if retry_rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, self.BLUE, retry_rect.inflate(20, 10))
            else:
                pygame.draw.rect(self.screen, self.WHITE, retry_rect.inflate(20, 10))

            if quit_rect.collidepoint(mouse_pos):
                pygame.draw.rect(self.screen, self.BLUE, quit_rect.inflate(20, 10))
            else:
                pygame.draw.rect(self.screen, self.WHITE, quit_rect.inflate(20, 10))

            self.screen.blit(death_text, death_rect)
            self.screen.blit(retry_text, retry_rect)
            self.screen.blit(quit_text, quit_rect)

            pygame.display.flip()

#gere les evenements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if retry_rect.collidepoint(event.pos):

                        return  # Recommencer
                    elif quit_rect.collidepoint(event.pos):
                        pygame.quit()
                        sys.exit()

    def fin_niveau_animation(self):
        #interface fin du niveau
        clock = pygame.time.Clock()
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        text = self.font.render("Niveau terminé !", True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.SCREEN_WIDTH // 2, self.SCREEN_HEIGHT // 2))

        for alpha in range(0, 256, 5):
            overlay.set_alpha(alpha)

            # Redessine la dernière image de jeu (optionnel)
            self.screen.fill((0, 0, 0))
            for layer in self.tmx_data.visible_layers:
                if isinstance(layer, pytmx.TiledTileLayer):
                    for x, y, gid in layer:
                        tile = self.tmx_data.get_tile_image_by_gid(gid)
                        if tile:
                            world_x = x * self.tile_width
                            world_y = y * self.tile_height
                            tile_rect = pygame.Rect(world_x, world_y, self.tile_width, self.tile_height)
                            self.screen.blit(tile, self.camera.apply(tile_rect))

            for sprite in self.all_sprites:
                self.screen.blit(sprite.image, self.camera.apply(sprite.rect))

            self.screen.blit(overlay, (0, 0))
            self.screen.blit(text, text_rect)

            pygame.display.flip()
            clock.tick(60)
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

    def run(self):
        #cree surface de demarrage et de jeu
        start_surface = self.create_start_screen()
        game_surface = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        self.all_sprites.update()
        self.render_game_to_surface_for_transition(game_surface) # Render initial game state for the transition

        running = True
        clock = pygame.time.Clock()

        # boucle de demarrage
        while running:
            if self.recommencer:
                break
            else:

                self.screen.blit(start_surface, (0, 0))
                pygame.display.flip()

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                        running = False # Exit start screen loop

        # Transition au jeu

        self.fade_transition(start_surface, game_surface, duration=60, screen=self.screen)

        # boucle principale
        running = True
        while running:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            #dessine les tuiles
            for layer in self.tmx_data.visible_layers:
                if isinstance(layer, pytmx.TiledTileLayer):
                    for x, y, gid in layer:
                        tile = self.tmx_data.get_tile_image_by_gid(gid)
                        if tile:
                            world_x = x * self.tile_width
                            world_y = y * self.tile_height
                            tile_rect = pygame.Rect(world_x, world_y, self.tile_width, self.tile_height)
                            self.screen.blit(tile, self.camera.apply(tile_rect))

            if not self.paused:
                # appelle la foncion handle input du joueur
                if self.player.life > 0:
                    self.player.handle_input()  # Processes keyboard inputs
                    self.update()
                else:
                    if self.player.invincible >= 3.5:
                        #appelle la fonction death et remet toutes les variables comme au debut si il recommence
                        self.death()
                        self.__init__()
                        self.recommencer = True
                        self.run()
                    self.player.update()
                    self.heart.update()

            keys = pygame.key.get_pressed()
            #ouvre menu pause si TAB est pressé
            if keys[pygame.K_TAB] and self.player.life > 0:
                if  not self.keys_states[pygame.K_TAB]:
                    self.paused = not self.paused
                    self.keys_states[pygame.K_TAB] = True
            else:
                self.keys_states[pygame.K_TAB] = False

            #dessine les sprites
            for sprite in self.all_sprites:
                self.screen.blit(sprite.image, self.camera.apply(sprite.rect))

            if self.player.equip_item:

                self.screen.blit(self.player.arme_image, self.camera.apply(self.player.rect_arme))
                self.screen.blit(self.player.hand_image, self.camera.apply(self.player.rect))
                if self.player.attaque and self.player.current_frame == 1:
                    self.screen.blit(self.player.attaque_image, self.camera.apply(self.player.rect_arme_attaque))

#dessine animation attaque si il y en a une
            for sprite in self.all_sprites:
                if sprite.entity:
                    if sprite.can_attack:
                        if sprite.rect_attaque != sprite.hitbox:
                            if sprite.affichage_attaque:
                                self.screen.blit(sprite.attaque_image, self.camera.apply(sprite.rect_attaque))

#affiche les rects et hitbox si activé
            if self.parametres["Afficher les rects : "]:
                if self.player.equip_item:
                    pygame.draw.rect(self.screen, (255, 0, 255), self.camera.apply(self.player.hand_position_rect), 1)

                for sprite in self.all_sprites:
                    pygame.draw.rect(self.screen, (255, 0, 0), self.camera.apply(sprite.hitbox), 1)
                    pygame.draw.rect(self.screen, (0, 255, 0), self.camera.apply(sprite.rect), 1)
                    if sprite.entity:
                        if sprite.can_attack:
                            if sprite.rect_attaque != sprite.hitbox:
                                if sprite.affichage_attaque:
                                    pygame.draw.rect(self.screen, (255, 0, 0), self.camera.apply(sprite.rect_attaque),1)

                for collision in self.collisions:
                    pygame.draw.rect(self.screen, (255, 0, 0), self.camera.apply(collision), 1)

            #dessine les coeurs du joueur et les coeurs laissés par les ennemis mort
            for heart in self.heart:
                self.screen.blit(heart.image, heart.rect)
            for heart in self.heart_drop:
                self.screen.blit(heart.image, self.camera.apply(heart.rect))

            #affiche le menu pause
            if self.paused:
                self.draw_pause_menu()

            #affiche l;'interface de fin du niveau
            if self.level_clear:
                self.fin_niveau_animation()

            pygame.display.flip() # Update the full display surface

            clock.tick(60) # Cap the frame rate

        pygame.quit()
        sys.exit()