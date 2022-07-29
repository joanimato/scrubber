import os

from rdkit import Chem

# this is the subdirectory name (with respect to the path of this file) where
# the the default datafiles are stored
DATA_DIR = "data"
DATA_PATH = os.path.join(os.path.dirname(__file__), DATA_DIR)


# from . import storage, scrubbercore

# TODO modify behavior so if the default options are empty, default_init is returned? (brittle!!!)


# an rdkit mol instance is this: Chem.rdchem.Mol

__all__ = ["DATA_PATH", "ScrubberBase", "UniqueMoleculeContainer"]


class ScrubberBase():
    """abstract class with the basic functionality that most (all?) Scrubber
    classes should have.
    A class method provide access to the class init defaults by returning the
    class `__init__` signature with default values as a dictionary
    `{arg:default_value}`.

    Inheriting classes should not run the base class __init__() method, but
    they must implement the `_stop_at_defaults` argument (preferably as the
    last one) to guarantee the `get_defaults` method works properly.
    >>> class ScrubberNewClass(ScrubberClass):
    ...
    ...     [ class implementation here ]
    ...
    # to present init options to a driver class:
    >>> scrubber_class_options = ScrubberNewClass.get_defaults()
    >>> scrubber_class_options['key'] = False
    >>> sc = ScrubberClassNew(**scrubber_class_options)
    """
    def __init__(self, arguments=None, _stop_at_defaults: bool = False):
        """generic implementation of the init;
        inheriting classes will implement their own args, but keep the
        __stop_at_defaults flag to support the get_defaults() class method and
        add the clause below to allow early termination.

        This method will create a disposable instance from which the defaults
        will be extractedcore.
        """
        # print("GOT HERE, TOO")
        self.options = {}
        if _stop_at_defaults:
            return

    @classmethod
    def get_defaults(cls):
        """method to return the default values of init options"""
        return cls(_stop_at_defaults=True).__dict__

    def get_datafile(self, fname: str) -> str:
        """helper function to provide the full-path of data files available in
        the Scrubber module default
        location ("scrubber/data", defined by the DATA_DIR variable)"""
        fullpath = os.path.join(DATA_PATH, fname)
        if not os.path.exists(fullpath):
            msg = (
                "ERROR: the specified filename [%s] "
                "does not exist in the data "
                "directory [%s]" % (fname, DATA_PATH),
            )
            raise ValueError(msg)
        return fullpath

    def _build_opts_dict(self):
        """build and populate the self.options dictionary"""
        self.options = self.__dict__.copy()


class UniqueMoleculeContainer():
    """Class to store RDKit molecules without duplicates. Isomeric
    canonical SMILES are used as unique keys, unless chirality is disabled when
    the class is initialized.
    The container can be "sealed" to track any modifications (add/remove
    molecules, etc.) by changing the 'sealed' attribute.

    Initialization and addition of molecules:
        >>> x = UniqueMoleculeContainer([mol1, mol1, mol2, mol3])
        >>> print(x)
        MoleculeContainer (3 mols):
        > NC(Cc1nc2[nH]ncn2n1)C(=O)O
        > NC(Cc1nn2cnnc2[nH]1)C(=O)O
        > NC(Cc1nc2nncn2[nH]1)C(=O)O
        >>> len(x)
        3
        >>> for mol in x:
        ...     print(m)
        ...
        <Chem.rdchem.Mol object at 0x1462f1e36be0>
        <Chem.rdchem.Mol object at 0x1462f1e36dc0>
        <Chem.rdchem.Mol object at 0x1462f1e36c40>
        >>> x.add(mol3)
        False           # the molecule is already present in the container
        >>> len(x)
        3
        >>> x.add(mol4)
        True           # the molecule is not present in the container
        >>> len(x)
        4
        >>> for m in x:
        ...     print(m)
        ...
        <Chem.rdchem.Mol object at 0x1462f1e36be0>
        <Chem.rdchem.Mol object at 0x1462f1e36dc0>
        <Chem.rdchem.Mol object at 0x1462f1e36c40>
        <Chem.rdchem.Mol object at 0x1462f1e36b80>

    Molecules can be retrieved using the 'get' method with a SMILES or using indices:
        >>> x.get("c1cccccc1")
        <Chem.rdchem.Mol object at 0x1462f1e36be0>
        >>> x[2]
        <Chem.rdchem.Mol object at 0x1462f1e36be0>

    Two containers are identical if they contain the same molecules:
        >>> x = UniqueMoleculeContainer([mol1, mol2, mol3])
        >>> y = UniqueMoleculeContainer([mol3, mol1, mol2])
        >>> x == y
        True

    An independent copy of a container can be generated by initializing a new
    container with the original one:
        >>> x = UniqueMoleculeContainer([mol1, mol2, mol3])
        >>> y = UniqueMoleculeContainer(x)

    By default the container is initialized as 'sealed'
        >>> x = UniqueMoleculeContainer([mol1, mol2, mol3], sealed=True)
        >>> x.sealed # initialized as sealed
        True

    Successful operations that modify the container will break the seal
        >>> x.add(mol3)  # adding an existing molecule
        False            # unsuccessful (duplicate)
        >>> x.sealed     # seal intact
        True
        >>> x.add(mol4)  # adding a new molecule
        True             # successful (new molecule)
        >>> x.sealed     # seal broken
        False
        >>> x.sealed = True # the container can be re-sealed at any time

    Molecular containers can be combined together with the '+' operator
        >>> x = UniqueMoleculeContainer([mol1, mol2, mol3])
        >>> y = UniqueMoleculeContainer([mol3, mol4, mol5])
        >>> z = x + y # duplicate molecules are merged automatically
        >>> len(z)
        5

    or incremented with the '+=' operator
        >>> x = UniqueMoleculeContainer([mol1, mol2, mol3])
        >>> y = UniqueMoleculeContainer([mol3, mol4, mol5])
        >>> x += y # duplicate molecules are merged automatically
        >>> len(x)
        5

    Molecules can be removed by passing an RDKit molecule
        >>> x = UniqueMoleculeContainer([mol1, mol2, mol3])
        >>> x.remove_mol(mol2)
        True
        >>> len(x)
        2
        >>> x.remove_mol(mol_non_existent)
        False
        >>> len(x)
        2

    or by passing a SMILES string
        >>> x.remove_smiles("c1ccccc1")
        True # the SMILES was found

    or by passing an iterable object of integers (will return the list of
    smiles removed; if an index is not found, an IndexValue exception will be
    raised):
        >>> x.remove_from_indices( (0,2,6,9) )
        ['c1cccccc1', 'c1cccncc1', ...]

    Molecule containers can be consumed with the pop() method:
        >>> x = UniqueMoleculeContainer([mol1, mol2, mol3])
        >>> for i in range(len(x)):
        ...     mol = x.pop()
        ...     # process molecule
        >>> print(x)
        >>>

    Intersection (AND) and difference (NOT) boolean operations are possible:
        >>> x = UniqueMoleculeContainer([mol1, mol2, mol3])
        >>> y = UniqueMoleculeContainer([mol3, mol4, mol5])
        >>> x & y  # intersection (AND)
        <Chem.rdchem.Mol object at 0x1462f1e36c40>  # mol3
        >>> x - y  # difference (NOT)
        <Chem.rdchem.Mol object at 0x1462f1e36b80>  # mol1
        <Chem.rdchem.Mol object at 0x1462f1e36be0>  # mol2
    """

    def __init__(
        self, argument=None, sealed: bool = True, ignore_chirality: bool = False
    ):
        self.__data = {}
        self.sealed = sealed
        self.__chirality = not ignore_chirality
        if not argument is None:
            if isinstance(argument, UniqueMoleculeContainer):
                # TODO check if shallow copy is sufficient!
                self.__data = argument.__data.copy()
                # for k, v in argument.__data.items():
                #     self.__data[k] = v
            elif isinstance(argument, list) or isinstance(argument, tuple):
                for m in argument:
                    self.add(m)
                    self.sealed = False
            else:
                raise TypeError(
                    "UniqueMoleculeContainer can be initialized with a list or "
                    "tuple of RDKit.Mol objects or another UniqueMoleculeContainer, not %s"
                    % type(argument)
                )

    def add(self, mol:Chem.rdchem.Mol, replace=False) -> bool:
        """add RDKit molecule if not present already; if replace==False, then the
        molecule is replaced with the new mol object"""
        # key = Chem.MolToSmiles(Chem.RemoveHs(mol), isomericSmiles=self.__chirality)
        key = mol2smi(mol, self.__chirality)
        if key in self.__data and not replace:
            return False
        self.__data[key] = mol
        self.sealed = False
        return True

    def remove_smiles(self, smiles: str) -> bool:
        """remove a molecule using a SMILES string and return True, otherwise
        False is returned"""
        try:
            del self.__data[smiles]
            self.sealed = False
            return True
        except:
            return False

    def remove_mol(self, mol: Chem.rdchem.Mol) -> bool:
        """remove a Chem.RDKit molecule specified explicitly and return True, otherwise
        False is returned"""
        # smiles = Chem.MolToSmiles(Chem.RemoveHs(mol), isomericSmiles=self.__chirality)
        smiles = mol2smi(mol, self.__chirality)
        return self.remove_smiles(smiles)

    def remove_mols(self, mol_list: list) -> bool:
        """remove a list of RDKit molecules"""
        if mol_list == []:
            return True
        success = False
        for mol in mol_list:
            if not self.remove_mol(mol):
                success = False
        return success

    def remove_from_indices(self, indices_list: list) -> str:
        """remove a list of indices and return the corresponding SMILES"""
        keys_list = list(self.__data.keys())
        smi_list = [keys_list[i] for i in indices_list]
        for smi in smi_list:
            self.remove_smiles(smi)
        return smi_list

    def get(self, key:str, default=None):
        """implement the get method to retrieve RDKit Mol objects using a
        SMILES string with a default value for missing items (default=None).
            >>> x = UniqueMoleculeContainer([mol1, mol2, mol3])
            >>> x.get("NON-EXISTENT", None)
            >>> x.get("c1cccccc1")
            <Chem.rdchem.Mol object at 0x152290864ac0>
        """
        try:
            self.__getitem__(key)
        except:
            return default

    def pop(self, index=0)->Chem.rdchem.Mol:
        """pop molecules from the container. If no index is provided, the first
        molecule in the container gets removed"""
        try:
            key = list(self.__data.keys())[index]
            mol = self.__data[key]
            del self.__data[key]
            return mol
        except IndexError:
            size = len(self.__data)
            if size == 0:
                msg = "Empty container."
            else:
                msg = "Valid index must be between 0 and %d, but %d was used." % (
                    size,
                    index,
                )
            raise IndexError(msg)

    def copy(self)->"UniqueMoleculeContainer":
        """return a (shallow) copy of the container"""
        return UniqueMoleculeContainer(self)

    def keys(self)->list:
        """return all molecule keys (SMILES)"""
        return list(self.__data.keys())

    def clear(self)->None:
        """remove all molecules in the container; if the container is empty,
        the seal will not be broken"""
        self.sealed = len(self.__data) == 0
        del self.__data
        self.__data = {}

    def __repr__(self):
        """create representation of the molecules contained"""
        return "\n  - ".join(self.__data.keys())

    def __str__(self):
        """string representation"""
        # DEBUG
        buff = []
        for m in self.__data.keys():
            buff.append("  - %s" % m)
        return "\n".join(buff)

        if len(self.__data) == 0:
            msg = "MoleculeContainer (empty)"
        else:
            msg = "MoleculeContainer (%d mols):\n> %s" % (
                len(self),
                "\n> ".join(list(self.__data.keys())),
            )
        return msg

    def __iter__(self):
        """re-initialize the counter every time a new iterator is requested for
        this container"""
        self.__index = -1
        return self

    def __next__(self):
        """ """
        self.__index += 1
        if self.__index > len(self.__data) - 1:
            raise StopIteration
        key = list(self.__data.keys())[self.__index]
        return self.__data[key]

    def __add__(self, other:"UniqueMoleculeContainer"):
        """overload add operator (+)
        UniqueMoleculeContainer = UniqueMoleculeContainer + UniqueMoleculeContainer
        """
        new = UniqueMoleculeContainer(self)
        for k, v in other.__data.items():
            if not k in new.__data:
                self.sealed = False
                new.__data[k] = v
        return new

    def __radd__(self, other:"UniqueMoleculeContainer")->"UniqueMoleculeContainer":
        """overload right-add operator ( x + self )
        UniqueMoleculeContainer = [ mol ] + UniqueMoleculeContainer
        """
        return self.__add__(other)

    def __iadd__(self, other:"UniqueMoleculeContainer")->"UniqueMoleculeContainer":
        """overlad increment operator (+=)
        UniqueMoleculeContainer += UniqueMoleculeContainer
        """
        for k, v in other.__data.items():
            if not k in self.__data:
                self.sealed = False
                self.__data[k] = v
        return self

    def __len__(self):
        """return the length of the container"""
        return len(self.__data.keys())

    def __contains__(self, mol:Chem.rdchem.Mol):
        """membership operator
        >>> x = UniqueMoleculeContainer([mol1, mol2, mol3])
        >>> mol1 in x
        True
        """
        key = mol2smi(mol, self.__chirality)
        return key in self.__data

    def __getitem__(self, key):
        """return the molecule using the SMILES or the index
        >>> x = UniqueMoleculeContainer([mol1, mol2, mol3])
        >>> m = x[1]
        <Chem.rdchem.Mol object at 0x152290864ac0>
        >>> m = x["c1ccccc1"]
        <Chem.rdchem.Mol object at 0x152290864ac0>

        If the key is not found, a KeyError exception is raised. For a safe
        access to molecules use the `get(key, default)` method, which allows to
        specify the default value returned if the molecule is not found
        (similarly to Python dictionaries)
        """
        if isinstance(key, str):
            return self.__data[key]
        if isinstance(key, int):
            key = list(self.__data)[key]
            return self.__data[key]
        raise TypeError(
            "molecular container indices must be integers or SMILES strings, not %s"
            % (type(key))
        )

    def __eq__(self, other):
        """return if this container is equal to the other container"""
        return set(self.__data.keys()) == set(other.__data.keys())

    def __and__(self, other):
        """implement the intersection ('&') operator and return a new container
        with molecules contained in both containers"""
        new = UniqueMoleculeContainer()
        for mol in self.__data.values():
            if not mol in other:
                continue
            new.add(mol)
        return new

    def __sub__(self, other):
        """implement the subtraction operator and return a new container with
        molecules present only on the first container"""
        new = UniqueMoleculeContainer()
        for mol in self.__data.values():
            if not mol in other:
                new.add(mol)
        return new


def mol2smi(mol, chirality=True):
    """convenience function to generate RDKit canonical and isomeric SMILES"""
    return Chem.MolToSmiles(
        Chem.RemoveHs(mol), isomericSmiles=chirality, canonical=True
    )


def copy_mol_properties(
    mol_source,
    mol_dest,
    strict: bool = False,
    include_name: bool = True,
    exclude: list = None,
):
    """convenience function to copy properties from a molecule to another; if
    strict mode is requested, only molecules in the source molecule will be
    kept in the destination molecule; an optional list of excluded properties
    can be provided

    computed properties are not copied
    """
    exclude = exclude or []
    input_properties = mol_source.GetPropsAsDict()
    # print("PROCESSING HTESE PROPERTIES", input_properties)
    for p, v in input_properties.items():
        if "_scrubber_tmp_" in p:
            continue
        if p in exclude:
            continue
        if type(v) == int:
            mol_dest.SetIntProp(p, v)
        elif type(v) == bool:
            mol_dest.SetBoolProp(p, v)
        elif type(v) == float:
            mol_dest.SetDoubleProp(p, v)
        elif type(v) == str:
            mol_dest.SetProp(p, v)
    if include_name:
        if not mol_source.HasProp("_Name"):
            return
        name = mol_source.GetProp("_Name")
        mol_dest.SetProp("_Name", name)
