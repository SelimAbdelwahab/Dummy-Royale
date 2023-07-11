import pygame as pg

defaultSurface = pg.Surface((10, 10))
defaultSurface.set_colorkey((132, 132, 132))
defaultSurface.fill(defaultSurface.get_colorkey())

# M1911 images
M1911_IMAGE_TOP = pg.image.load("assets/game/guns/M1911_top.png").convert()
M1911_IMAGE_TOP = pg.transform.scale(M1911_IMAGE_TOP, (round(M1911_IMAGE_TOP.get_size()[0] / 11.25),
                                                       round(M1911_IMAGE_TOP.get_size()[1] / 11.25)))

M1911_IMAGE_TOP_SIZE = M1911_IMAGE_TOP.get_size()

M1911_IMAGE_SIDE = pg.image.load("assets/game/guns/M1911_side.png")
M1911_IMAGE_SIDE = pg.transform.scale(M1911_IMAGE_SIDE,
                                      (round(M1911_IMAGE_SIDE.get_size()[0] / 6),
                                       round(M1911_IMAGE_SIDE.get_size()[1] / 6)))
M1911_IMAGE_SIDE_SIZE = M1911_IMAGE_SIDE.get_size()

# Revolver images
REVOLVER_IMAGE_TOP = pg.image.load("assets/game/guns/revolver_top.png").convert()
REVOLVER_IMAGE_TOP = pg.transform.scale(REVOLVER_IMAGE_TOP, (round(REVOLVER_IMAGE_TOP.get_size()[0] / 6.75),
                                                             round(REVOLVER_IMAGE_TOP.get_size()[1] / 11.25)))
REVOLVER_IMAGE_TOP_SIZE = REVOLVER_IMAGE_TOP.get_size()

REVOLVER_IMAGE_SIDE = pg.image.load("assets/game/guns/Revolver_side.png")
REVOLVER_IMAGE_SIDE = pg.transform.scale(REVOLVER_IMAGE_SIDE,
                                         (round(REVOLVER_IMAGE_SIDE.get_size()[0] / 6),
                                          round(REVOLVER_IMAGE_SIDE.get_size()[1] / 6)))

REVOLVER_IMAGE_SIDE_SIZE = REVOLVER_IMAGE_SIDE.get_size()

# AWP images
AWP_IMAGE_TOP = pg.image.load("assets/game/guns/AWP_top.png").convert()
AWP_IMAGE_TOP = pg.transform.scale(AWP_IMAGE_TOP,
                                   (round(AWP_IMAGE_TOP.get_size()[0] / 3.375),
                                    round(AWP_IMAGE_TOP.get_size()[1] / 6.75)))

AWP_IMAGE_TOP_SIZE = AWP_IMAGE_TOP.get_size()

AWP_IMAGE_SIDE = pg.image.load("assets/game/guns/AWP_side.png")
AWP_IMAGE_SIDE = pg.transform.scale(AWP_IMAGE_SIDE, (133, 40))

AWP_IMAGE_SIDE_SIZE = AWP_IMAGE_SIDE.get_size()
