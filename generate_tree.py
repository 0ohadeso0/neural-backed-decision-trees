"""Generates subset_structure_released.xml from structured_released.xml

Constructs minimal tree such that all wnids contained in
tiny-imagenet-200/wnids.txt and their ancestors are included.
"""

from utils.utils import DATASETS, METHODS, DATASET_TO_FOLDER_NAME
from utils.xmlutils import keep_matched_nodes_and_ancestors, count_nodes, \
    compute_depth, compute_num_children, prune_single_child_nodes, \
    prune_duplicate_leaves
from utils.nltkutils import build_minimal_wordnet_tree, build_random_tree
from utils.utils import Colors
import xml.etree.ElementTree as ET
import argparse
import os


def generate_fname(method, seed=0, branching_factor=2, **kwargs):
    fname = f'tree-{method}'
    if method == 'random':
        if seed != 0:
            fname += f'-seed{seed}'
        if branching_factor != 2:
            fname += f'-branch{branching_factor}'
    return fname


def print_tree_stats(tree, name, args):
    num_children = compute_num_children(tree)
    print('[{}] \t Nodes: {} \t Depth: {} \t Max Children: {}'.format(
        name,
        count_nodes(tree),
        compute_depth(tree),
        max(num_children)))
    if args.verbose:
        print('[{}]'.format(name), num_children)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset',
        help='Must be a folder data/{dataset} containing a wnids.txt',
        choices=DATASETS,
        default='CIFAR10')
    parser.add_argument('--method', choices=METHODS,
        help='structure_released.xml apparently is missing many CIFAR100 classes. '
        'As a result, pruning does not work for CIFAR100. Random will randomly '
        'join clusters together, iteratively, to make a roughly-binary tree.',
        default='build')
    parser.add_argument('--seed', type=int, default=0)
    parser.add_argument('--branching-factor', type=int, default=2)
    parser.add_argument('--extra-roots', action='store_true',
                        help='If should include all parents of each synset '
                        'as extra roots.')
    parser.add_argument('--verbose', action='store_true')

    args = parser.parse_args()

    folder = DATASET_TO_FOLDER_NAME[args.dataset]
    directory = os.path.join('data', folder)
    with open(os.path.join(directory, 'wnids.txt')) as f:
        wnids = [wnid.strip() for wnid in f.readlines()]

    if args.method == 'prune':
        tree = ET.parse('structure_released.xml')

        print_tree_stats(tree, 'original', args)
        tree = keep_matched_nodes_and_ancestors(tree, [
            './/synset[@wnid="{}"]'.format(wnid) for wnid in wnids
        ])
    elif args.method == 'build':
        tree = build_minimal_wordnet_tree(wnids, extra_roots=args.extra_roots)
    elif args.method == 'random':
        tree = build_random_tree(
            wnids, seed=args.seed, branching_factor=args.branching_factor)
    else:
        raise NotImplementedError(f'Method "{args.method}" not yet handled.')

    print_tree_stats(tree, 'matched', args)
    # lol
    # tree = prune_single_child_nodes(tree)
    # tree = prune_single_child_nodes(tree)
    # tree = prune_single_child_nodes(tree)

    # prune duplicate leaves
    tree = prune_duplicate_leaves(tree)

    print_tree_stats(tree, 'pruned', args)
    fname = generate_fname(**vars(args))
    path = os.path.join(directory, f'{fname}.xml')
    tree.write(path)

    Colors.green('==> Wrote tree to {}'.format(path))

    wnids_set = {node.get('wnid') for node in tree.iter()}
    assert all(wnid.strip() in wnids_set for wnid in wnids), \
        [wnid.strip() for wnid in wnids if wnid.strip() not in wnids_set]


if __name__ == '__main__':
    main()
