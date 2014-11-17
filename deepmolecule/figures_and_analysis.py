import os
import itertools
import numpy as np
import matplotlib
#matplotlib.use('Agg')   # Cluster-friendly backend.  TODO: Add a flag depending on Odyssey.
import matplotlib.pyplot as plt

from rdkit import Chem
from rdkit.Chem import Draw

from features import N_atom_features, N_bond_features


def plot_learning_curve(results_filename, outdir):
    curve = np.load(results_filename)['learning_curve']
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    fig = plt.figure()
    fig.add_subplot(1,1,1)
    plt.plot(curve)
    matplotlib.rcParams.update({'font.size': 16})
    plt.xlabel("Epoch")
    plt.ylabel("Training Loss")
    plt.savefig(os.path.join(outdir, 'learning_curve.png'))
    plt.close()

def plot_predictions(results_filename, outdir):
    """Generates prediction vs actual scatterplots."""
    def scatterplot(x, y, title, outfilename):
        fig = plt.figure()
        fig.add_subplot(1,1,1)
        plt.scatter(x, y)
        matplotlib.rcParams.update({'font.size': 16})
        plt.xlabel("predicted " + target_name)
        plt.ylabel("true " + target_name)
        plt.title(title)
        plt.savefig(os.path.join(outdir, outfilename + '.png'))
        plt.savefig(os.path.join(outdir, outfilename + '.eps'))
        plt.close()

    preds = np.load(results_filename)
    target_name = str(preds['target_name'])
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    scatterplot(preds['train_preds'], preds['train_targets'],
                "Training Accuracy on " + target_name, "training_" + target_name)
    scatterplot(preds['val_preds'], preds['val_targets'],
                "Validation Accuracy on " + target_name, "val_" + target_name)
    scatterplot(preds['test_preds'], preds['test_targets'],
                "Test Accuracy on " + target_name, "testing_" + target_name)


def plot_maximizing_inputs(net_building_func, weights_file, outdir):
    """Plots the molecular fragment which maximizes each hidden unit of the network."""

    # Build the network
    saved_net = np.load(weights_file)
    trained_weights = saved_net['weights']
    arch_params = saved_net['arch_params'][()]
    _, _, _, hidden_layer, zero_weights = net_building_func(**arch_params)
    assert(len(trained_weights) == zero_weights.N)

    # Make a set of smiles to search over.
    def generate_smiles_list():
        fragments = ['C', 'N', 'O', 'c1ccccc1', 'F', "CC(C)C","NC(=O)C"]
        return [''.join(s) for s in itertools.combinations_with_replacement(fragments, 2)]
    smiles_list = np.array(generate_smiles_list())

    # Evaluate on the network and find the best smiles.
    input_scores = hidden_layer(trained_weights, smiles_list)
    max_smiles_ixs = np.argmax(input_scores, axis=0)
    min_smiles_ixs = np.argmin(input_scores, axis=0)

    # Now draw them and save the images.
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    for n, ix in enumerate(max_smiles_ixs):
        mol = Chem.MolFromSmiles(smiles_list[ix])
        outfilename = os.path.join(outdir, 'hidden-unit-' + str(n) + '-maximizing.png')
        Draw.MolToFile(mol, outfilename, fitImage=True)

    for n, ix in enumerate(min_smiles_ixs):
        mol = Chem.MolFromSmiles(smiles_list[ix])
        outfilename = os.path.join(outdir, 'hidden-unit-' + str(n) + '-minimizing.png')
        Draw.MolToFile(mol, outfilename, fitImage=True)


def plot_weight_meanings(net_building_func, weights_file, outdir, outfilename):
    saved_net = np.load(weights_file)
    trained_weights_vec = saved_net['weights']
    arch_params = saved_net['arch_params'][()]
    _, _, _, _, weights_container = net_building_func(**arch_params)
    assert(len(trained_weights_vec) == weights_container.N)
    weights_container.value = trained_weights_vec  # Put back in a nice structure.

    atoms = ['C', 'N', 'O', 'S', 'F', 'Si', 'P', 'Cl']
    masses = [12, 14,  16,   32,  19,  28,   31, 35.5]

    atom_weights = weights_container.lookup_by_name('atom2vec').value.ravel()

    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)
    ax.plot( masses, atom_weights, 'o')

    for ix, atom in enumerate(atoms):
        print "Atom: ", atom, " has weight", atom_weights[ix]
        ax.text( masses[ix], atom_weights[ix], atom)
    ax.set_xlabel("True mass")
    ax.set_ylabel("Weights")
    plt.savefig(os.path.join(outdir, outfilename + '-atoms.png'))
    plt.savefig(os.path.join(outdir, outfilename + '-atoms.eps'))
    plt.close()

    if arch_params['bond_vec_dim'] > 0:
        bond_names = ['single', 'double', 'triple', 'aromatic', 'conjugated', 'in ring']
        bond_masses = [1.0, 2.0, 3.0, 1.5, 4.0, 1.5]
        bond_weights = weights_container.lookup_by_name('bond2vec').value.ravel()

        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        ax.plot( bond_masses, bond_weights, 'o')
        for ix, bond in enumerate(bond_names):
            print "Bond: ", bond, " has weight", bond_weights[ix]
            ax.text( bond_masses[ix], bond_weights[ix], bond)
        ax.set_xlabel("True mass")
        ax.set_ylabel("Weights")
        plt.savefig(os.path.join(outdir, outfilename + '-bonds.png'))
        plt.savefig(os.path.join(outdir, outfilename + '-bonds.eps'))
        plt.close()

def plot_weights_container(wc, fig):
    N_groups = len(wc._weights_list)
    N_side = np.ceil(np.sqrt(N_groups))

    for ix in range(N_groups):
        ax = fig.add_subplot(N_side, N_side, ix + 1)
        #ax.imshow(wc._weights_list[ix].value)
        ax.pcolormesh(np.atleast_2d(wc._weights_list[ix].value))
        ax.set_title(wc._names_list[ix])
        plt.setp(ax.get_xticklabels(), visible=False)
    plt.draw()




def plot_weights(net_building_func, weights_file, outdir, outfilename):
    saved_net = np.load(weights_file)
    trained_weights_vec = saved_net['weights']
    arch_params = saved_net['arch_params'][()]
    _, _, _, _, weights_container = net_building_func(**arch_params)
    assert(len(trained_weights_vec) == weights_container.N)
    weights_container.value = trained_weights_vec  # Put back in a nice structure.

    fig = plt.figure()
    plot_weights_container(weights_container, fig)

    plt.savefig(os.path.join(outdir, outfilename + '-atoms.png'))
    plt.savefig(os.path.join(outdir, outfilename + '-atoms.eps'))
    plt.close()
