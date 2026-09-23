"""Noms français des 80 catégories COCO détectées par YOLO26."""

FRENCH = {
    'person': 'personne', 'bicycle': 'vélo', 'car': 'voiture', 'motorcycle': 'moto', 'airplane': 'avion',
    'bus': 'bus', 'train': 'train', 'truck': 'camion', 'boat': 'bateau', 'traffic light': 'feu tricolore',
    'fire hydrant': "bouche d'incendie", 'stop sign': 'panneau stop', 'parking meter': 'parcmètre',
    'bench': 'banc', 'bird': 'oiseau', 'cat': 'chat', 'dog': 'chien', 'horse': 'cheval', 'sheep': 'mouton',
    'cow': 'vache', 'elephant': 'éléphant', 'bear': 'ours', 'zebra': 'zèbre', 'giraffe': 'girafe',
    'backpack': 'sac à dos', 'umbrella': 'parapluie', 'handbag': 'sac à main', 'tie': 'cravate',
    'suitcase': 'valise', 'frisbee': 'frisbee', 'skis': 'skis', 'snowboard': 'snowboard',
    'sports ball': 'ballon', 'kite': 'cerf-volant', 'baseball bat': 'batte de baseball',
    'baseball glove': 'gant de baseball', 'skateboard': 'skateboard', 'surfboard': 'planche de surf',
    'tennis racket': 'raquette de tennis', 'bottle': 'bouteille', 'wine glass': 'verre à vin', 'cup': 'tasse',
    'fork': 'fourchette', 'knife': 'couteau', 'spoon': 'cuillère', 'bowl': 'bol', 'banana': 'banane',
    'apple': 'pomme', 'sandwich': 'sandwich', 'orange': 'orange', 'broccoli': 'brocoli', 'carrot': 'carotte',
    'hot dog': 'hot-dog', 'pizza': 'pizza', 'donut': 'donut', 'cake': 'gâteau', 'chair': 'chaise',
    'couch': 'canapé', 'potted plant': 'plante en pot', 'bed': 'lit', 'dining table': 'table',
    'toilet': 'toilettes', 'tv': 'télévision', 'laptop': 'ordinateur portable', 'mouse': 'souris',
    'remote': 'télécommande', 'keyboard': 'clavier', 'cell phone': 'téléphone', 'microwave': 'micro-ondes',
    'oven': 'four', 'toaster': 'grille-pain', 'sink': 'évier', 'refrigerator': 'réfrigérateur', 'book': 'livre',
    'clock': 'horloge', 'vase': 'vase', 'scissors': 'ciseaux', 'teddy bear': 'ours en peluche',
    'hair drier': 'sèche-cheveux', 'toothbrush': 'brosse à dents',
}


def french(name):
    label = FRENCH.get(name, name)
    return label[:1].upper() + label[1:]
