#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2018 Kyoto University (Hirofumi Inaguma)
#  Apache 2.0  (http://www.apache.org/licenses/LICENSE-2.0)

""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import argparse
import codecs
from distutils.util import strtobool
import kaldi_io
import os
import re
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('--feat', type=str,
                    help='feat.scp file')
parser.add_argument('--utt2num_frames', type=str,
                    help='utt2num_frames file')
parser.add_argument('--dict', type=str,
                    help='dictionary file')
parser.add_argument('--text', type=str,
                    help='text file')
parser.add_argument('--unit', type=str, choices=['word', "bpe", 'char', "phone"],
                    help='token units')
parser.add_argument('--remove_word_boundary', type=strtobool, default=False,
                    help='')
parser.add_argument('--is_test', type=strtobool, default=False)
parser.add_argument('--unk', type=str, default='<unk>',
                    help='<unk> token')
parser.add_argument('--space', type=str, default='<space>',
                    help='<space> token')
parser.add_argument('--nlsyms', type=str, default='', nargs='?',
                    help='path to non-linguistic symbols, e.g., <NOISE> etc.')
args = parser.parse_args()


def main():

    nlsyms = []
    if args.nlsyms:
        with codecs.open(args.nlsyms, 'r', 'utf-8') as f:
            for line in f:
                nlsyms.append(line.strip().encode('utf-8'))

    utt2feat = {}
    with codecs.open(args.feat, 'r', 'utf-8') as f:
        for line in f:
            utt_id, feat_path = line.strip().split(' ')
            utt2feat[utt_id] = feat_path

    utt2frame = {}
    with codecs.open(args.utt2num_frames, 'r', 'utf-8') as f:
        for line in f:
            utt_id, x_len = line.strip().split(' ')
            utt2frame[utt_id] = int(x_len)

    token2id = {}
    with codecs.open(args.dict, 'r', 'utf-8') as f:
        for line in f:
            token, id = line.strip().split(' ')
            token2id[token] = str(id)

    print(',utt_id,feat_path,x_len,x_dim,text,token_id,y_len,y_dim')

    x_dim = None
    utt_count = 0
    with codecs.open(args.text, 'r', 'utf-8') as f:
        pbar = tqdm(total=len(open(args.text).readlines()))
        for line in f:
            # Remove succesive spaces
            line = re.sub(r'[\s]+', ' ', line.strip().encode('utf-8'))
            utt_id = line.split(' ')[0]
            words = line.split(' ')[1:]
            if '' in words:
                words.remove('')

            # for CSJ
            words = list(map(lambda x: x.split('+')[0], words))

            text = ' '.join(words)
            feat_path = utt2feat[utt_id]
            x_len = utt2frame[utt_id]

            if not os.path.isfile(feat_path.split(':')[0]):
                raise ValueError('There is no file: %s' % feat_path)

            # Convert strings into the corresponding indices
            if args.is_test:
                token_id = ''
                y_len = 1
                # NOTE; skip test sets for OOV issues
            else:
                token_ids = []
                if args.unit == 'word':
                    for w in words:
                        if w in token2id.keys():
                            token_ids.append(token2id[w])
                        else:
                            # Replace with <unk>
                            token_ids.append(token2id[args.unk])

                elif args.unit == 'bpe':
                    raise NotImplementedError()

                elif args.unit == 'char':
                    for i,  w in enumerate(words):
                        if w in nlsyms:
                            token_ids.append(token2id[w])
                        else:
                            token_ids += list(map(lambda c: token2id[c], list(w)))

                        # Remove whitespaces
                        if args.remove_word_boundary:
                            if i < len(words) - 1:
                                token_ids.append(token2id[args.space])

                elif args.unit == 'phone':
                    for p in words:
                        token_ids.append(token2id[p])

                else:
                    raise ValueError(args.unit)
                token_id = ' '.join(token_ids)
                y_len = len(token_ids)

            if x_dim is None:
                x_dim = kaldi_io.read_mat(feat_path).shape[-1]
            y_dim = len(token2id.keys())

            print("%d,%s,%s,%d,%d,%s,%s,%d,%d" %
                  (utt_count, utt_id, feat_path, x_len, x_dim, text, token_id, y_len, y_dim))
            utt_count += 1
            pbar.update(1)


if __name__ == '__main__':
    main()
