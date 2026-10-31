# 🎮 Zelda Bros - Projet POO (Terminale)

Mon projet de spécialité de terminale et ma première véritable expérience avec la Programmation Orientée Objet (POO) en Python. 

Il s'agit d'un jeu de plateforme stratégique baptisé "Zelda bros". On peut y récupérer des clés dans des coffres, s'équiper d'armes pour vaincre divers monstres, et trouver la fameuse clé rouge pour déverrouiller la porte de fin de niveau.

<img width="1002" height="790" alt="image" src="https://github.com/user-attachments/assets/d72dedfa-fca5-4e64-b4f3-484c98ebf76d" />


## ✨ Fonctionnalités
* **Système d'inventaire et Menu Pause :** Gestion des clés et des armes équipables via un menu interactif, ainsi qu'un onglet de paramètres pour afficher les boîtes de collision (hitboxes).
* **Combat et Santé :** Un système de points de vie représenté par des cœurs, des frames d'invincibilité après avoir subi des dégâts, et un système de recul.
* **Comportements avancés :** Des ennemis variés comme le "Gluglu" qui patrouille et charge le joueur, ou l'"Eye" qui tire des lasers.
* **Entités dynamiques :** Une clé rouge vivante ("Red_key") qui fuit le joueur, s'évanouit si on l'attaque, puis le suit pour ouvrir la porte finale.
* **Level Design :** Cartes créées sur Tiled, importées dynamiquement avec des échelles, des portes, et une caméra fluide qui suit le joueur tout en restant dans les limites de la carte.

## 🛠️ Technologies utilisées
* **Langage :** Python 3.12
* **Moteur de jeu :** Pygame
* **Gestion des cartes :** `pytmx` (pour lire les fichiers `.tmx` générés par Tiled)
