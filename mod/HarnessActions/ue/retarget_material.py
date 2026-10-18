import os
import sys
import unreal

# Spec 33. Give an already imported mesh the game material. Environment: MESH_PATH (object path of the static mesh).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import meshy_material

PATH = os.environ["MESH_PATH"]
mesh = unreal.load_asset(PATH)
meshy_material.make_game_material(mesh, PATH.rsplit("/", 1)[0])
unreal.log("RETARGET done " + PATH)
