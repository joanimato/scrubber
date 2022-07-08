import sys, os
from rdkit import Chem
from time import sleep
sys.path.append("../")
try:
    from scrubber.core import ScrubberCore
except Exception as e:
    print("The script must be executed from the script/ directory")
    raise e

def dock(mol):
    print("Docking molecule: |-",  end="")
    for i in range(10):
        print("-", end="")
        sys.stdout.flush()
        sleep(0.2)
    print("| DONE!")


if __name__ == "__main__":
    smiles = "O=C([C@H](CC1=CNC=N1)N)O histidine"
    # get and customize configuration (these should be the defaults)

    config = ScrubberCore.get_defaults()
    config["isomers"]["active"] = True
    config["isomers"]["values"]["tauto_enum"] = True
    config["isomers"]["values"]["proto_enum"] = True
    config["isomers"]["values"]["ph_datafile"] = "..//scrubber/data/test_model.txt"
    # initialize the scrubber
    scrub = ScrubberCore(config)
    mol = Chem.MolFromSmiles(smiles)
    for m in scrub.process(mol):
        dock(mol)

